"""Keysight PNA driver for Ethernet SCPI/VISA measurements."""

import re

import numpy as np

try:
    import pyvisa
except ImportError:  # Allows tests with an injected resource manager.
    pyvisa = None


class VNA_Controller:
    """Control a Keysight PNA-family VNA over an Ethernet VISA session.

    The default resource uses VXI-11 (``TCPIP0::<host>::inst0::INSTR``).
    A complete VISA resource can be supplied when HiSLIP or another supported
    transport is required.
    """

    def __init__(
        self,
        host,
        timeout=30,
        resource_name=None,
        visa_backend=None,
        resource_manager=None,
    ):
        self.host = host
        self.timeout = float(timeout)
        self.resource_name = resource_name or f"TCPIP0::{host}::inst0::INSTR"
        self.visa_backend = visa_backend
        self.resource_manager = resource_manager
        self.connection = None
        self.idn = None
        self.last_frequencies = None
        self.last_trace = None
        self.last_error = None
        self._owns_resource_manager = resource_manager is None

    @property
    def is_connected(self):
        return self.connection is not None

    def connect(self):
        """Open the VISA session and identify the instrument."""
        try:
            if self.resource_manager is None:
                if pyvisa is None:
                    raise RuntimeError(
                        "PyVISA is not installed. Run 'python -m pip install -r requirements.txt'."
                    )
                if self.visa_backend is None:
                    self.resource_manager = pyvisa.ResourceManager()
                else:
                    self.resource_manager = pyvisa.ResourceManager(self.visa_backend)

            self.connection = self.resource_manager.open_resource(self.resource_name)
            self.connection.timeout = round(self.timeout * 1000)
            self.connection.read_termination = "\n"
            self.connection.write_termination = "\n"
            self.connection.write("*CLS")
            self.idn = self.connection.query("*IDN?").strip()
            if not self.idn:
                raise RuntimeError("The VNA returned an empty *IDN? response.")
            self.last_error = None
            print(f"[SYSTEM] Connection established to VNA: {self.idn}")
            return True
        except Exception as exc:
            self.last_error = exc
            self._close_resources()
            print(f"[ERROR] Could not connect to VNA: {exc}")
            return False

    def identify(self):
        """Return the VNA IEEE-488.2 identification string."""
        connection = self._require_connection()
        self.idn = connection.query("*IDN?").strip()
        return self.idn

    def configure_measurement(self, parameter="S21", channel=1, trace_name="NEO_S21"):
        """Create and select a standard S-parameter measurement."""
        connection = self._require_connection()
        channel = self._validate_channel(channel)
        parameter = parameter.upper()
        if re.fullmatch(r"S[1-9][0-9]*", parameter) is None:
            raise ValueError("parameter must be an S-parameter such as 'S11' or 'S21'.")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", trace_name) is None:
            raise ValueError("trace_name may contain only letters, numbers, and underscores.")

        catalog = connection.query(f"CALC{channel}:PAR:CAT:EXT? DEF").strip()
        catalog = catalog.strip('"')
        catalog_items = [item.strip() for item in catalog.split(",") if item.strip()]
        measurement_names = catalog_items[0::2]
        if trace_name in measurement_names:
            connection.write(f"CALC{channel}:PAR:DEL '{trace_name}'")
        connection.write(f"CALC{channel}:PAR:DEF:EXT '{trace_name}','{parameter}'")
        connection.write(f"CALC{channel}:PAR:SEL '{trace_name}'")

    def configure_sweep(
        self,
        start_frequency,
        stop_frequency,
        points,
        channel=1,
        if_bandwidth=None,
        source_power=None,
    ):
        """Configure a linear frequency sweep using SI units (Hz, Hz, dBm)."""
        connection = self._require_connection()
        channel = self._validate_channel(channel)
        start_frequency = self._positive_float(start_frequency, "start_frequency")
        stop_frequency = self._positive_float(stop_frequency, "stop_frequency")
        if stop_frequency <= start_frequency:
            raise ValueError("stop_frequency must be greater than start_frequency.")
        if isinstance(points, bool) or int(points) != points or int(points) < 2:
            raise ValueError("points must be an integer greater than or equal to 2.")

        connection.write(f"SENS{channel}:SWE:TYPE LIN")
        connection.write(f"SENS{channel}:FREQ:STAR {start_frequency:.12g}")
        connection.write(f"SENS{channel}:FREQ:STOP {stop_frequency:.12g}")
        connection.write(f"SENS{channel}:SWE:POIN {int(points)}")
        if if_bandwidth is not None:
            if_bandwidth = self._positive_float(if_bandwidth, "if_bandwidth")
            connection.write(f"SENS{channel}:BAND {if_bandwidth:.12g}")
        if source_power is not None:
            source_power = float(source_power)
            if not np.isfinite(source_power):
                raise ValueError("source_power must be finite.")
            connection.write(f"SOUR{channel}:POW {source_power:.12g}")

    def measure(self, channel=1, trace_name=None, trigger=True):
        """Acquire the selected corrected trace as ``[frequency, real, imag]``.

        Returns
        -------
        numpy.ndarray
            A floating array with shape ``(number_of_points, 3)``. Column 0 is
            stimulus frequency in Hz; columns 1 and 2 are the real and
            imaginary components of the selected corrected measurement.
        """
        connection = self._require_connection()
        channel = self._validate_channel(channel)
        if trace_name is not None:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", trace_name) is None:
                raise ValueError("trace_name may contain only letters, numbers, and underscores.")
            connection.write(f"CALC{channel}:PAR:SEL '{trace_name}'")

        continuous_was_on = False
        try:
            if trigger:
                continuous_was_on = bool(
                    int(float(connection.query(f"INIT{channel}:CONT?").strip()))
                )
                connection.write("ABOR")
                connection.write(f"INIT{channel}:CONT OFF")
                opc = connection.query(f"INIT{channel}:IMM;*OPC?").strip()
                if int(float(opc)) != 1:
                    raise RuntimeError(f"Unexpected operation-complete response: {opc!r}")

            connection.write("FORM:DATA REAL,64")
            connection.write("FORM:BORD SWAP")
            frequencies = np.asarray(
                connection.query_binary_values(
                    f"CALC{channel}:X?",
                    datatype="d",
                    is_big_endian=False,
                    container=np.array,
                ),
                dtype=float,
            )
            interleaved = np.asarray(
                connection.query_binary_values(
                    f"CALC{channel}:DATA? SDATA",
                    datatype="d",
                    is_big_endian=False,
                    container=np.array,
                ),
                dtype=float,
            )
            if interleaved.size % 2:
                raise RuntimeError("The VNA returned an odd number of SDATA values.")

            trace = interleaved[0::2] + 1j * interleaved[1::2]
            if frequencies.size != trace.size:
                raise RuntimeError(
                    "The frequency and trace arrays have different lengths "
                    f"({frequencies.size} and {trace.size})."
                )
            self.last_frequencies = frequencies.copy()
            self.last_trace = trace.copy()
            return np.column_stack((frequencies, trace.real, trace.imag))
        finally:
            if trigger and continuous_was_on and self.connection is not None:
                connection.write(f"INIT{channel}:CONT ON")

    def get_complex_trace(self):
        """Return a copy of the complex trace from the most recent measurement."""
        if self.last_trace is None:
            raise RuntimeError("No VNA measurement has been acquired yet.")
        return self.last_trace.copy()

    def disconnect(self):
        """Close the instrument session and its owned VISA resource manager."""
        self._close_resources()
        print(f"[SYSTEM] {self.resource_name} - VNA disconnected.")

    def _close_resources(self):
        if self.connection is not None:
            try:
                self.connection.close()
            finally:
                self.connection = None
        if self._owns_resource_manager and self.resource_manager is not None:
            try:
                self.resource_manager.close()
            finally:
                self.resource_manager = None

    def _require_connection(self):
        if self.connection is None:
            raise RuntimeError("The VNA is not connected.")
        return self.connection

    @staticmethod
    def _validate_channel(channel):
        if isinstance(channel, bool) or int(channel) != channel or int(channel) < 1:
            raise ValueError("channel must be a positive integer.")
        return int(channel)

    @staticmethod
    def _positive_float(value, name):
        value = float(value)
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite number.")
        return value

import importlib.util
from pathlib import Path
import unittest

import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "neo" / "drivers" / "vna_driver.py"
SPEC = importlib.util.spec_from_file_location("vna_driver", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VNA_Controller = MODULE.VNA_Controller


class FakeInstrument:
    def __init__(self):
        self.timeout = None
        self.read_termination = None
        self.write_termination = None
        self.writes = []
        self.closed = False

    def write(self, command):
        self.writes.append(command)

    def query(self, command):
        if command == "*IDN?":
            return "Keysight Technologies,N5227B,MY12345678,A.15.00\n"
        if command == "CALC1:PAR:CAT:EXT? DEF":
            return '"NEO_S21,S21"\n'
        if command == "INIT1:CONT?":
            return "1\n"
        if command == "INIT1:IMM;*OPC?":
            return "1\n"
        raise AssertionError(f"Unexpected query: {command}")

    def query_binary_values(self, command, **kwargs):
        assert kwargs["datatype"] == "d"
        assert kwargs["is_big_endian"] is False
        if command == "CALC1:X?":
            return kwargs["container"]([1.0e9, 2.0e9, 3.0e9])
        if command == "CALC1:DATA? SDATA":
            return kwargs["container"]([1.0, 0.1, 2.0, 0.2, 3.0, 0.3])
        raise AssertionError(f"Unexpected binary query: {command}")

    def close(self):
        self.closed = True


class FakeResourceManager:
    def __init__(self, instrument):
        self.instrument = instrument
        self.opened_resource = None

    def open_resource(self, resource_name):
        self.opened_resource = resource_name
        return self.instrument


def connected_vna():
    instrument = FakeInstrument()
    manager = FakeResourceManager(instrument)
    vna = VNA_Controller("192.0.2.10", timeout=12.5, resource_manager=manager)
    assert vna.connect()
    return vna, instrument, manager


class VNADriverTests(unittest.TestCase):
    def test_connect_configure_and_measure_numpy_matrix(self):
        vna, instrument, manager = connected_vna()
        self.assertEqual(
            manager.opened_resource, "TCPIP0::192.0.2.10::inst0::INSTR"
        )
        self.assertEqual(instrument.timeout, 12500)

        vna.configure_measurement("S21", trace_name="NEO_S21")
        vna.configure_sweep(
            1.0e9, 3.0e9, 3, if_bandwidth=1.0e3, source_power=-20
        )
        measurement = vna.measure(trace_name="NEO_S21")

        self.assertIsInstance(measurement, np.ndarray)
        self.assertEqual(measurement.shape, (3, 3))
        np.testing.assert_allclose(measurement[:, 0], [1.0e9, 2.0e9, 3.0e9])
        np.testing.assert_allclose(measurement[:, 1], [1.0, 2.0, 3.0])
        np.testing.assert_allclose(measurement[:, 2], [0.1, 0.2, 0.3])
        np.testing.assert_allclose(
            vna.get_complex_trace(), [1 + 0.1j, 2 + 0.2j, 3 + 0.3j]
        )
        self.assertIn("INIT1:CONT OFF", instrument.writes)
        self.assertEqual(instrument.writes[-1], "INIT1:CONT ON")

    def test_invalid_sweep_is_rejected_before_writing(self):
        vna, instrument, _ = connected_vna()
        writes_before = list(instrument.writes)
        with self.assertRaisesRegex(ValueError, "greater than"):
            vna.configure_sweep(3.0e9, 1.0e9, 201)
        self.assertEqual(instrument.writes, writes_before)

    def test_disconnect_closes_session_and_blocks_measurement(self):
        vna, instrument, _ = connected_vna()
        vna.disconnect()
        self.assertTrue(instrument.closed)
        self.assertFalse(vna.is_connected)
        with self.assertRaisesRegex(RuntimeError, "not connected"):
            vna.measure()


if __name__ == "__main__":
    unittest.main()

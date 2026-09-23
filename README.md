# NEO: Nearfield Emission Observatory

Python drivers for controlling the Nearfield Emission Observatory
positioning system. The current implementation communicates with a
three-axis motor controller and two position readouts over serial
connections, and with a Keysight PNA-family VNA over Ethernet.

## Components

- `neo/neo_driver.py`: high-level controller that owns the motor, readout, and
  VNA drivers and provides positioning and RF-acquisition entry points.
- `neo/drivers/vxc_driver.py`: serial driver for the three-axis motor controller.
- `neo/drivers/vro_driver.py`: serial driver for the XY and angular position
  readouts.
- `neo/drivers/vna_driver.py`: Ethernet VISA/SCPI driver for a Keysight PNA.
- `Tester.py`: hardware test script demonstrating calibration and two
  5 x 5 scans at 0 and 90 degrees.

## Documentation

Start with the [documentation index](documentation/README.md). Detailed guides
cover:

- [architecture and component responsibilities](documentation/architecture.md);
- [hardware setup, dependencies, and commissioning safety](documentation/hardware-and-installation.md);
- [the positioning-controller API](documentation/controller-api.md);
- [PNA configuration and NumPy acquisition](documentation/vna-guide.md);
- [scan traversal and array shapes](documentation/scan-data-model.md); and
- [testing and troubleshooting](documentation/testing-and-troubleshooting.md); and
- [the per-file automated test guide](tests/README.md).

## Repository structure

```text
.
|-- Tester.py
|-- requirements.txt
|-- documentation/
|   |-- README.md
|   |-- architecture.md
|   |-- controller-api.md
|   |-- hardware-and-installation.md
|   |-- scan-data-model.md
|   |-- testing-and-troubleshooting.md
|   `-- vna-guide.md
|-- tests/
|   |-- test_neo_vna_integration.py
|   `-- test_vna_driver.py
`-- neo/
    |-- __init__.py
    |-- neo_driver.py
    `-- drivers/
        |-- __init__.py
        |-- vro_driver.py
        |-- vna_driver.py
        `-- vxc_driver.py
```

## Requirements

- Python 3
- NumPy
- pySerial
- PyVISA with either Keysight/NI VISA or the included `pyvisa-py` backend
- Compatible motor-control and position-readout hardware

Install the Python dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Usage

Configure the serial ports and scan parameters in `Tester.py`. The
current example assumes:

- `COM3`: motor controller
- `COM4`: XY position readout
- `COM5`: angular position readout

Run the example with:

```bash
python Tester.py
```

The high-level interface can also be instantiated directly:

```python
from neo import NEO_Controller

neo = NEO_Controller(
    port_Motors="COM3",
    port_Readout_XY="COM4",
    port_Readout_Phi="COM5",
    host_VNA="192.168.0.10",
)

if neo.connect():
    try:
        neo.configure_vna(
            parameter="S21",
            trace_name="NEO_S21",
            start_frequency=170e9,
            stop_frequency=200e9,
            points=401,
            if_bandwidth=1e3,
        )
        vna_measurement = neo.measure_vna(trace_name="NEO_S21")
        neo.calibrate()
        neo.home()
        order, positions, measurements = neo.measure(5, 5, 1)
    finally:
        neo.disconnect()
```

`NEO_Controller` exposes the connected VNA as `neo.VNA`. Its high-level
`measure_vna()` method returns the PNA trace as a NumPy matrix with columns
`[frequency_hz, real, imag]`. The low-level driver uses a VXI-11 resource by
default. Replace the example address and sweep limits with the values for the
measurement setup.

```python
neo.configure_vna(
    parameter="S21",
    trace_name="NEO_S21",
    start_frequency=170e9,
    stop_frequency=200e9,
    points=401,
    if_bandwidth=1e3,
)
measurement = neo.measure_vna(trace_name="NEO_S21")
```

For a PNA configured for HiSLIP, pass its complete VISA resource to the
high-level constructor, for example
`resourceNameVNA="TCPIP0::192.168.0.10::hislip0::INSTR"`.

See the [VNA guide](documentation/vna-guide.md) for the full API, command
sequence, units, array definition, and measurement-integrity checklist.

## Hardware safety

This software commands physical motion. Verify the serial-port
assignments, travel limits, coordinate signs, clearance, emergency-stop
operation, and homing procedure before running a scan. Begin with low
motor speeds and short movements under direct supervision.

The complete commissioning checklist is in
[Hardware and installation](documentation/hardware-and-installation.md).

## Current scope

The scan routine's `measurement_matrix` still contains traversal markers.
The VNA is owned by `NEO_Controller` and can be acquired through
`measure_vna()`, but spatial `measure()` does not yet trigger it at each grid
position. Per-position trace storage still requires a defined frequency-axis,
metadata, and failure policy.

The exact current scan representation and a proposed future complex-data model
are documented in [Scan data model](documentation/scan-data-model.md).

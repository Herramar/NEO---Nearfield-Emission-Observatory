# NEO: Nearfield Emission Observatory

Python drivers for controlling the Nearfield Emission Observatory
positioning system. The current implementation communicates with a
three-axis motor controller and two position readouts over serial
connections, and with a Keysight PNA-family VNA over Ethernet.

## Components

- `neo/neo_driver.py`: high-level controller for connection, calibration,
  homing, translation, rotation, and spiral-grid traversal.
- `neo/drivers/vxc_driver.py`: serial driver for the three-axis motor controller.
- `neo/drivers/vro_driver.py`: serial driver for the XY and angular position
  readouts.
- `neo/drivers/vna_driver.py`: Ethernet VISA/SCPI driver for a Keysight PNA.
- `Tester.py`: hardware test script demonstrating calibration and two
  5 x 5 scans at 0 and 90 degrees.

## Repository structure

```text
.
|-- Tester.py
|-- requirements.txt
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
)

if neo.connect():
    try:
        neo.calibrate()
        neo.home()
        order, positions, measurements = neo.measure(5, 5, 1)
    finally:
        neo.disconnect()
```

The VNA driver uses a VXI-11 resource by default. Replace the example IP
address and sweep limits with the values for the measurement setup:

```python
from neo.drivers import VNA_Controller

vna = VNA_Controller("192.168.0.10", timeout=30)
if vna.connect():
    try:
        vna.configure_measurement("S21", trace_name="NEO_S21")
        vna.configure_sweep(170e9, 200e9, 401, if_bandwidth=1e3)
        measurement = vna.measure(trace_name="NEO_S21")
        # measurement[:, 0]: frequency in Hz
        # measurement[:, 1]: real(S21)
        # measurement[:, 2]: imag(S21)
    finally:
        vna.disconnect()
```

For a PNA configured for HiSLIP, pass its complete VISA resource, for example
`resource_name="TCPIP0::192.168.0.10::hislip0::INSTR"`.

## Hardware safety

This software commands physical motion. Verify the serial-port
assignments, travel limits, coordinate signs, clearance, emergency-stop
operation, and homing procedure before running a scan. Begin with low
motor speeds and short movements under direct supervision.

## Current scope

The scan routine's `measurement_matrix` still contains traversal markers.
The VNA driver provides trace acquisition independently and is ready to be
connected to the scan routine once the required per-position trace shape and
storage policy are defined.

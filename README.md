# NEO: Nearfield Emission Observatory

Python drivers for controlling the Nearfield Emission Observatory
positioning system. The current implementation communicates with a
three-axis motor controller and two position readouts over serial
connections.

## Components

- `neo_driver.py`: high-level controller for connection, calibration,
  homing, translation, rotation, and spiral-grid traversal.
- `vxc_driver.py`: serial driver for the three-axis motor controller.
- `vro_driver.py`: serial driver for the XY and angular position
  readouts.
- `Tester.py`: hardware test script demonstrating calibration and two
  5 x 5 scans at 0 and 90 degrees.

## Requirements

- Python 3
- NumPy
- pySerial
- Compatible motor-control and position-readout hardware

Install the Python dependencies with:

```bash
python -m pip install numpy pyserial
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
from neo_driver import NEO_Controller

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

## Hardware safety

This software commands physical motion. Verify the serial-port
assignments, travel limits, coordinate signs, clearance, emergency-stop
operation, and homing procedure before running a scan. Begin with low
motor speeds and short movements under direct supervision.

## Current scope

The scan routine records traversal order and reported positions. The
current `measurement_matrix` contains traversal markers; acquisition
from an RF instrument is not yet implemented in this repository.

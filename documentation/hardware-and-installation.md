# Hardware and Installation

## Supported interfaces

The current repository expects:

- one serial connection to a three-axis motor controller;
- one serial connection to the XY position readout;
- one serial connection to the angular position readout; and
- one Ethernet connection to a Keysight PNA-family vector network analyzer.

The supplied `Tester.py` example uses `COM3`, `COM4`, and `COM5`. These are
examples, not automatically discovered or universally correct assignments.

## Python installation

From the repository root:

```bash
python -m pip install -r requirements.txt
```

The requirements are:

| Package | Purpose |
| --- | --- |
| `numpy` | Scan arrays and VNA measurement matrices |
| `pyserial` | Motor-controller and position-readout communication |
| `pyvisa` | VISA API used by the VNA driver |
| `pyvisa-py` | Pure-Python VISA backend when another VISA implementation is unavailable |

Keysight IO Libraries Suite or NI-VISA may be used instead of the
`pyvisa-py` backend when installed and configured on the measurement computer.

## Serial configuration

### Motor controller

Default `VXC_Controller` settings:

| Setting | Default |
| --- | --- |
| Baud rate | 57600 bit/s |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Timeout | 1 s |
| Motor speed | 500 in the low-level driver; 100 through `NEO_Controller` |

### Position readouts

Default `VRO_Controller` settings:

| Setting | Default |
| --- | --- |
| Baud rate | 9600 bit/s |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Timeout | 1 s |

The readout driver sends `E,` for echo on or `F,` for echo off, followed by
`Q,` during connection setup. Position queries use `X` or `Y` and read through
the carriage-return terminator.

## PNA Ethernet configuration

The default VNA resource is:

```text
TCPIP0::<IPv4 address or hostname>::inst0::INSTR
```

For example:

```python
from neo.drivers import VNA_Controller

vna = VNA_Controller("192.168.0.10")
```

This selects the VXI-11 `inst0` endpoint. A complete resource string can
override it, including a HiSLIP endpoint:

```python
vna = VNA_Controller(
    "192.168.0.10",
    resource_name="TCPIP0::192.168.0.10::hislip0::INSTR",
)
```

Before running a sweep:

1. Put the computer and PNA on reachable IP networks.
2. Confirm the PNA address from its front-panel network configuration.
3. Confirm that the selected VISA backend can discover or open the resource.
4. Verify the test ports, external frequency-extension hardware, calibration
   state, power limits, and expected measurement parameter.
5. Start with a non-radiating or otherwise safe setup when checking remote
   control.

The driver timeout is specified in seconds and converted internally to the
millisecond value required by PyVISA.

## Pre-motion safety checklist

Complete these checks under direct supervision before calibration, homing, or
a scan:

- Verify every serial-port assignment by disconnecting or identifying one
  device at a time.
- Verify motor-number mapping: 1 horizontal, 2 vertical, 3 rotary.
- Verify positive and negative direction conventions at low speed.
- Confirm physical travel limits, probe and DUT clearance, cable slack, and
  rotary clearance.
- Confirm that an emergency stop is accessible and functional.
- Begin with short movements and conservative motor speed.
- Confirm readout units before using the returned values as millimetres or
  degrees.
- Do not run unattended until homing and the full scan envelope have been
  validated.

## Initial connection check

```python
from neo import NEO_Controller
from neo.drivers import VNA_Controller

positioner = NEO_Controller("COM3", "COM4", "COM5", echo=0)
vna = VNA_Controller("192.168.0.10")

positioner_ok = positioner.connect()
vna_ok = vna.connect()

print("Positioner connected:", positioner_ok)
print("PNA identification:", vna.idn if vna_ok else vna.last_error)

if vna_ok:
    vna.disconnect()
if positioner_ok:
    positioner.disconnect()
```

Do not use this connection check as proof that motion directions, scale
factors, RF cabling, or calibration are correct.

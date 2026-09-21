# VNA Guide

## Purpose and supported behavior

`VNA_Controller` controls a Keysight PNA-family vector network analyzer over
an Ethernet VISA resource. It can:

- open and close a VISA instrument session;
- query the IEEE-488.2 identification string;
- create and select a standard S-parameter measurement;
- configure a linear frequency sweep;
- request a synchronized single sweep;
- retrieve the stimulus frequencies and corrected complex trace; and
- return the result as a NumPy matrix.

It does not perform calibration, calibration-kit definition, de-embedding,
port extension, averaging configuration, time-domain conversion, multi-trace
acquisition, or file storage on the PNA.

## Import and constructor

```python
from neo.drivers import VNA_Controller

vna = VNA_Controller(
    host="192.168.0.10",
    timeout=30,
    resource_name=None,
    visa_backend=None,
    resource_manager=None,
)
```

| Parameter | Meaning |
| --- | --- |
| `host` | PNA hostname or IPv4 address used in the default resource string |
| `timeout` | VISA I/O timeout in seconds |
| `resource_name` | Complete VISA resource override |
| `visa_backend` | Optional argument passed to `pyvisa.ResourceManager()` |
| `resource_manager` | Optional preconstructed resource manager, mainly for tests or shared ownership |

The default resource is `TCPIP0::<host>::inst0::INSTR`. The driver owns and
closes a resource manager that it constructs. It does not close an injected
resource manager.

## Connection

```python
if not vna.connect():
    raise RuntimeError(vna.last_error)

print(vna.idn)
```

`connect()` opens the resource, converts the timeout to milliseconds, sets
newline read and write termination, sends `*CLS`, and queries `*IDN?`. It
returns `True` only when the identification response is non-empty.

On failure it:

- stores the exception in `last_error`;
- closes any partially opened resources owned by the controller;
- prints an error; and
- returns `False`.

`identify()` repeats the `*IDN?` query and returns the stripped response. It
raises `RuntimeError` if the driver is disconnected.

## Configure an S-parameter

```python
vna.configure_measurement(
    parameter="S21",
    channel=1,
    trace_name="NEO_S21",
)
```

Accepted parameter names start with `S` and contain a positive first digit,
for example `S11` or `S21`. Trace names are limited to letters, digits, and
underscores and cannot begin with a digit.

The method performs this sequence:

1. Query `CALC<channel>:PAR:CAT:EXT? DEF`.
2. Delete an existing measurement with the same trace name.
3. Create the measurement with `CALC<channel>:PAR:DEF:EXT`.
4. Select it with `CALC<channel>:PAR:SEL`.

Recreating a named measurement can remove settings attached specifically to
that measurement. Confirm the PNA state and calibration association after
configuration.

## Configure a linear sweep

```python
vna.configure_sweep(
    start_frequency=170e9,
    stop_frequency=200e9,
    points=401,
    channel=1,
    if_bandwidth=1e3,
    source_power=-20,
)
```

| Parameter | Unit | Validation |
| --- | --- | --- |
| `start_frequency` | Hz | Positive and finite |
| `stop_frequency` | Hz | Positive, finite, and greater than start |
| `points` | samples | Integer and at least 2 |
| `channel` | none | Positive integer |
| `if_bandwidth` | Hz | Optional, positive, and finite |
| `source_power` | dBm | Optional and finite |

The driver requests a linear sweep and writes the start, stop, point count,
optional IF bandwidth, and optional source power. The PNA remains responsible
for enforcing its model-specific frequency, power, and point-count limits.

## Acquire a trace

```python
matrix = vna.measure(channel=1, trace_name="NEO_S21", trigger=True)
```

When `trigger=True`, the driver:

1. Queries whether continuous sweep is enabled.
2. Aborts the current operation.
3. Disables continuous sweep on the selected channel.
4. sends `INIT<channel>:IMM;*OPC?` and requires the response `1`;
5. selects 64-bit binary data and swapped byte order;
6. queries `CALC<channel>:X?` for stimulus values;
7. queries `CALC<channel>:DATA? SDATA` for corrected complex data; and
8. restores continuous sweep only if it was originally enabled.

With `trigger=False`, the driver reads the currently available trace without
initiating a new sweep.

### Returned NumPy matrix

The returned `numpy.ndarray` has floating dtype and shape `(N, 3)`:

| Column | Quantity | Unit |
| ---: | --- | --- |
| 0 | Stimulus frequency | Hz |
| 1 | Real part of corrected S-parameter | Dimensionless |
| 2 | Imaginary part of corrected S-parameter | Dimensionless |

For example:

```python
frequency_hz = matrix[:, 0]
s21 = matrix[:, 1] + 1j * matrix[:, 2]
magnitude_db = 20 * np.log10(np.abs(s21))
phase_deg = np.angle(s21, deg=True)
```

The frequency and complex arrays are also copied into `last_frequencies` and
`last_trace`. `get_complex_trace()` returns a copy of `last_trace` and raises
`RuntimeError` before the first successful acquisition.

The driver rejects odd-length interleaved data and mismatched frequency and
trace lengths rather than silently truncating them.

## Complete example

```python
import numpy as np

from neo.drivers import VNA_Controller


vna = VNA_Controller("192.168.0.10", timeout=30)
if not vna.connect():
    raise RuntimeError(f"PNA connection failed: {vna.last_error}")

try:
    vna.configure_measurement("S21", channel=1, trace_name="NEO_S21")
    vna.configure_sweep(
        170e9,
        200e9,
        401,
        channel=1,
        if_bandwidth=1e3,
        source_power=-20,
    )
    measurement = vna.measure(channel=1, trace_name="NEO_S21")

    frequency_hz = measurement[:, 0]
    s21 = measurement[:, 1] + 1j * measurement[:, 2]
    magnitude_db = 20 * np.log10(np.abs(s21))
finally:
    vna.disconnect()
```

## Measurement integrity

Before treating a returned trace as research data, record and verify:

- PNA model, serial number, and firmware from `idn`;
- VISA resource and transport;
- selected channel and S-parameter;
- start/stop frequency, point count, IF bandwidth, source power, and averaging;
- calibration method, standards, date, reference planes, and correction state;
- frequency-extender and waveguide configuration, if used;
- cable/probe condition and connection repeatability;
- warm-up time and environmental conditions; and
- repeated-trace variation and any uncertainty calculation.

The driver retrieves corrected `SDATA`, but that does not prove that a valid
or current calibration is active.

## Command references

- [Keysight TCPIP VISA interface formats](https://helpfiles.keysight.com/IO_Libraries_Suite/English/IOLS_Linux/VISA/Content/UsersGuide/chapter6/Using%20the%20TCPIP%20Interface.htm)
- [Keysight PNA calculate/data commands](https://helpfiles.keysight.com/csg/e5080a/programming/gp-ib_command_finder/calculate/data.htm)
- [Keysight PNA measurement-parameter commands](https://helpfiles.keysight.com/csg/e5080a/programming/gp-ib_command_finder/calculate/parameter.htm)
- [Keysight PNA initiate commands](https://helpfiles.keysight.com/csg/NA520xA/Programming/GP-IB_Command_Finder/Initiate.htm)

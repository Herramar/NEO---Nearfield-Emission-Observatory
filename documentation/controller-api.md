# Controller API

This reference describes the current public behavior of the positioning
classes. Units follow the assumptions in the source code and must be verified
against the connected hardware.

## `NEO_Controller`

Import:

```python
from neo import NEO_Controller
```

### Constructor

```python
NEO_Controller(
    port_Motors,
    port_Readout_XY,
    port_Readout_Phi,
    motorSpeed=100,
    baudrateVRO=9600,
    baudrateVXC=57600,
    timeout=1,
    echo=1,
)
```

| Parameter | Meaning |
| --- | --- |
| `port_Motors` | Serial port for the three-axis motor controller |
| `port_Readout_XY` | Serial port for the two-axis translation readout |
| `port_Readout_Phi` | Serial port for the angular readout |
| `motorSpeed` | Speed value sent to motors 1, 2, and 3 |
| `baudrateVRO` | Baud rate for both readout connections |
| `baudrateVXC` | Baud rate for the motor controller |
| `timeout` | Serial timeout in seconds |
| `echo` | `1` enables device echo; other values select echo off |

The initial `X_sensitivity`, `Z_sensitivity`, and `Phi_sensitivity` values are
all `1.0` until `calibrate()` replaces them.

### `connect()`

Constructs the three low-level controllers and connects them in this order:
motor controller, XY readout, angular readout. Returns `True` only if all three
connections return true.

The expression uses short-circuit evaluation. If one connection fails, later
connections are not attempted. A failed partial connection is not
automatically rolled back.

### `calibrate()`

Sends the readout home commands, commands 1000 units through `move_right()`,
`move_up()`, and `rotate()`, reads the resulting positions, and calculates:

```text
X_sensitivity   = X_readout / 1000       [mm/step, assumed]
Z_sensitivity   = Z_readout / 1000       [mm/step, assumed]
Phi_sensitivity = Phi_readout / 1000     [degree/step, assumed]
```

The values are rounded to six decimal places. The method returns `True` after
the sequence and does not itself return to home, despite the current console
message. `Tester.py` calls `home()` immediately afterward.

The current home-command condition is not a general all-device success check:

```python
if not self.Readout_XY.setHome() and self.Readout_Phi.setHome():
```

Treat calibration success as unverified until both readouts and all three
motions have been observed and checked. A zero sensitivity will later cause a
division-by-zero error in the movement methods.

### `home(homePhi=True)`

Reads the current horizontal, vertical, and angular coordinates, then commands
motions intended to return them to zero. Set `homePhi=False` to leave the
rotary axis unchanged. The method currently returns `True` without checking
the return value of each motion command or confirming the final readout.

### Motion methods

```python
move_right(distance)
move_left(distance)
move_up(distance)
move_down(distance)
rotate(Phi)
```

Translation distances are assumed to be millimetres and `Phi` is assumed to
be degrees. Each method converts the requested physical displacement to an
integer step count using the corresponding sensitivity, calls
`VXC_Controller.move_motor()`, and returns its Boolean result.

Current mapping and signs:

| Method | Motor | Step expression |
| --- | ---: | --- |
| `move_right(distance)` | 1 | `round(-distance / X_sensitivity)` |
| `move_left(distance)` | 1 | `round(distance / X_sensitivity)` |
| `move_up(distance)` | 2 | `round(-distance / Z_sensitivity)` |
| `move_down(distance)` | 2 | `round(distance / Z_sensitivity)` |
| `rotate(Phi)` | 3 | `round(Phi / Phi_sensitivity)` |

### `measure(m, n, distance)`

Traverses an `m` by `n` grid in an outward spiral and returns:

```python
order_matrix, position_matrix, measurement_matrix
```

This method controls position only. See [Scan data model](scan-data-model.md)
before using its output.

### `disconnect()`

Calls `disconnect()` on the motor and both readout controllers. It assumes the
three attributes were created by `connect()`. Calling it before connection or
after an early connection failure can raise `AttributeError`.

## `VXC_Controller`

Import:

```python
from neo.drivers import VXC_Controller
```

### Constructor

```python
VXC_Controller(port, motorSpeed=500, baudrate=57600, timeout=1, echo=1)
```

### `connect()`

Opens an 8-N-1 serial connection, clears both buffers, selects echo mode, sets
all three motor speeds, and returns `True` on an open serial object. The motor
configuration command has this form:

```text
E C S1M<speed>, S2M<speed>, S3M<speed>R
```

`F` replaces `E` when echo is disabled.

### `move_motor(motor_number, steps)`

Accepts motor numbers 1 through 3, clears the serial buffers, sends:

```text
C I<motor_number>M<steps>, R
```

It then calls `wait_for_completion()` and, on success, waits another 0.2 s
before returning `True`. It returns `False` on completion timeout. Invalid
motor numbers or a missing connection print an error and implicitly return
`None`.

### `wait_for_completion(timeout=30)`

Reads one byte at a time until the `^` completion character arrives. It polls
at 10 ms intervals and returns `False` after the timeout.

### `disconnect()`

Sends `Q,` to the controller. The current method does not call
`serial.Serial.close()`.

## `VRO_Controller`

Import:

```python
from neo.drivers import VRO_Controller
```

### Constructor

```python
VRO_Controller(port, baudrate=9600, timeout=1, echo=1, type=0)
```

`type=0` labels the instance as the XY readout. Any other value labels it as
the angular readout in console messages.

### `connect()`

Opens an 8-N-1 serial connection, sends `E,` or `F,` for echo selection,
sends `Q,`, and returns a Boolean connection result.

### `getPosition(axis=0)`

Sends `X` when `axis == 0`; any other value sends `Y`. It reads through a
carriage return, decodes UTF-8, strips whitespace, and returns the resulting
string. `NEO_Controller` converts this string to `float`.

### `setHome()`

Sends `C`, reads a carriage-return-terminated response, and returns the
stripped response string. It returns `None` when no open connection exists.

### `disconnect()`

Sends `Q,`. The current method does not call `serial.Serial.close()`.

## `VNA_Controller`

The VNA API is documented separately because it has different connection,
error, triggering, and data-return behavior. See the [VNA guide](vna-guide.md).

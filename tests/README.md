# Test Suite

The tests are hardware-independent unit and integration checks. Fake serial
ports and VISA instruments capture protocol commands and provide deterministic
responses, so running the suite does not move the positioning system or contact
a VNA.

Run every test from the repository root:

```bash
python -m unittest discover -s tests -v
```

Run one file while developing a driver:

```bash
python -m unittest tests/test_vro_driver.py -v
python -m unittest tests/test_vxc_driver.py -v
python -m unittest tests/test_vna_driver.py -v
python -m unittest tests/test_neo_vna_integration.py -v
```

## Files

### `test_vro_driver.py`

Tests the position-readout serial protocol. It verifies serial-port settings,
echo enable/disable commands, initial `Q,` command, X/Y position queries,
response decoding and whitespace removal, the home command, disconnected
behavior, connection failures, and the disconnect command.

### `test_vxc_driver.py`

Tests the three-axis motor-controller serial protocol. It verifies serial-port
settings, echo mode and three-motor speed configuration, buffer resets, motion
command formatting, valid motor selection, completion detection on `^`, timeout
behavior, connection failures, and the disconnect command. The movement test
mocks the settling delay and never controls real hardware.

### `test_vna_driver.py`

Tests the low-level Keysight PNA VISA/SCPI driver. It verifies resource and
timeout configuration, measurement and sweep commands, binary frequency and
complex-trace conversion to the `(N, 3)` NumPy result, continuous-sweep
restoration, cached complex data, input validation, and session closure.

### `test_neo_vna_integration.py`

Tests orchestration by `NEO_Controller` with all hardware controllers replaced
by fakes. It verifies controller ownership and lifecycle, VNA configuration and
measurement delegation, validation of incomplete sweep settings, and clean
disconnection of the motor, both readouts, and VNA.

## Scope

Passing tests confirm command construction, response handling, validation, and
controller orchestration against the fakes. They do not validate physical
motion, travel limits, position accuracy, serial timing under load, instrument
compatibility, RF calibration, or measurement performance. Perform the
supervised hardware checks in
[`documentation/testing-and-troubleshooting.md`](../documentation/testing-and-troubleshooting.md)
before operating the full system.


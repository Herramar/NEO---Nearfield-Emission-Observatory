# Testing and Troubleshooting

## Automated VNA tests

Run the hardware-independent test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The current tests use fake serial and VISA controllers. They cover:

- ownership of the VNA at the same level as the motor and readout drivers;
- high-level VNA configuration and measurement delegation;
- disconnection of all four controllers;
- construction of the default VXI-11 resource string;
- conversion of the timeout from seconds to milliseconds;
- measurement and sweep command flow;
- conversion of interleaved real/imaginary data into an `(N, 3)` array;
- restoration of continuous sweep state;
- access to the cached complex trace;
- invalid sweep-range rejection; and
- session closure and disconnected-use rejection.

These tests do not contact a PNA and do not validate model-specific limits,
network configuration, calibration, RF performance, or physical motion.

## Syntax check

```bash
python -m py_compile neo/*.py neo/drivers/*.py tests/*.py
```

## PNA connection failure

Inspect the stored exception:

```python
if not neo.connect():
    error = neo.VNA.last_error if neo.VNA else None
    print(type(error).__name__, error)
```

Check, in order:

1. PNA hostname or IPv4 address.
2. Computer/PNA subnet and reachability.
3. VISA resource spelling and selected transport (`inst0` or `hislip0`).
4. Firewall rules and PNA remote-interface settings.
5. Installed VISA backend and its resource discovery.
6. Timeout relative to the expected sweep duration.

## PNA connects but measurement fails

- Confirm that `vna.idn` identifies the intended instrument.
- Verify that the requested channel exists and supports the parameter.
- Verify that the S-parameter is valid for the available ports/test set.
- Confirm start/stop frequencies, power, point count, and IF bandwidth are
  within model and extender limits.
- Increase `timeout` for long sweeps.
- Inspect the PNA error queue from a VISA console after reproducing the
  failure; the current driver does not expose an error-queue helper.
- Try `trigger=False` only when intentionally reading an already acquired
  trace.

## Unexpected VNA values

- Reconstruct the complex trace as `real + 1j * imag`; do not interpret the
  real column alone as magnitude.
- Calculate magnitude in dB with `20*log10(abs(s))`, not `10*log10`.
- Confirm that the selected trace is the intended S-parameter.
- Confirm calibration/correction state and reference planes on the PNA.
- Check for compression, receiver saturation, insufficient dynamic range,
  unstable connections, and extender multiplication effects.
- Compare repeated traces and a known standard before scanning a DUT.

## Serial connection failure

- Verify the COM port in the operating system.
- Close terminal programs or other processes holding the port.
- Confirm baud rate and 8-N-1 framing.
- Confirm that the motor controller and readouts have not been interchanged.
- Test each low-level driver independently before constructing
  `NEO_Controller`.

## Motor completion timeout

`VXC_Controller` expects a `^` character within 30 seconds. If a move times
out:

- stop further automated motion;
- inspect the controller for alarms or limit activation;
- verify echo mode and returned protocol bytes;
- check whether the commanded step count is physically reasonable;
- confirm the completion character using a serial monitor; and
- do not simply increase the timeout until the mechanical cause is known.

## Incorrect position or direction

- Recheck motor mapping and direction signs with a very small move.
- Confirm readout axis selection (`X` for axis 0, `Y` otherwise).
- Verify the calibration displacement and calculated sensitivity.
- Check for a zero, negative, or implausible sensitivity.
- Confirm that millimetres and degrees match the actual readout configuration.

## Shutdown limitations

The low-level serial `disconnect()` methods send `Q,` but do not close their
`serial.Serial` objects. If a process must release ports without terminating,
applications should explicitly close the serial objects after sending the
device command, for example:

```python
neo.disconnect()
neo.Motors.connection.close()
neo.Readout_XY.connection.close()
neo.Readout_Phi.connection.close()
```

Only do this after `connect()` successfully created all three serial-controller
attributes. The high-level `disconnect()` also closes the owned VNA session.
This documents the current serial behavior; changing serial resource ownership
should be handled as a separate code revision with tests.

## Hardware validation sequence

Use this progression for commissioning:

1. Run the automated VNA tests.
2. Connect to the PNA and verify only `*IDN?`.
3. Acquire a trace from a known static setup and compare it with the PNA
   display or an exported reference trace.
4. Connect each serial device independently without motion.
5. Verify readout queries.
6. Command small single-axis movements at low speed.
7. Verify calibration factors and return-to-zero repeatability.
8. Dry-run the scan index sequence without connected mechanics if possible.
9. Run a small supervised scan without RF acquisition.
10. Integrate position and RF acquisition only after defining the persistent
    data format and failure policy.

## Information to record with bug reports

- operating system and Python version;
- installed versions of NumPy, pySerial, PyVISA, and the VISA backend;
- PNA `*IDN?` response and resource string, with network-sensitive details
  redacted when necessary;
- serial-port mapping and driver constructor arguments;
- exact method call and complete exception or console output;
- whether the failure is reproducible with fake tests, static hardware, or
  motion disabled; and
- the smallest safe sequence that reproduces the problem.

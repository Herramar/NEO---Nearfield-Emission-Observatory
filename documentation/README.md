# NEO Documentation

This directory documents the current implementation of the Nearfield Emission
Observatory (NEO). It describes what the code does today, including known
limitations. It does not imply that hardware combinations or scan modes not
listed here have been validated.

## Documentation map

- [Architecture](architecture.md): software layers, communication paths, and
  component responsibilities.
- [Hardware and installation](hardware-and-installation.md): dependencies,
  serial and Ethernet setup, initial checks, and safety precautions.
- [Controller API](controller-api.md): `NEO_Controller`, `VXC_Controller`, and
  `VRO_Controller` constructors and methods.
- [VNA guide](vna-guide.md): PNA connection, sweep configuration, triggering,
  binary transfer, returned arrays, and examples.
- [Scan data model](scan-data-model.md): spiral traversal, matrix definitions,
  coordinate conventions, and current acquisition gap.
- [Testing and troubleshooting](testing-and-troubleshooting.md): test commands,
  common failures, diagnostics, and validation checklist.

## Current implementation status

| Capability | Status |
| --- | --- |
| Three-axis motor commands | Implemented through `VXC_Controller` |
| XY and angular readout | Implemented through `VRO_Controller` |
| Motion calibration and homing | Implemented; requires supervised hardware validation |
| Spiral-grid traversal | Implemented for the demonstrated 5 x 5 use case |
| Ethernet PNA connection | Implemented through `VNA_Controller` |
| S-parameter sweep acquisition | Implemented as an independent NumPy-returning API |
| VNA acquisition at every scan position | Not integrated into `NEO_Controller.measure()` |
| Automated hardware integration tests | Not present |

## Naming and units

- `X` is the horizontal translation coordinate in millimetres.
- `Z` is the vertical translation coordinate in millimetres. Some internal
  variables and comments call the second array index `Y`; the public motion
  methods and result descriptions use `Z`.
- `Phi` is the rotation angle in degrees.
- VNA frequencies and IF bandwidth are in hertz.
- VNA source power is in dBm.
- VNA corrected S-parameter data are dimensionless complex ratios.

## Important scope boundary

`VNA_Controller.measure()` acquires a frequency trace from the PNA. In
contrast, `NEO_Controller.measure()` currently moves the positioner and fills
its `measurement_matrix` with the value `1` at visited positions. Applications
must not treat that scan matrix as measured RF data until the two controllers
are explicitly integrated.

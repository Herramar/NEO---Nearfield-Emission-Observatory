# Architecture

## Overview

The high-level `NEO_Controller` owns and coordinates four peer hardware
drivers: the motor controller, two position readouts, and the PNA driver.
Positioning and RF acquisition remain separate high-level operations so their
different array shapes and failure modes stay explicit.

```mermaid
flowchart LR
    App[Tester.py or user application]
    NEO[NEO_Controller]
    VXC[VXC_Controller]
    XY[VRO_Controller: XY]
    Phi[VRO_Controller: Phi]
    VNA[VNA_Controller]
    Motors[Three-axis motor controller]
    XYHW[XY readout]
    PhiHW[Angular readout]
    PNA[Keysight PNA]

    App --> NEO
    NEO --> VXC -->|Serial| Motors
    NEO --> XY -->|Serial| XYHW
    NEO --> Phi -->|Serial| PhiHW
    NEO --> VNA
    VNA -->|Ethernet VISA/SCPI| PNA
```

`NEO_Controller.connect()` connects all four drivers. Applications configure
and acquire the owned PNA through `configure_vna()` and `measure_vna()` or,
when lower-level control is required, through the `VNA` attribute. Spatial
`measure()` does not yet call the VNA at every grid position.

## Repository layout

```text
.
|-- README.md
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
|-- neo/
|   |-- __init__.py
|   |-- neo_driver.py
|   `-- drivers/
|       |-- __init__.py
|       |-- vna_driver.py
|       |-- vro_driver.py
|       `-- vxc_driver.py
`-- tests/
    |-- test_neo_vna_integration.py
    `-- test_vna_driver.py
```

## Component responsibilities

### `neo/neo_driver.py`

Provides `NEO_Controller`, the hardware facade. It opens three serial
connections and one Ethernet PNA connection, estimates distance-per-step and
angle-per-step sensitivities, homes the axes, translates or rotates the stage,
traverses a grid in an outward spiral, and exposes PNA configuration and trace
acquisition.

### `neo/drivers/vxc_driver.py`

Provides `VXC_Controller`. It formats the motor-controller command language,
maps motor numbers 1, 2, and 3 to horizontal, vertical, and rotary motion, and
waits for the `^` completion character after each commanded move.

### `neo/drivers/vro_driver.py`

Provides `VRO_Controller`. One instance is used for XY readout (`type=0`) and
another for angular readout (`type=1`). It selects echo mode, reads an axis,
and sends the readout's home-setting command.

### `neo/drivers/vna_driver.py`

Provides the low-level `VNA_Controller` used by `NEO_Controller`. It opens a
PyVISA resource, identifies the PNA,
creates or selects an S-parameter measurement, configures a linear sweep,
performs a synchronized acquisition, and converts binary corrected data into
a NumPy matrix.

### `Tester.py`

Demonstrates the positioning workflow using fixed COM ports and a configurable
PNA IP address. It connects all four controllers, calibrates, homes, performs a
5 x 5 scan at `Phi=0`, rotates to 90 degrees, performs a second scan, returns
home, and prints the arrays. It does not yet configure or acquire a VNA trace.

## Connection ownership

- `NEO_Controller.connect()` constructs the motor, two readout, and VNA driver
  instances and calls all four `connect()` methods.
- The serial drivers construct their own `serial.Serial` objects.
- The VNA owned by `NEO_Controller` normally constructs its own PyVISA
  resource manager. Tests or applications may inject a resource manager
  through `resourceManagerVNA`.
- An injected VNA resource manager remains owned by the caller and is not
  closed by `VNA_Controller.disconnect()`.

## Error model

The code uses two error styles:

- Serial and high-level positioning methods generally print an error and
  return `False` or `None`.
- VNA `connect()` prints an error, stores the exception in `last_error`, and
  returns `False`. Other VNA methods raise `RuntimeError` or `ValueError` for
  connection, response, or argument errors.

Applications should check every connection and motion result and use
`try/finally` around connected hardware.

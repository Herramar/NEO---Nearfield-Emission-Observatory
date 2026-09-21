# Scan Data Model

## Current positioning scan

`NEO_Controller.measure(m, n, distance)` starts at an index near the centre of
an `m` by `n` array and traverses outward in a spiral. The direction sequence
is right, down, left, up. The number of moves in a direction increases after
each pair of directions.

The default example calls:

```python
order, positions, measurements = neo.measure(5, 5, 1)
```

where the code assumes `distance` is in millimetres.

## Starting index and traversal

The starting array index is:

```text
x = (m - 1) // 2
y = (n - 1) // 2
```

The starting cell receives order value `0`. After each motor movement, the
code updates the array index, writes the traversal count, waits 0.2 s, and
reads the XY position.

The current implementation updates the arrays before checking whether the
new indices are within bounds. It has no validation for positive integer
dimensions, odd dimensions, rectangular grids, or a positive step distance.
The supplied 5 x 5 example is the documented use case; validate other grid
shapes in software and with motion disabled before using hardware.

## Returned arrays

### `order_matrix`

Shape: `(m, n)`

Contains the integer-like traversal number stored in a floating NumPy array.
The centre is `0`, the first moved-to cell is `1`, and subsequent cells follow
the spiral order.

### `position_matrix`

Shape: `(m, n, 2)`

| Final-axis index | Quantity | Assumed unit |
| ---: | --- | --- |
| 0 | Horizontal `X` readout | mm |
| 1 | Vertical `Z` readout | mm |

Although local variables and some comments use `y`, the high-level public
motion methods call the vertical physical axis `Z`.

The values are the readouts after each movement and a fixed 0.2 s delay. They
are not commanded coordinates and do not include an uncertainty estimate.

### `measurement_matrix`

Shape: `(m, n)`

This is not an RF measurement matrix. The current implementation writes `1`
for each visited position, including the starting position. It is therefore a
visit marker only.

## Two-angle example in `Tester.py`

`Tester.py` allocates arrays for scans at 0 and 90 degrees:

| Array | Shape in the example | Meaning |
| --- | --- | --- |
| `order` | `(5, 5, 2)` | Traversal order for the two rotation angles |
| `positions` | `(5, 5, 4)` | X and Z readouts for each angle |
| `measurements` | `(5, 5, 2)` | Visit markers for each angle |

The final axis of `order` and `measurements` selects the angle. The final axis
of `positions` is `[X at 0 degrees, Z at 0 degrees, X at 90 degrees, Z at 90
degrees]`.

## Relationship to VNA data

One call to `NEO_Controller.measure_vna()` delegates to the owned VNA driver
and returns shape `(Nf, 3)`, where `Nf` is the number of frequency points. A
frequency-resolved complex scan cannot fit in the existing two-dimensional
`measurement_matrix` without defining an additional frequency axis.

A natural future representation would separate the frequency vector from a
complex scan cube:

```text
frequency_hz:       (Nf,)
s_parameter_scan:   (m, n, Nf) complex
positions:          (m, n, 2) float
order:              (m, n) integer
```

For multiple angles, a further angle axis could be added:

```text
s_parameter_scan:   (Nphi, m, n, Nf) complex
positions:          (Nphi, m, n, 2) float
phi_deg:             (Nphi,)
```

This is a recommended future data model, not an implemented repository
feature. Before integration, decide how to handle failed traces, retries,
metadata, partial scans, file persistence, and memory use.

## Coordinate and RF validation

For each scan configuration, verify:

- commanded direction versus measured X/Z sign;
- step size versus readout displacement;
- starting point and complete scan envelope;
- positioning repeatability after returning to a point;
- settling time before acquisition;
- cable-flex and probe-loading effects across the travel range;
- frequency-axis equality across all PNA traces; and
- a policy for invalid, interrupted, or saturated measurements.

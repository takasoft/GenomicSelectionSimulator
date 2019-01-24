# GenomicSelectionSimulator

Research simulator for plant breeding with a Python/Qt GUI and a NumPy engine.
It models repeated selection and crossing of plants using genomic estimated
breeding values (GEBVs).

The [genetic linkage engine](genetic_linkage/README.md) is maintained in this
repository alongside the simulator. Genetic linkage describes the tendency of
nearby loci on a chromosome to be inherited together. "Generic linkage" was a
naming mistake in the original module.

Developed as part of an [undergraduate research project at Iowa State University](http://lib.dr.iastate.edu/undergradresearch_symposium/2017/presentations/82/).
See the [research poster](poster.pdf).

## Usage

With Python 3.9 or newer, install the engine from the repository root:

```text
python -m pip install .
```

This installs `genetic_linkage` with NumPy only. The GUI is not needed to use it:

```python
import numpy as np
from genetic_linkage import cross2

L1 = np.array([[0, 0, 0], [1, 1, 1]], dtype=np.int8)
L2 = np.array([[1, 1, 1], [0, 0, 0]], dtype=np.int8)
RF = np.array([0.05, 0.05])
progeny = cross2(L1, L2, RF, 3)  # Shape: (3, 2, 3)
```

To install the optional GUI dependencies and launch the existing simulator,
run these commands from the source checkout:

```text
python -m pip install ".[gui]"
python main.py
```

The GUI remains the original research application, not a redesigned interface.
`from GenericLinkage import cross2` still works for existing callers, but new
code should use `genetic_linkage`. There is only one implementation of `cross2`.

Run the engine tests without GUI dependencies:

```text
python -m unittest discover -s tests -v
```

The bundled engine retains its [original MIT license](genetic_linkage/LICENSE).
That license notice covers the linkage code, not a new license grant for the
rest of the simulator.

## Contributions

- [Takao Shibamoto](https://github.com/takasoft) - main developer
- [Dr. Lizhi Wang](https://www.imse.iastate.edu/directory/faculty/lizhi-wang/) - mentor
- [ISU Industrial and Manufacturing Systems Engineering](https://www.imse.iastate.edu/)
- [ISU University Honors Program](https://www.honors.iastate.edu/)

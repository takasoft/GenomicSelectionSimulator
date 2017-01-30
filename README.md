# Genetic linkage

A NumPy-only module for generating progeny from two diploid genomes.
Genetic linkage describes the tendency of nearby loci on a chromosome to be
inherited together.

Install from the repository root:

```text
python -m pip install .
```

```python
import numpy as np
from genetic_linkage import cross2

L1 = np.array([[0, 0, 0], [1, 1, 1]], dtype=np.int8)
L2 = np.array([[1, 1, 1], [0, 0, 0]], dtype=np.int8)
RF = np.array([0.05, 0.05])
progeny = cross2(L1, L2, RF, 3)
assert progeny.shape == (3, 2, 3)
```

See the [module documentation](genetic_linkage/README.md) for the algorithm,
input shapes, and reproducibility.
The legacy `from GenericLinkage import cross2` import remains available.

The module retains its [original MIT license](genetic_linkage/LICENSE).

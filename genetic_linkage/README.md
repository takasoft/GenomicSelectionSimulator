# Genetic linkage

A NumPy-only engine for generating progeny from two diploid genomes.
Installing from the repository root with `python -m pip install .`
installs the engine and the legacy `GenericLinkage` import.

## API and algorithm

Use `from genetic_linkage import cross2`, then call `cross2(L1, L2, RF, k)`.

| Argument | Meaning |
| :--- | :--- |
| `L1`, `L2` | Parent arrays of shape `(2, n)`, one haplotype per row |
| `RF` | One-dimensional array of `n - 1` recombination probabilities |
| `k` | Nonnegative integer number of progeny |
| Return | Array of shape `(k, 2, n)`, one inherited haplotype per parent |

Each column is a locus. Alleles can be represented as 0 or 1,
with 1 marking an allele treated as favorable in a simulation.

For each parent, the algorithm randomly selects a starting haplotype with
equal probability. At each following locus, it switches haplotypes with the
corresponding probability in `RF`. Combining one resulting haplotype from each
parent produces one diploid offspring. This models genetic linkage, not
"generic linkage."

```python
import numpy as np
from genetic_linkage import cross2

L1 = np.array([[0, 0, 0, 0, 0], [1, 1, 1, 1, 1]], dtype=np.int8)
L2 = np.array([[1, 1, 1, 1, 1], [0, 0, 0, 0, 0]], dtype=np.int8)
RF = np.array([0.05, 0.05, 0.05, 0.05])
np.random.seed(7)
progeny = cross2(L1, L2, RF, 3)
assert progeny.shape == (3, 2, 5)
```

The existing algorithm and NumPy global random-state behavior are preserved.
Inputs must already have the documented shapes. The module does not
add input validation or change probability handling. For biological
recombination fractions, use values between 0 and 0.5.

## Experimental variants and provenance

The former `GenericLinkageBeta.py` batching variants are available only through
explicit imports:

```python
from genetic_linkage.experimental import cross2mp, cross2sp
```

`cross2mp` uses multiprocessing, while `cross2sp` processes batches sequentially.
Both call the same `cross2` implementation.
They retain the legacy CPU-dependent batch sizing and progress output.
They still collect the full result in memory and are not streaming APIs.
Multiprocessing random-state behavior depends on the process start method,
so a parent-process seed does not guarantee reproducible or independent worker
streams. Prefer `cross2` for reproducible simulations.

On Windows and other systems using the spawn start method, call `cross2mp`
from a script inside an `if __name__ == "__main__":` guard.

The code and algorithm documentation were migrated from the former
`genetic-linkage` repository at revision
`ba576517b6dfc0621e803494106e67329a21ad9b`.
The default implementation omits the original module's debug prints.
The old timing examples are replaced by small regression tests in this repository.

The [original MIT license](LICENSE) is retained for the linkage code.

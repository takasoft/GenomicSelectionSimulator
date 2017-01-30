"""NumPy-only genetic linkage simulation."""

import numpy as np

__all__ = ["cross2"]


def cross2(L1, L2, RF, k):
    """Generate k diploid progeny from two parents.

    L1 and L2 are arrays of shape (2, n), with one haplotype per row.
    RF is a one-dimensional array of n - 1 recombination probabilities
    between adjacent loci. The result has shape (k, 2, n).

    Uses NumPy's global random state, preserving the original algorithm
    and behavior of np.random.seed().
    """
    n = L1.shape[1]

    # The first draw selects a haplotype. Later draws decide when to switch.
    probabilities = np.hstack((np.array([0.5]), RF))
    RC = np.random.random((2*k, n)) <= np.tile(probabilities, [2*k, 1])

    # Cumulative signs track the selected haplotype after every switch.
    cumprodRC = np.cumprod(1-2*RC, axis=1, dtype=np.int8)
    fDown = cumprodRC < 0
    fDown = np.reshape(fDown, (2*k, n), order='F')
    fUp = cumprodRC > 0
    fUp = np.reshape(fUp, (2*k, n), order='F')

    splittedL1 = np.vsplit(L1, 2)
    splittedL2 = np.vsplit(L2, 2)
    combinedUp = np.vstack((splittedL1[0], splittedL2[0]))
    combinedDown = np.vstack((splittedL1[1], splittedL2[1]))
    Y1 = np.tile(combinedUp, [k, 1])
    Y2 = np.tile(combinedDown, [k, 1])
    Y = fUp*Y1 + fDown*Y2
    Y = np.reshape(Y, (k, 2, n), order='C')
    return Y

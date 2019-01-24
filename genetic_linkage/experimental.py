"""Legacy batching experiments, not used by the simulator's default path."""

import multiprocessing as mp
from functools import partial

import numpy as np

from . import cross2

__all__ = ["cross2mp", "cross2sp"]


def cross2iterable(L1, L2, RF, k, i):
    """Run one batch from the original experimental implementation."""
    print("Job " + str(i))
    return cross2(L1, L2, RF, k)


def cross2mp(L1, L2, RF, k):
    """Generate progeny in worker processes using the legacy batch layout.

    Call only from an if __name__ == '__main__' guard when using spawn.
    A seed in the calling process does not guarantee reproducible results.
    """
    maxTotalJobSize = 200
    numCores = mp.cpu_count()
    numJobs = numCores
    progenyPerJob = k//numJobs

    while progenyPerJob*numCores > maxTotalJobSize:
        numJobs = numJobs * 2
        progenyPerJob = k//numJobs

    theRestNum = k % numJobs
    print("numJobs {}, progenyPerJob {}, theRestNum {}".format(
        numJobs, progenyPerJob, theRestNum
    ))

    func = partial(cross2iterable, L1, L2, RF, progenyPerJob)
    with mp.Pool() as pool:
        progenyList = pool.map(func, range(numJobs))

    progenies = np.array(progenyList)
    progenies = np.reshape(progenies, (numJobs*progenyPerJob, 2, L1.shape[1]))
    if theRestNum != 0:
        theRestProgenies = cross2iterable(L1, L2, RF, theRestNum, numJobs)
        progenies = np.concatenate((progenies, theRestProgenies), axis=0)
    return progenies


def cross2sp(L1, L2, RF, k):
    """Generate progeny in sequential batches using the legacy batch layout."""
    maxTotalJobSize = 100
    numCores = mp.cpu_count()
    numJobs = numCores
    progenyPerJob = k//numJobs

    while progenyPerJob*numCores > maxTotalJobSize:
        numJobs = numJobs * 2
        progenyPerJob = k//numJobs

    theRestNum = k % numJobs
    print("numJobs {}, progenyPerJob {}, theRestNum {}".format(
        numJobs, progenyPerJob, theRestNum
    ))

    progenyList = [
        cross2iterable(L1, L2, RF, progenyPerJob, i) for i in range(numJobs)
    ]
    progenies = np.array(progenyList)
    progenies = np.reshape(progenies, (numJobs*progenyPerJob, 2, L1.shape[1]))
    if theRestNum != 0:
        theRestProgenies = cross2iterable(L1, L2, RF, theRestNum, numJobs)
        progenies = np.concatenate((progenies, theRestProgenies), axis=0)
    return progenies

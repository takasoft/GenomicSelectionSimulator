# GenomicSelectionSimulator

Research simulator for plant breeding with a Python/Qt GUI and a NumPy engine.
It models repeated selection and crossing of plants using genomic estimated
breeding values (GEBVs).

The [genetic linkage engine](genetic_linkage/README.md) is maintained in this
repository alongside the simulator. Genetic linkage describes the tendency of
nearby loci on a chromosome to be inherited together.

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

Calculations and data preparation run in worker threads. Qt handles status and
plot updates on the main thread and queues redraws. Pause and Stop take effect
between calculation steps. Closing requests cancellation and waits for the
worker to finish without blocking the event loop. File loading supports MATLAB
HDF5 `.mat` files.

**Synthetic poster-scale dataset.** The bundled
[demo data](demo/synthetic-poster-demo.mat) models 300 plants from 20 founders,
with 14,000 loci in 100 linked blocks. The
[Python generator](scripts/generate_synthetic_poster_demo.py) creates the NumPy
inputs and runs a seeded reference simulation to illustrate the poster's score
scale and selection curve. This is synthetic data, not the original research
dataset.

The binary `.mat` file is stored with Git LFS. Install Git LFS and retrieve
the data before loading it:

```text
git lfs install
git lfs pull
```

In the GUI, choose **File > Open Data File**, select
`demo\synthetic-poster-demo.mat`, then press **Start**.
The [metadata](demo/synthetic-poster-demo.json) records the generation parameters,
dataset seed `2017`, simulation seed `43`, and expected mean GEBVs.
The reference run rises from about 4.67 million to 8.04 million and levels off
in later generations. Exact reference results require `np.random.seed(43)`
before starting the simulation. Normal interactive runs can vary because the
GUI does not automatically apply the seed from the metadata file.

With the GUI dependencies installed, regenerate the bundled dataset and reference
results from the repository root:

```powershell
python scripts\generate_synthetic_poster_demo.py `
  --output-path demo\synthetic-poster-demo.mat `
  --metadata-path demo\synthetic-poster-demo.json `
  --overwrite
```

Both paths are required and include the filename. They can use different
directories, and missing parent directories are created automatically.
The example uses `--overwrite` to replace the bundled files. Without it, the
generator refuses to replace existing output files.
The input arrays and reference scores are reproducible from the recorded seeds.
HDF5 container bytes can depend on the installed library versions.

`from GenericLinkage import cross2` still works for existing callers, but new
code should use `genetic_linkage`. There is only one implementation of `cross2`.

Run the engine tests without GUI dependencies:

```text
python -m unittest discover -s tests -v
```

With the GUI dependencies installed, run the offscreen UI regression tests:

```text
python -m unittest discover -s tests\gui -v
```

These cover GUI-thread rendering, event-loop responsiveness, pause and restart,
stopping and closing, background data loading, and dataset regeneration.

The bundled engine retains its [original MIT license](genetic_linkage/LICENSE).
That license notice covers the linkage code, not a new license grant for the
rest of the simulator.

## Contributions

- [Takao Shibamoto](https://github.com/takasoft) - main developer
- [Dr. Lizhi Wang](https://www.imse.iastate.edu/directory/faculty/lizhi-wang/) - mentor
- [ISU Industrial and Manufacturing Systems Engineering](https://www.imse.iastate.edu/)
- [ISU University Honors Program](https://www.honors.iastate.edu/)

"""Reproduce the synthetic GenomicSelectionSimulator poster-scale dataset.

Requires NumPy, h5py, and the installed genetic_linkage package.
This generates demonstration data, not the original research dataset.
"""

import argparse
import json
import tempfile
from pathlib import Path

import h5py
import numpy as np

from genetic_linkage import cross2


DATASET_SEED = 2017
SIMULATION_SEED = 43


def _scores(genomes, effects):
    return np.array([
        np.sum((genome[0] + genome[1]) * effects) for genome in genomes
    ])


def build_dataset():
    rng = np.random.RandomState(DATASET_SEED)
    blocks, block_size = 100, 140
    founders = (rng.random_sample((20, 2, blocks)) < 0.38).astype(np.int8)
    genomes = np.repeat(np.repeat(founders, 15, axis=0), block_size, axis=2)
    effects = rng.uniform(0, 100, blocks * block_size)
    effects *= 12369035.6329792 / (2 * effects.sum())
    rf = np.zeros(blocks * block_size - 1)
    rf[block_size - 1::block_size] = 0.01
    data = {
        'Geno': genomes,
        'RF': rf[np.newaxis, :],
        'eft': effects[np.newaxis, :],
        'gebvs': _scores(genomes, effects)[:, np.newaxis],
        'potentials': np.array([0, 2 * effects.sum()]),
    }
    metadata = {
        'kind': 'Synthetic poster-scale demonstration, not the original research dataset',
        'dataset_seed': DATASET_SEED,
        'simulation_seed': SIMULATION_SEED,
        'population_size': 300,
        'founders': 20,
        'replicates_per_founder': 15,
        'loci': 14000,
        'linkage_blocks': blocks,
        'loci_per_block': block_size,
        'initial_favorable_allele_probability': 0.38,
        'between_block_recombination': 0.01,
        'within_block_recombination': 0.0,
        'theoretical_upper_bound': float(2 * effects.sum()),
    }

    # cross2 uses NumPy's global RNG. Leave the caller's random state unchanged.
    random_state = np.random.get_state()
    means = []
    try:
        np.random.seed(SIMULATION_SEED)
        for generation in range(11):
            values = _scores(genomes, effects)
            means.append(float(values.mean()))
            if generation < 10:
                selected = genomes[np.argsort(values)[::-1][:30]]
                genomes = np.concatenate([
                    cross2(selected[i], selected[i + 1], rf, 20)
                    for i in range(0, 30, 2)
                ])
    finally:
        np.random.set_state(random_state)
    metadata['expected_mean_gebv_by_generation'] = means
    return data, metadata


def generate_dataset(output_path, metadata_path, overwrite=False):
    mat_path = Path(output_path)
    json_path = Path(metadata_path)
    resolved_mat = mat_path.resolve()
    resolved_json = json_path.resolve()
    if resolved_mat == resolved_json:
        raise ValueError('Dataset and metadata paths must refer to different files.')
    if resolved_mat in resolved_json.parents or resolved_json in resolved_mat.parents:
        raise ValueError('An output file cannot be the parent directory of the other output.')
    for path in (mat_path, json_path):
        if path.is_dir():
            raise IsADirectoryError('Output path must be a file: {}'.format(path))
        if not overwrite and (path.exists() or path.is_symlink()):
            raise FileExistsError(
                '{} already exists. Use --overwrite to replace the demo files.'.format(path)
            )
    mat_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    data, metadata = build_dataset()
    # Stage each file on its destination filesystem so replacement works across drives.
    with (
        tempfile.TemporaryDirectory(prefix='.poster-demo-', dir=mat_path.parent) as mat_directory,
        tempfile.TemporaryDirectory(prefix='.poster-demo-', dir=json_path.parent) as json_directory,
    ):
        mat_temp = Path(mat_directory) / mat_path.name
        json_temp = Path(json_directory) / json_path.name
        with h5py.File(mat_temp, 'w') as output:
            output.create_dataset('Geno', data=data['Geno'], compression='gzip')
            for name in ('RF', 'eft', 'gebvs', 'potentials'):
                output[name] = data[name]
            for key, value in metadata.items():
                if key != 'expected_mean_gebv_by_generation':
                    output.attrs[key] = value
        json_temp.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        mat_temp.replace(mat_path)
        json_temp.replace(json_path)
    return mat_path, json_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output-path', type=Path, required=True,
        help='Path and filename for the generated MAT dataset.',
    )
    parser.add_argument(
        '--metadata-path', type=Path, required=True,
        help='Path and filename for the generated JSON metadata.',
    )
    parser.add_argument('--overwrite', action='store_true', help='Replace existing demo files.')
    args = parser.parse_args()
    try:
        paths = generate_dataset(args.output_path, args.metadata_path, args.overwrite)
    except (OSError, ValueError) as error:
        parser.exit(1, 'error: {}\n'.format(error))
    for path in paths:
        print('Wrote {}'.format(path))


if __name__ == '__main__':
    main()

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import h5py
import numpy as np

from scripts.generate_synthetic_poster_demo import build_dataset, generate_dataset


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'generate_synthetic_poster_demo.py'


class DemoDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        output = Path(cls.directory.name)
        cls.mat_path, cls.json_path = generate_dataset(
            output / 'dataset files' / 'chosen-population.mat',
            output / 'run reports' / 'chosen-metadata.json',
        )
        cls.expected_metadata = json.loads(
            (ROOT / 'demo' / 'synthetic-poster-demo.json').read_text(encoding='utf-8')
        )

    def test_generated_arrays_and_attributes_match_bundled_data(self):
        with h5py.File(self.mat_path, 'r') as actual:
            with h5py.File(ROOT / 'demo' / 'synthetic-poster-demo.mat', 'r') as expected:
                self.assertEqual(set(actual), set(expected))
                self.assertEqual(dict(actual.attrs), dict(expected.attrs))
                for name in expected:
                    with self.subTest(dataset=name):
                        self.assertEqual(actual[name].dtype, expected[name].dtype)
                        np.testing.assert_array_equal(actual[name][()], expected[name][()])

    def test_generated_metadata_and_reference_curve_match(self):
        actual = json.loads(self.json_path.read_text(encoding='utf-8'))
        self.assertEqual(actual, self.expected_metadata)
        self.assertEqual(len(actual['expected_mean_gebv_by_generation']), 11)

    def test_custom_filenames_and_separate_directories(self):
        self.assertEqual(self.mat_path.name, 'chosen-population.mat')
        self.assertEqual(self.json_path.name, 'chosen-metadata.json')
        self.assertNotEqual(self.mat_path.parent, self.json_path.parent)
        self.assertTrue(self.mat_path.is_file())
        self.assertTrue(self.json_path.is_file())
        self.assertFalse((Path(self.directory.name) / 'synthetic-poster-demo.mat').exists())
        self.assertFalse((Path(self.directory.name) / 'synthetic-poster-demo.json').exists())

    def test_build_preserves_callers_random_state(self):
        previous = np.random.get_state()
        try:
            np.random.seed(901)
            expected = np.random.get_state()
            build_dataset()
            actual = np.random.get_state()
            self.assertEqual(actual[0], expected[0])
            np.testing.assert_array_equal(actual[1], expected[1])
            self.assertEqual(actual[2:], expected[2:])
        finally:
            np.random.set_state(previous)

    def test_each_existing_output_is_protected_before_generation(self):
        for filename in ('synthetic-poster-demo.mat', 'synthetic-poster-demo.json'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / filename
                path.write_bytes(b'keep existing content')
                with patch('scripts.generate_synthetic_poster_demo.build_dataset') as build:
                    with self.assertRaisesRegex(FileExistsError, 'Use --overwrite'):
                        generate_dataset(
                            Path(directory) / 'synthetic-poster-demo.mat',
                            Path(directory) / 'synthetic-poster-demo.json',
                        )
                    build.assert_not_called()
                self.assertEqual(path.read_bytes(), b'keep existing content')
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            mat_path = Path(directory) / 'dataset files' / 'population.mat'
            json_path = Path(directory) / 'metadata files' / 'run.json'
            mat_path.parent.mkdir()
            mat_path.write_bytes(b'keep existing content')
            command = [
                sys.executable, str(SCRIPT), '--output-path', str(mat_path),
                '--metadata-path', str(json_path),
            ]
            refused = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(refused.returncode, 1)
            self.assertIn('Use --overwrite', refused.stderr)
            self.assertEqual(mat_path.read_bytes(), b'keep existing content')
            self.assertFalse(json_path.parent.exists())
            written = subprocess.run(
                command + ['--overwrite'], cwd=ROOT,
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            actual = json.loads(json_path.read_text(encoding='utf-8'))
            self.assertEqual(actual, self.expected_metadata)
            with h5py.File(mat_path, 'r') as data:
                self.assertEqual(data['Geno'].shape, (300, 2, 14000))

    def test_cli_reports_unusable_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'not-a-directory'
            output.write_text('preserve this file', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--output-path', str(output / 'demo.mat'),
                 '--metadata-path', str(Path(directory) / 'metadata.json')],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn('error:', result.stderr)
            self.assertEqual(output.read_text(encoding='utf-8'), 'preserve this file')

    def test_identical_or_normalized_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'same.mat'
            variants = [output, Path(directory) / 'unused' / '..' / 'same.mat']
            for metadata in variants:
                for overwrite in (False, True):
                    with self.subTest(metadata=metadata, overwrite=overwrite):
                        with patch('scripts.generate_synthetic_poster_demo.build_dataset') as build:
                            with self.assertRaisesRegex(ValueError, 'different files'):
                                generate_dataset(output, metadata, overwrite=overwrite)
                            build.assert_not_called()
            self.assertFalse(any(Path(directory).iterdir()))

    def test_output_paths_cannot_be_ancestors_of_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / 'output'
            child = parent / 'metadata.json'
            for paths in ((parent, child), (child, parent)):
                with self.subTest(paths=paths):
                    with patch('scripts.generate_synthetic_poster_demo.build_dataset') as build:
                        with self.assertRaisesRegex(ValueError, 'parent directory'):
                            generate_dataset(*paths, overwrite=True)
                        build.assert_not_called()
            self.assertFalse(any(Path(directory).iterdir()))

    def test_existing_directory_is_not_an_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'folder'
            folder.mkdir()
            other = Path(directory) / 'other'
            for paths in ((folder, other), (other, folder)):
                with self.subTest(paths=paths):
                    with patch('scripts.generate_synthetic_poster_demo.build_dataset') as build:
                        with self.assertRaises(IsADirectoryError):
                            generate_dataset(*paths, overwrite=True)
                        build.assert_not_called()
            self.assertTrue(folder.is_dir())
            self.assertFalse(other.exists())

    def test_same_basename_in_different_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            mat_path = Path(directory) / 'arrays' / 'result'
            json_path = Path(directory) / 'metadata' / 'result'
            generate_dataset(mat_path, json_path)
            with h5py.File(mat_path, 'r') as data:
                self.assertEqual(data['Geno'].shape, (300, 2, 14000))
            self.assertEqual(
                json.loads(json_path.read_text(encoding='utf-8')), self.expected_metadata
            )

    def test_cli_requires_both_output_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            mat_path = Path(directory) / 'demo.mat'
            json_path = Path(directory) / 'metadata.json'
            variants = [
                ([], '--output-path'),
                (['--output-path', str(mat_path)], '--metadata-path'),
                (['--metadata-path', str(json_path)], '--output-path'),
            ]
            for arguments, missing in variants:
                with self.subTest(arguments=arguments):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT)] + arguments,
                        cwd=ROOT, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(missing, result.stderr)
            self.assertFalse(any(Path(directory).iterdir()))

    def test_cli_reports_colliding_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'same-file'
            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--output-path', str(output),
                 '--metadata-path', str(output), '--overwrite'],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn('different files', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()

import contextlib
import io
import multiprocessing as mp
import subprocess
import sys
import unittest
from functools import partial
from unittest.mock import patch

import numpy as np

import GenericLinkage
import genetic_linkage
from genetic_linkage import cross2, experimental


class GeneticLinkageTests(unittest.TestCase):
    def setUp(self):
        self.random_state = np.random.get_state()
        self.addCleanup(np.random.set_state, self.random_state)
        self.L1 = np.array([[0, 1, 0, 1], [1, 0, 1, 0]], dtype=np.int8)
        self.L2 = np.array([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.int8)
        self.RF = np.array([0.05, 0.1, 0.2])

    def test_legacy_import_is_the_same_function(self):
        self.assertIs(GenericLinkage.cross2, cross2)
        self.assertIs(experimental.cross2, cross2)

    def test_import_needs_no_gui_or_experimental_module(self):
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; import genetic_linkage; import GenericLinkage; "
             "assert not any(name.split('.')[0] in "
             "('PyQt5', 'matplotlib', 'h5py', 'multiprocessing') "
             "for name in sys.modules); "
             "assert 'genetic_linkage.experimental' not in sys.modules"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_experimental_functions_are_not_default_exports(self):
        self.assertEqual(genetic_linkage.__all__, ["cross2"])
        self.assertFalse(hasattr(genetic_linkage, "cross2mp"))
        self.assertFalse(hasattr(genetic_linkage, "cross2sp"))

    def test_shape_dtype_and_parental_inheritance(self):
        for dtype in (np.int8, np.int32, np.bool_):
            for n in (1, 4):
                for k in (0, 1, 7):
                    with self.subTest(dtype=dtype, n=n, k=k):
                        L1 = self.L1[:, :n].astype(dtype)
                        L2 = self.L2[:, :n].astype(dtype)
                        result = cross2(L1, L2, self.RF[:n-1], k)
                        self.assertEqual(result.shape, (k, 2, n))
                        self.assertEqual(result.dtype, dtype)
                        for index, parent in enumerate((L1, L2)):
                            inherited = result[:, index, :]
                            self.assertTrue(np.all(
                                (inherited == parent[0]) | (inherited == parent[1])
                            ))

    def test_seed_reproduces_result_without_mutating_inputs(self):
        originals = [array.copy() for array in (self.L1, self.L2, self.RF)]
        np.random.seed(7)
        first = cross2(self.L1, self.L2, self.RF, 9)
        np.random.seed(7)
        second = cross2(self.L1, self.L2, self.RF, 9)
        np.testing.assert_array_equal(first, second)
        for actual, expected in zip((self.L1, self.L2, self.RF), originals):
            np.testing.assert_array_equal(actual, expected)

    def test_haplotype_switches_and_progeny_order(self):
        L1 = np.array([[10, 11, 12, 13], [20, 21, 22, 23]])
        L2 = np.array([[30, 31, 32, 33], [40, 41, 42, 43]])
        draws = np.array([
            [0.8, 0.9, 0.1, 0.9],
            [0.2, 0.05, 0.9, 0.1],
            [0.3, 0.5, 0.7, 0.2],
            [0.7, 0.05, 0.1, 0.9],
        ])
        with patch("genetic_linkage.np.random.random", return_value=draws) as random:
            result = cross2(L1, L2, np.array([0.1, 0.2, 0.3]), 2)
        random.assert_called_once_with((4, 4))
        np.testing.assert_array_equal(result, [
            [[10, 11, 22, 23], [40, 31, 32, 43]],
            [[20, 21, 22, 13], [30, 41, 32, 33]],
        ])

    def test_zero_recombination_preserves_whole_haplotypes(self):
        draws = np.array([[0.25] * 4, [0.75] * 4])
        with patch("genetic_linkage.np.random.random", return_value=draws):
            result = cross2(self.L1, self.L2, np.zeros(3), 1)
        np.testing.assert_array_equal(result[0], [self.L1[1], self.L2[0]])

    def test_default_path_does_not_print(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cross2(self.L1, self.L2, self.RF, 3)
        self.assertEqual(output.getvalue(), "")

    def test_sequential_batches_preserve_seeded_result(self):
        with patch.object(experimental.mp, "cpu_count", return_value=2):
            for k in (0, 1, 5, 205):
                with self.subTest(k=k):
                    np.random.seed(11)
                    expected = cross2(self.L1, self.L2, self.RF, k)
                    np.random.seed(11)
                    with contextlib.redirect_stdout(io.StringIO()):
                        actual = experimental.cross2sp(self.L1, self.L2, self.RF, k)
                    np.testing.assert_array_equal(actual, expected)

    def test_multiprocessing_batches_with_spawn(self):
        spawn_pool = partial(mp.get_context("spawn").Pool, processes=2)
        with patch.object(experimental.mp, "cpu_count", return_value=2):
            with patch.object(experimental.mp, "Pool", side_effect=spawn_pool):
                for k in (0, 1, 5, 405):
                    with self.subTest(k=k):
                        with contextlib.redirect_stdout(io.StringIO()):
                            result = experimental.cross2mp(
                                self.L1, self.L2, self.RF, k
                            )
                        self.assertEqual(result.shape, (k, 2, 4))
                        self.assertEqual(result.dtype, np.int8)
                        for index, parent in enumerate((self.L1, self.L2)):
                            inherited = result[:, index, :]
                            self.assertTrue(np.all(
                                (inherited == parent[0]) | (inherited == parent[1])
                            ))


if __name__ == "__main__":
    unittest.main()

"""Read-only checks against the committed canonical run. Never writes into data/."""

import random
import unittest
from pathlib import Path

from distinguish import shortest_distinguishing
from pairs import find_run_dirs
from loader import load_batch
from tests.helpers import brute_force, run

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
CANONICAL = "2026-11-15_00-36-37-375402_UTC"
DUPLICATE = "2026-11-15_00-30-21-627385_UTC"
# From agentLogs/GPT_2026-11-14_18-44-44_existing-batch-runtime-benchmark.md
EXPECTED_EQUIVALENT = {(2, 10): 37, (2, 20): 0, (2, 30): 0, (3, 10): 0, (3, 20): 0, (3, 30): 0}


@unittest.skipUnless(find_run_dirs(CANONICAL, DATA_ROOT), "canonical run not present")
class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batches = {}
        for d in find_run_dirs(CANONICAL, DATA_ROOT):
            b = load_batch(d)
            cls.batches[(len(b.alphabet), b.n_states)] = b

    def test_all_six_load(self):
        self.assertEqual(set(self.batches), set(EXPECTED_EQUIVALENT))
        for b in self.batches.values():
            self.assertEqual(len(b.dfas), 500)

    def test_duplicate_run_identical(self):
        dup = {}
        for d in find_run_dirs(DUPLICATE, DATA_ROOT):
            b = load_batch(d)
            dup[(len(b.alphabet), b.n_states)] = b
        self.assertEqual(set(dup), set(self.batches))
        for key, b in self.batches.items():
            self.assertEqual(dup[key].dfas, b.dfas)

    def test_equivalent_counts_and_brute_force(self):
        rng = random.Random(2026)
        for key, b in sorted(self.batches.items()):
            k = len(b.alphabet)
            dfas = b.dfas
            n_eq, max_len = 0, 0
            for i in range(len(dfas)):
                for j in range(i + 1, len(dfas)):
                    L = shortest_distinguishing(dfas[i], dfas[j], k).length
                    if L is None:
                        n_eq += 1
                    else:
                        max_len = max(max_len, L)
            with self.subTest(batch=key):
                self.assertEqual(n_eq, EXPECTED_EQUIVALENT[key])
            # Oracle on sampled pairs, bounded by largest observed length + 1.
            for _ in range(100):
                i, j = rng.sample(range(len(dfas)), 2)
                r = shortest_distinguishing(dfas[i], dfas[j], k)
                oracle = brute_force(dfas[i], dfas[j], k, max_len + 1)
                self.assertEqual(r.witness, oracle)
                if oracle is not None:
                    self.assertNotEqual(run(dfas[i], oracle), run(dfas[j], oracle))


if __name__ == "__main__":
    unittest.main()

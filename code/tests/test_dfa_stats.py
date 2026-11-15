import random
import unittest

from dfa_stats import minimal_size, reachable_states
from distinguish import shortest_distinguishing_from
from tests.helpers import make_dfa, random_dfa


def classes_by_bfs(d, k):
    reach = sorted(reachable_states(d))
    reps = []
    for p in reach:
        if not any(shortest_distinguishing_from(d, p, d, r, k).length is None for r in reps):
            reps.append(p)
    return len(reps)


class HandMade(unittest.TestCase):
    def test_unreachable(self):
        d = make_dfa([[1], [0], [2], [0]], [True, False, True, False])
        self.assertEqual(reachable_states(d), frozenset({0, 1}))
        self.assertEqual(minimal_size(d, 1), 2)

    def test_merged_equivalent(self):
        # States 0 and 2 equivalent, 1 and 3 equivalent: "even number of 1s".
        d = make_dfa([[2, 1], [3, 0], [0, 3], [1, 2]], [True, False, True, False])
        self.assertEqual(len(reachable_states(d)), 4)
        self.assertEqual(minimal_size(d, 2), 2)

    def test_uniform_acceptance(self):
        d = make_dfa([[1, 2], [2, 0], [0, 1], [3, 3]], [True, True, True, False])
        self.assertEqual(minimal_size(d, 2), 1)

    def test_sink_counts(self):
        # Accept exactly the word "0": needs initial, accept, and dead sink.
        d = make_dfa([[1, 2], [2, 2], [2, 2]], [False, True, False])
        self.assertEqual(minimal_size(d, 2), 3)


class CrossCheck(unittest.TestCase):
    def test_random(self):
        rng = random.Random(7)
        for _ in range(2000):
            k = rng.randint(1, 3)
            d = random_dfa(rng, rng.randint(1, 7), k)
            self.assertEqual(minimal_size(d, k), classes_by_bfs(d, k))


if __name__ == "__main__":
    unittest.main()

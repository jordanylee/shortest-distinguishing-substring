import random
import unittest

from distinguish import shortest_distinguishing, shortest_distinguishing_from
from loader import AlphabetMismatchError
from tests.helpers import brute_force, make_dfa, random_dfa, run


def mod_counter(n, accept_at=0, k=1):
    """Accepts words whose length is congruent to accept_at mod n (all symbols advance)."""
    return make_dfa([[(p + 1) % n] * k for p in range(n)], [p == accept_at for p in range(n)])


class HandMade(unittest.TestCase):
    def test_identical(self):
        d = mod_counter(3)
        self.assertEqual(shortest_distinguishing(d, d, 1).length, None)
        self.assertEqual(shortest_distinguishing(d, d, 1).witness, None)

    def test_empty_string(self):
        a = make_dfa([[0]], [True])
        b = make_dfa([[0]], [False])
        r = shortest_distinguishing(a, b, 1)
        self.assertEqual((r.length, r.witness), (0, ()))

    def test_equivalent_padded(self):
        # Minimal "even number of 1s" DFA vs. a 5-state copy with duplicated and unreachable states.
        minimal = make_dfa([[0, 1], [1, 0]], [True, False])
        padded = make_dfa([[2, 1], [3, 0], [0, 3], [1, 2], [4, 4]], [True, False, True, False, False])
        self.assertIsNone(shortest_distinguishing(minimal, padded, 2).length)
        self.assertIsNone(shortest_distinguishing(padded, minimal, 2).length)

    def test_long_witness_mod(self):
        # length = 0 mod 3 vs length = 0 mod 4 first disagree at length 3.
        r = shortest_distinguishing(mod_counter(3), mod_counter(4), 1)
        self.assertEqual(r.length, 3)
        # length = 5 mod 6 vs 5 mod 7: both accept at 5, first disagree at 11.
        a, b = mod_counter(6, accept_at=5), mod_counter(7, accept_at=5)
        self.assertEqual(shortest_distinguishing(a, b, 1).length, 11)

    def test_lexicographic_witness(self):
        # Both 0 and 1 lead to a distinguishing state; witness must use symbol 0.
        a = make_dfa([[1, 1], [1, 1]], [False, True])
        b = make_dfa([[0, 0]], [False])
        self.assertEqual(shortest_distinguishing(a, b, 2).witness, (0,))

    def test_multichar_symbol(self):
        k = 11
        a = make_dfa([[0] * 10 + [1], [1] * k], [False, True])
        b = make_dfa([[0] * k], [False])
        r = shortest_distinguishing(a, b, k)
        alphabet = [str(i) for i in range(k)]
        self.assertEqual([alphabet[s] for s in r.witness], ["10"])

    def test_wrong_width(self):
        a = make_dfa([[0, 0]], [True])
        b = make_dfa([[0]], [True])
        with self.assertRaises(AlphabetMismatchError):
            shortest_distinguishing(a, b, 2)
        with self.assertRaises(AlphabetMismatchError):
            shortest_distinguishing(a, a, 3)

    def test_start_state_range(self):
        a = make_dfa([[0], [1]], [True, False])
        b = make_dfa([[0], [1], [2]], [True, False, False])
        for p0, q0 in ((0, 3), (0, -1), (2, 0), (-1, 0)):
            with self.assertRaises(ValueError):
                shortest_distinguishing_from(a, p0, b, q0, 1)
        bad = make_dfa([[0], [1]], [True])
        with self.assertRaises(ValueError):
            shortest_distinguishing(bad, a, 1)

    def test_check_false_matches(self):
        rng = random.Random(7)
        for _ in range(200):
            a, b = random_dfa(rng, 4, 2), random_dfa(rng, 5, 2)
            self.assertEqual(shortest_distinguishing(a, b, 2),
                             shortest_distinguishing(a, b, 2, check=False))


class BruteForce(unittest.TestCase):
    def test_random_small_pairs(self):
        rng = random.Random(12345)
        n_equiv = 0
        for _ in range(5000):
            k = rng.randint(1, 3)
            a = random_dfa(rng, rng.randint(1, 4), k)
            b = random_dfa(rng, rng.randint(1, 4), k)
            r = shortest_distinguishing(a, b, k)
            # Non-equivalent DFAs with n1, n2 states disagree on some word of length
            # <= n1 + n2 - 2 (Moore), so n1 + n2 is a sufficient, cheaper bound than n1 * n2.
            bound = len(a.delta) + len(b.delta)
            oracle = brute_force(a, b, k, bound)
            if oracle is None:
                n_equiv += 1
                self.assertEqual((r.length, r.witness), (None, None))
            else:
                self.assertEqual(r.witness, oracle)
                self.assertEqual(r.length, len(oracle))
                self.assertNotEqual(run(a, r.witness), run(b, r.witness))
            r2 = shortest_distinguishing(b, a, k)
            self.assertEqual((r2.length, r2.witness), (r.length, r.witness))
        # Sanity: both outcomes occur.
        self.assertGreater(n_equiv, 0)
        self.assertLess(n_equiv, 5000)


if __name__ == "__main__":
    unittest.main()

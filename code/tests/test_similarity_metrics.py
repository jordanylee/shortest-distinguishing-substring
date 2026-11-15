"""Independent exhaustive oracle for the distribution in similarity-metrics.md."""

import itertools
import random
import unittest
from fractions import Fraction

from loader import AlphabetMismatchError, DFA
from similarity_metrics import METRIC_FIELDS, calculate_similarity
from tests.helpers import make_dfa, random_dfa, run


def enumerate_metrics(a, b, k, horizon):
    weights = dict.fromkeys(("weight_a", "weight_b", "weight_intersection",
                             "weight_union", "weight_symmetric_difference"), Fraction(0))
    for length in range(horizon + 1):
        word_weight = Fraction(1, (horizon + 1) * k ** length)
        for word in itertools.product(range(k), repeat=length):
            fa, fb = run(a, word), run(b, word)
            events = (fa, fb, fa and fb, fa or fb, fa != fb)
            for key, event in zip(weights, events):
                weights[key] += word_weight * event
    weights["probability_of_agreement"] = 1 - weights["weight_symmetric_difference"]
    weights["weighted_jaccard"] = (weights["weight_intersection"] / weights["weight_union"]
                                    if weights["weight_union"] else Fraction(1))
    return weights


class SimilarityTests(unittest.TestCase):
    def setUp(self):
        self.empty = make_dfa([[0, 0]], [False])
        self.universal = make_dfa([[0, 0]], [True])
        self.part = make_dfa([[0, 1], [0, 1]], [False, True])

    def assert_oracle(self, a, b, k, horizon):
        symbols = [str(i) for i in range(k)]
        actual = calculate_similarity(a, b, symbols, horizon)
        expected = enumerate_metrics(a, b, k, horizon)
        for key in METRIC_FIELDS:
            self.assertEqual(actual[key], expected[key], key)
            self.assertLessEqual(0, actual[key])
            self.assertLessEqual(actual[key], 1)
        self.assertEqual(actual["weight_union"], actual["weight_a"] + actual["weight_b"] - actual["weight_intersection"])
        self.assertEqual(actual["weight_symmetric_difference"], actual["weight_a"] + actual["weight_b"] - 2 * actual["weight_intersection"])
        reverse = calculate_similarity(b, a, symbols, horizon)
        for key in ("probability_of_agreement", "weighted_jaccard", "weight_intersection",
                    "weight_union", "weight_symmetric_difference"):
            self.assertEqual(actual[key], reverse[key])
        self.assertEqual(actual["weight_a"], reverse["weight_b"])
        return actual

    def test_constant_and_partial_languages(self):
        for a, b in ((self.empty, self.empty), (self.empty, self.universal),
                     (self.empty, self.part), (self.part, self.part)):
            for horizon in (0, 1, 4):
                self.assert_oracle(a, b, 2, horizon)
        result = calculate_similarity(self.empty, self.empty, ["0", "1"], 4)
        self.assertEqual(result["weighted_jaccard"], 1)
        self.assertEqual(result["weight_union"], 0)

    def test_complement_and_equivalent_structure(self):
        complement = make_dfa(self.part.delta, [True, False])
        result = self.assert_oracle(self.part, complement, 2, 4)
        self.assertEqual(result["probability_of_agreement"], 0)
        self.assertEqual(result["weighted_jaccard"], 0)
        padded = make_dfa([[0, 0], [1, 1]], [False, True])
        result = self.assert_oracle(self.empty, padded, 2, 5)
        self.assertEqual(result["probability_of_agreement"], 1)

    def test_beyond_horizon_and_epsilon(self):
        delayed = make_dfa([[1], [2], [2]], [False, False, True])
        empty = make_dfa([[0]], [False])
        for horizon in (0, 1, 2, 4):
            result = self.assert_oracle(delayed, empty, 1, horizon)
            if horizon < 2:
                self.assertEqual(result["weighted_jaccard"], 1)
                self.assertEqual(result["probability_of_agreement"], 1)
        result = calculate_similarity(self.empty, self.universal, ["0", "1"], 0)
        self.assertEqual(result["weight_symmetric_difference"], 1)

    def test_token_labels_and_column_alignment(self):
        reordered = make_dfa([[1, 0], [1, 0]], [False, True])
        result = calculate_similarity(self.part, reordered, ["0", "10"], 5,
                                      alphabet_b=["10", "0"])
        self.assertEqual(result["weighted_jaccard"], 1)
        self.assertEqual(result["probability_of_agreement"], 1)
        same_destinations = make_dfa([[1, 1], [0, 0]], [False, True])
        self.assert_oracle(same_destinations, self.part, 2, 5)

    def test_seeded_random_oracle(self):
        rng = random.Random(20261115)
        for _ in range(150):
            k = rng.randint(1, 3)
            a, b = (random_dfa(rng, rng.randint(1, 4), k) for _ in range(2))
            self.assert_oracle(a, b, k, rng.randint(0, 5))

    def test_validation(self):
        for horizon in (None, -1, 1.5, True, "3"):
            with self.assertRaises(ValueError):
                calculate_similarity(self.empty, self.part, ["0", "1"], horizon)
        for symbols in ([], ["0", "0"], [0, 1]):
            with self.assertRaises(ValueError):
                calculate_similarity(self.empty, self.part, symbols, 1)
        with self.assertRaises(AlphabetMismatchError):
            calculate_similarity(self.empty, self.part, ["0", "1"], 1, alphabet_b=["a", "b"])
        with self.assertRaises(AlphabetMismatchError):
            calculate_similarity(self.empty, self.part, ["0"], 1)
        for bad in (DFA(0, ((2, 0),), (False,), 0), DFA(0, ((0, 0),), (), 0),
                    DFA(0, ((0, 0),), (False,), -1)):
            with self.assertRaises(ValueError):
                calculate_similarity(bad, self.empty, ["0", "1"], 1)

"""Cross-batch identity, complete Cartesian products, and isolated output checks."""

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cross_state
from distinguish import shortest_distinguishing
from loader import AlphabetMismatchError, load_batch
from result_summary import markdown_summary, read_jsonl, summarize
from similarity_metrics import METRIC_FIELDS, calculate_similarity
from tests.helpers import make_dfa, random_dfa, write_synthetic_batch


class CrossStateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.batches = {}
        for k in (2, 3):
            for n, count in ((10, 2), (15, 1), (20, 3), (25, 1), (30, 2)):
                path = write_synthetic_batch(
                    self.root / f"alphabet_{k}" / f"states_{n}" / "source",
                    [random_dfa(random.Random(n * 100 + i), n, k, id=i) for i in reversed(range(count))],
                    [str(i) for i in range(k)], run_id="source")
                self.batches[k, n] = load_batch(path)

    def test_preview_benchmark_exclude_15_25_and_write_nothing(self):
        before = sorted(self.root.rglob("*"))
        rows = cross_state.preview("source", self.root)
        self.assertEqual(len(rows), 6)
        self.assertEqual([r["pair_count"] for r in rows], [6, 4, 6] * 2)
        self.assertEqual({(r["state_count_a"], r["state_count_b"]) for r in rows},
                         {(10, 20), (10, 30), (20, 30)})
        timings = cross_state.benchmark("source", self.root, horizon=3, sample_pairs=100)
        self.assertEqual([r["sample_pairs"] for r in timings], [6, 4, 6] * 2)
        self.assertEqual(before, sorted(self.root.rglob("*")))
        self.assertEqual(len(cross_state.preview("source", self.root, [3])), 3)

    def test_all_pairs_metrics_identity_and_saved_summary(self):
        for compress in (False, True):
            outs = cross_state.run_all("source", self.root, horizon=3, results_id=f"run-{compress}",
                                       compress=compress)
            self.assertEqual(len(outs), 6)
            for out in outs:
                m = json.loads((out / "manifest.json").read_text())
                k = m["alphabet_size"]
                a, b = (self.batches[k, n] for n in m["state_counts"])
                rows = list(read_jsonl(out / m["pairs_file"]))
                expected_keys = {(x.id, y.id) for x in a.dfas for y in b.dfas}
                self.assertEqual({(r["a"], r["b"]) for r in rows}, expected_keys)
                self.assertEqual(len(rows), len(expected_keys))
                # Equal IDs across state batches are included; a > b is allowed.
                self.assertTrue(any(r["a"] == r["b"] for r in rows))
                self.assertTrue(any(r["a"] > r["b"] for r in rows))
                by_a, by_b = ({d.id: d for d in batch.dfas} for batch in (a, b))
                for row in rows:
                    left, right = by_a[row["a"]], by_b[row["b"]]
                    sds = shortest_distinguishing(left, right, k)
                    self.assertEqual(row["length"], sds.length)
                    self.assertEqual(row["witness"], None if sds.witness is None else
                                     [a.alphabet[s] for s in sds.witness])
                    scores = calculate_similarity(left, right, a.alphabet, 3)
                    for field in METRIC_FIELDS:
                        self.assertEqual(row[field], float(scores[field]))
                    self.assertEqual([row["state_count_a"], row["state_count_b"]], m["state_counts"])
                stats = list(read_jsonl(out / m["dfa_stats_file"]))
                self.assertEqual(len({(r["state_count"], r["id"]) for r in stats}),
                                 len(a.dfas) + len(b.dfas))
                summary = summarize(out)
                self.assertIn(f"states {a.n_states} vs {b.n_states}", markdown_summary(summary))
                self.assertEqual(sum(summary["length_histogram"].values()) +
                                 summary["equivalent_pair_count"], len(rows))
                self.assertEqual(m["sources"][0]["sha256"], a.input_sha256)

    def test_failure_cleanup_and_preflight_no_overwrite(self):
        with mock.patch.object(cross_state, "_pair_record", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                cross_state.run_all("source", self.root, horizon=2, results_id="retry")
        self.assertFalse(list(self.root.rglob("*.part")))
        cross_state.run_all("source", self.root, horizon=2, alphabet_sizes=[3], results_id="retry")
        with self.assertRaises(FileExistsError):
            cross_state.run_all("source", self.root, horizon=2, results_id="retry")
        # A later alphabet's conflict is detected before any alphabet-2 computation.
        self.assertFalse((self.root / "alphabet_2/cross_state/source/retry/states_10_vs_20").exists())

    def test_missing_batches_and_mismatched_alphabets_rejected(self):
        with self.assertRaises(FileNotFoundError):
            cross_state.preview("source", self.root, [4])
        selected = [self.batches[2, n].run_dir for n in (10, 20)]
        with mock.patch.object(cross_state, "select_batches", return_value=selected):
            with self.assertRaisesRegex(FileNotFoundError, "missing state counts.*30"):
                cross_state.run_all("source", self.root, horizon=2, results_id="missing")
        path = self.batches[2, 30].run_dir / "manifest.json"
        m = json.loads(path.read_text())
        m["alphabet"] = ["1", "0"]
        path.write_text(json.dumps(m))
        with self.assertRaises(AlphabetMismatchError):
            cross_state.run_all("source", self.root, horizon=2, results_id="bad")
        self.assertFalse(list(self.root.rglob("cross_state")))
        path.unlink()
        with self.assertRaises(ValueError):
            cross_state.preview("source", self.root, [2])

    def test_equivalence_is_separate_from_empty_string_distinctions(self):
        # Two constant-language DFAs per batch give two equivalent and two L=0
        # pairs per combination, even though the raw state counts differ.
        for n in (10, 20, 30):
            dfas = [make_dfa([[0, 0]] * n, [accept] * n, id=i)
                    for i, accept in enumerate((False, True))]
            write_synthetic_batch(self.batches[2, n].run_dir, dfas, ["0", "1"], run_id="source")
        outputs = cross_state.run_all("source", self.root, horizon=0, alphabet_sizes=[2])
        for out in outputs:
            summary = summarize(out)
            self.assertEqual(summary["equivalent_pair_count"], 2)
            self.assertEqual(summary["length_histogram"], {0: 2})
            self.assertEqual(summary["finite_length_distribution"], {0: 1.0})
            self.assertEqual(summary["positive_length_distribution"], {})
            self.assertEqual(summary["mean_similarity"]["probability_of_agreement"], 0.5)
            self.assertEqual(summary["mean_similarity"]["weighted_jaccard"], 0.5)

    def test_config_validation(self):
        for horizon in (None, -1, True):
            with self.assertRaises(ValueError):
                cross_state.run_all("source", self.root, horizon=horizon)
        with self.assertRaises(ValueError):
            cross_state.run_all("source", self.root, horizon=3, results_id="../escape")
        with self.assertRaises(ValueError):
            cross_state.benchmark("source", self.root, horizon=3, sample_pairs=0)
        with self.assertRaises(ValueError):
            cross_state.preview("../source", self.root)

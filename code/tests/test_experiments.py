import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import experiments
import pairs
from distinguish import shortest_distinguishing
from loader import load_batch
from result_summary import markdown_summary, read_jsonl, summarize
from similarity_metrics import METRIC_FIELDS, calculate_similarity
from tests.helpers import make_dfa, random_dfa, write_synthetic_batch


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        rng = random.Random(13)
        dfas = [random_dfa(rng, 3, 2, id=i) for i in range(5)]
        dfas.append(make_dfa(dfas[0].delta, dfas[0].accept, id=5))
        # Deliberately reverse input order to check marginal weights belong to sorted IDs.
        self.path = write_synthetic_batch(self.root / "alphabet_2" / "states_3" / "R1",
                                         list(reversed(dfas)), ["0", "1"], run_id="R1")

    def test_all_modes_and_compression(self):
        batch = load_batch(self.path)
        by_id = {d.id: d for d in batch.dfas}
        for mode in ("sds", "similarity", "both"):
            for compress in (False, True):
                out = experiments.run_batch(self.path, calculations=mode, horizon=3,
                                            results_id=f"{mode}-{compress}", compress=compress)
                m = json.loads((out / "manifest.json").read_text())
                rows = list(read_jsonl(out / m["pairs_file"]))
                self.assertEqual(len(rows), 15)
                self.assertEqual(len({(r['a'], r['b']) for r in rows}), 15)
                self.assertEqual(len(list(read_jsonl(out / m["dfa_stats_file"]))), 6)
                for row in rows:
                    self.assertLess(row["a"], row["b"])
                    a, b = by_id[row["a"]], by_id[row["b"]]
                    self.assertEqual("length" in row, mode != "similarity")
                    self.assertEqual("weighted_jaccard" in row, mode != "sds")
                    if mode != "similarity":
                        expected = shortest_distinguishing(a, b, 2)
                        self.assertEqual(row["length"], expected.length)
                        self.assertEqual(row["witness"], None if expected.witness is None else
                                         [batch.alphabet[s] for s in expected.witness])
                    if mode != "sds":
                        expected = calculate_similarity(a, b, batch.alphabet, 3)
                        for field in METRIC_FIELDS:
                            self.assertEqual(row[field], float(expected[field]))
                        self.assertEqual(m["distribution"]["horizon"], 3)
                summary = summarize(out)
                self.assertEqual(summary["pair_count"], 15)
                self.assertIn("states 3", markdown_summary(summary))
                if mode != "similarity":
                    self.assertGreaterEqual(summary["equivalent_pair_count"], 1)
                    self.assertEqual(sum(summary["length_histogram"].values()) + summary["equivalent_pair_count"], 15)

    def test_legacy_summary_and_sds_parity(self):
        old = pairs.run_batch(self.path, "legacy")
        new = experiments.run_batch(self.path, calculations="sds", results_id="new")
        self.assertEqual(list(read_jsonl(old / "pairs.jsonl.gz")), list(read_jsonl(new / "pairs.jsonl.gz")))
        self.assertEqual(summarize(old)["length_histogram"], summarize(new)["length_histogram"])

    def test_no_overwrite_failure_cleanup_and_horizon(self):
        with self.assertRaises(ValueError):
            experiments.run_batch(self.path)
        with mock.patch.object(experiments, "_pair_record", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                experiments.run_batch(self.path, horizon=2, results_id="retry")
        self.assertFalse((self.path / "comparisons" / "retry.part").exists())
        out = experiments.run_batch(self.path, horizon=2, results_id="retry")
        before = (out / "pairs.jsonl.gz").read_bytes()
        with self.assertRaises(FileExistsError):
            experiments.run_batch(self.path, horizon=4, results_id="retry")
        self.assertEqual(before, (out / "pairs.jsonl.gz").read_bytes())
        with self.assertRaises(ValueError):
            experiments.run_batch(self.path, calculations="bad")
        with self.assertRaises(ValueError):
            experiments.run_batch(self.path, calculations="sds", results_id="../escape")

    def test_selection_preview_benchmark_and_shared_id(self):
        second = write_synthetic_batch(self.root / "alphabet_3" / "states_2" / "R1",
                                       [random_dfa(random.Random(i), 2, 3, id=i) for i in range(3)],
                                       ["0", "1", "2"], run_id="R1")
        preview = experiments.preview("R1", self.root)
        self.assertEqual(sum(row["pair_count"] for row in preview), 18)
        before = sorted(str(p) for p in self.root.rglob("*"))
        timings = experiments.benchmark("R1", self.root, horizon=3, sample_pairs=2)
        self.assertEqual([t["sample_pairs"] for t in timings], [2, 2])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))
        outs = experiments.run_all("R1", self.root, calculations="sds", results_id="shared")
        self.assertEqual(outs, [self.path / "comparisons/shared", second / "comparisons/shared"])
        self.assertEqual(len(experiments.preview("R1", self.root, alphabet_sizes=[3])), 1)
        with self.assertRaises(FileNotFoundError):
            experiments.preview("missing", self.root)
        with self.assertRaises(ValueError):
            experiments.preview("../R1", self.root)

    def test_summary_rejects_incomplete_and_wrong_count(self):
        out = experiments.run_batch(self.path, calculations="sds", results_id="summary")
        path = out / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["pair_count"] += 1
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            summarize(out)
        manifest["status"] = "partial"
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            summarize(out)

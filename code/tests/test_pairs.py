import gzip
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pairs
from distinguish import shortest_distinguishing
from tests.helpers import make_dfa, random_dfa, write_synthetic_batch


def read_jsonl(path):
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt") as f:
        return [json.loads(line) for line in f]


class PairsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        rng = random.Random(3)
        dfas = [random_dfa(rng, 4, 2, id=i) for i in range(9)]
        dfas.append(make_dfa(dfas[0].delta, dfas[0].accept, id=9))  # guarantee an equivalent pair
        self.dfas = dfas
        self.alphabet = ["0", "1"]
        self.run_dir = write_synthetic_batch(self.tmp / "data" / "alphabet_2" / "states_4" / "R1",
                                             dfas, self.alphabet)

    def tearDown(self):
        self._tmp.cleanup()

    def test_end_to_end(self):
        for compress in (True, False):
            out = pairs.run_batch(self.run_dir, f"res-{compress}", compress=compress)
            m = json.loads((out / "manifest.json").read_text())
            rows = read_jsonl(out / m["pairs_file"])
            n = len(self.dfas)
            self.assertEqual(len(rows), n * (n - 1) // 2)
            self.assertEqual(m["pair_count"], len(rows))
            self.assertEqual(m["expected_pair_count"], len(rows))
            self.assertEqual(m["status"], "complete")
            by_id = {d.id: d for d in self.dfas}
            keys = set()
            for row in rows:
                self.assertLess(row["a"], row["b"])
                keys.add((row["a"], row["b"]))
                r = shortest_distinguishing(by_id[row["a"]], by_id[row["b"]], 2)
                self.assertEqual(row["length"], r.length)
                exp = None if r.witness is None else [self.alphabet[s] for s in r.witness]
                self.assertEqual(row["witness"], exp)
            self.assertEqual(len(keys), len(rows))
            n_eq = sum(row["length"] is None for row in rows)
            self.assertGreaterEqual(n_eq, 1)
            self.assertEqual(m["equivalent_pair_count"], n_eq)
            self.assertEqual(m["length_zero_pair_count"], sum(row["length"] == 0 for row in rows))
            self.assertEqual(m["max_finite_length"],
                             max(row["length"] for row in rows if row["length"] is not None))
            self.assertEqual(sum(m["length_histogram"].values()) + n_eq, len(rows))
            stats = read_jsonl(out / m["dfa_stats_file"])
            self.assertEqual([s["id"] for s in stats], [d.id for d in self.dfas])
            self.assertFalse((out.parent / f"{out.name}.part").exists())

    def test_no_overwrite(self):
        out = pairs.run_batch(self.run_dir, "fixed")
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with self.assertLogs("pairs", level="ERROR"), self.assertRaises(FileExistsError):
            pairs.run_batch(self.run_dir, "fixed")
        self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)

    def test_run_all(self):
        other = write_synthetic_batch(self.tmp / "data" / "alphabet_3" / "states_2" / "R1",
                                      [random_dfa(random.Random(i), 2, 3, id=i) for i in range(4)],
                                      ["0", "1", "2"])
        outs = pairs.run_all("R1", self.tmp / "data", results_id="shared")
        self.assertEqual(outs, [self.run_dir / "pairs" / "shared", other / "pairs" / "shared"])
        outs = pairs.run_all("R1", self.tmp / "data", results_id="only3", alphabet_sizes=[3])
        self.assertEqual(outs, [other / "pairs" / "only3"])

    def test_failure_removes_part_dir(self):
        calls = {"n": 0}
        real = pairs.shortest_distinguishing

        def flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 5:
                raise RuntimeError("boom")
            return real(*args, **kwargs)

        with mock.patch.object(pairs, "shortest_distinguishing", flaky), \
                self.assertRaises(RuntimeError):
            pairs.run_batch(self.run_dir, "crash")
        self.assertFalse((self.run_dir / "pairs" / "crash.part").exists())
        self.assertFalse((self.run_dir / "pairs" / "crash").exists())
        out = pairs.run_batch(self.run_dir, "crash")  # same id works after the failure
        self.assertTrue((out / "manifest.json").is_file())

    def test_find_run_dirs_skips_bad_names(self):
        for name in ("alphabet_x/states_4", "alphabet_2_old/states_4", "alphabet_2/states_4b"):
            (self.tmp / "data" / name / "R1").mkdir(parents=True)
        with self.assertLogs("pairs", level="WARNING"):
            found = pairs.find_run_dirs("R1", self.tmp / "data")
        self.assertEqual(found, [self.run_dir])


if __name__ == "__main__":
    unittest.main()

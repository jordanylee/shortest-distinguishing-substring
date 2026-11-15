import json
import random
import tempfile
import unittest
from pathlib import Path

from loader import AlphabetMismatchError, BatchFormatError, load_batch
from tests.helpers import random_dfa, write_raw_batch, write_synthetic_batch


def good_record(id=0, n=2, k=2):
    return {"id": id, "seed": "1", "initial_state": 0,
            "transitions": [[0] * k for _ in range(n)], "acceptance": [True] * n}


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _dfas(self, count=5, n=4, k=3):
        rng = random.Random(1)
        return [random_dfa(rng, n, k, id=i) for i in range(count)]

    def test_round_trip(self):
        for compress in (False, True):
            dfas = self._dfas()
            d = write_synthetic_batch(self.tmp / f"r{compress}", dfas, ["0", "1", "2"], compress=compress)
            b = load_batch(d)
            self.assertEqual(b.dfas, tuple(dfas))
            self.assertEqual(b.alphabet, ("0", "1", "2"))
            self.assertEqual(b.n_states, 4)
            self.assertEqual(set(b.input_sha256), {"manifest.json", b.manifest["batch_file"]})

    def test_no_compression_field(self):
        d = write_synthetic_batch(self.tmp / "old", self._dfas(), ["0", "1", "2"], compress=True,
                                  drop_manifest_fields=("compression",))
        self.assertEqual(len(load_batch(d).dfas), 5)

    def test_bad_status(self):
        d = write_synthetic_batch(self.tmp / "a", self._dfas(), ["0", "1", "2"],
                                  manifest_overrides={"status": "running"})
        with self.assertRaises(BatchFormatError):
            load_batch(d)
        d = write_synthetic_batch(self.tmp / "b", self._dfas(), ["0", "1", "2"],
                                  drop_manifest_fields=("status",))
        with self.assertRaises(BatchFormatError):
            load_batch(d)

    def test_bad_schema(self):
        d = write_synthetic_batch(self.tmp / "a", self._dfas(), ["0", "1", "2"],
                                  manifest_overrides={"schema_version": 2})
        with self.assertRaises(BatchFormatError):
            load_batch(d)

    def test_wrong_sample_count(self):
        d = write_synthetic_batch(self.tmp / "a", self._dfas(), ["0", "1", "2"],
                                  manifest_overrides={"sample_count": 6})
        with self.assertRaises(BatchFormatError):
            load_batch(d)

    def test_alphabet_size_mismatch(self):
        d = write_synthetic_batch(self.tmp / "a", self._dfas(), ["0", "1", "2"],
                                  manifest_overrides={"alphabet_size": 4})
        with self.assertRaises(AlphabetMismatchError):
            load_batch(d)

    def _expect(self, exc, records, n=2, k=2, bad_id=None, **kw):
        d = write_raw_batch(self.tmp / f"x{random.random()}", records, [str(i) for i in range(k)], n, **kw)
        with self.assertLogs("loader", level="ERROR") as cm, self.assertRaises(exc):
            load_batch(d)
        if bad_id is not None:
            self.assertIn(f"id={bad_id}", cm.output[0])

    def test_record_checks(self):
        r = good_record(id=7)
        r["transitions"] = r["transitions"][:1]
        self._expect(BatchFormatError, [good_record(0), r], bad_id=7)

        r = good_record(id=8)
        r["acceptance"] = [True]
        self._expect(BatchFormatError, [r], bad_id=8)

        r = good_record(id=9)
        r["transitions"][1][0] = 2
        self._expect(BatchFormatError, [r], bad_id=9)

        r = good_record(id=10)
        r["transitions"][1][0] = 1.0
        self._expect(BatchFormatError, [r], bad_id=10)

        r = good_record(id=11)
        r["acceptance"][0] = 1
        self._expect(BatchFormatError, [r], bad_id=11)

        r = good_record(id=12)
        r["initial_state"] = 5
        self._expect(BatchFormatError, [r], bad_id=12)

        r = good_record(id=13)
        r["transitions"][0] = [0, 0, 0]
        self._expect(AlphabetMismatchError, [r], bad_id=13)

        self._expect(BatchFormatError, [good_record(3), good_record(3)], bad_id=3)

    def test_non_object_record(self):
        for rec in ([], 5, "x"):
            d = write_raw_batch(self.tmp / f"nonobj-{type(rec).__name__}", [rec], ["0", "1"], 2)
            with self.assertLogs("loader", level="ERROR"), self.assertRaises(BatchFormatError):
                load_batch(d)

    def test_valid_raw(self):
        d = write_raw_batch(self.tmp / "ok", [good_record(0), good_record(1)], ["0", "1"], 2)
        self.assertEqual(len(load_batch(d).dfas), 2)


if __name__ == "__main__":
    unittest.main()

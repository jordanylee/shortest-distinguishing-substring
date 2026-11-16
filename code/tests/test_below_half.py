"""Filter boundary, pair identity/parity, and isolated result storage."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments import below_half_accepting, run_batch
from result_summary import read_jsonl, summarize
from run_below_half import preview, run
from tests.helpers import make_dfa, write_synthetic_batch


class BelowHalfTests(unittest.TestCase):
    def test_strict_boundary_and_raw_unreachable_states(self):
        delta = [[0,0]]*4
        # Other states are unreachable; the filter deliberately counts all four.
        self.assertTrue(below_half_accepting(make_dfa(delta,[0,1,0,0])))
        self.assertFalse(below_half_accepting(make_dfa(delta,[0,1,1,0])))
        self.assertFalse(below_half_accepting(make_dfa(delta,[0,1,1,1])))
        self.assertTrue(below_half_accepting(make_dfa([[0,0]]*3,[0,1,0])))
        self.assertFalse(below_half_accepting(make_dfa([[0,0]]*3,[0,1,1])))

    def test_subset_matches_full_pair_results_and_preserves_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            delta = [[1,0],[2,1],[3,2],[0,3]]
            dfas = [make_dfa(delta,flags,id=i) for i,flags in
                    [(90,[0,0,0,0]),(7,[1,0,0,0]),(32,[0,1,0,0]),(18,[1,1,0,0]),(99,[1,1,1,0])]]
            path = write_synthetic_batch(root/'alphabet_2/states_4/R',dfas,['0','1'],run_id='R')
            rows = preview('R',root,(2,),(4,))
            self.assertEqual((rows[0]['selected_dfas'],rows[0]['pair_count'],rows[0]['exactly_half']),(3,3,1))
            full = run_batch(path,horizon=3,results_id='same')
            subset = run('R',root,horizon=3,results_id='same',alphabet_sizes=(2,),state_counts=(4,))[0]
            self.assertEqual(subset,path/'comparisons_below_half/same')
            expected = [r for r in read_jsonl(full/'pairs.jsonl.gz') if r['a'] in (7,32,90) and r['b'] in (7,32,90)]
            self.assertEqual(list(read_jsonl(subset/'pairs.jsonl.gz')),expected)
            m = json.loads((subset/'manifest.json').read_text())
            self.assertEqual(m['dfa_selection']['selected_ids'],[7,32,90])
            self.assertEqual(m['source_dfa_count'],5)
            self.assertEqual(m['dfa_count'],3)
            self.assertEqual(summarize(subset)['pair_count'],3)
            self.assertIn('run_below_half.py',m['code_sha256'])
            with self.assertRaises(FileExistsError):
                run('R',root,horizon=3,results_id='same',alphabet_sizes=(2,),state_counts=(4,))
            with self.assertRaises(FileNotFoundError):
                preview('R',root,(2,3),(4,))

    def test_empty_subset_writes_valid_zero_pair_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=write_synthetic_batch(Path(temporary)/'R',[make_dfa([[0,0],[1,1]],[1,0],id=5)],['0','1'],run_id='R')
            output=run_batch(path,horizon=2,results_id='empty',below_half_only=True)
            self.assertEqual(list(read_jsonl(output/'dfa_stats.jsonl.gz')),[])
            self.assertEqual(summarize(output)['pair_count'],0)

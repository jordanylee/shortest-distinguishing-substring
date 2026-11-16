"""SDS and similarity within the strictly <50% accepting subset, alphabets 2/3.

Preview: python code/run_below_half.py
Compute: python code/run_below_half.py --run --horizon 5
No DFAs are generated. Both endpoints must pass the filter. No cross-size pairs.
"""
import argparse
import logging
from pathlib import Path

from experiments import _results_id, below_half_accepting, run_batch, select_batches
from loader import load_batch
from similarity_metrics import validate_horizon

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = '2026-11-15_19-36-35-433280_UTC'


def preview(run_id=SOURCE_ID, data_root=ROOT/'data', alphabet_sizes=(2,3), state_counts=(10,15,20,25,30)):
    if not alphabet_sizes or any(a not in (2,3) for a in alphabet_sizes):
        raise ValueError('Only alphabets 2 and 3 are supported')
    if not state_counts or any(type(s) is not int or s < 1 for s in state_counts):
        raise ValueError('state_counts must contain positive integers')
    paths = select_batches(run_id, data_root, alphabet_sizes, state_counts)
    expected = {(a,s) for a in alphabet_sizes for s in state_counts}
    rows = []
    for path in paths:
        b = load_batch(path)
        selected = [d for d in b.dfas if below_half_accepting(d)]
        n = len(selected)
        rows.append(dict(run_dir=path, alphabet_size=len(b.alphabet), state_count=b.n_states,
                         source_dfas=len(b.dfas), selected_dfas=n, pair_count=n*(n-1)//2,
                         exactly_half=sum(2*sum(d.accept)==len(d.accept) for d in b.dfas)))
    if {(r['alphabet_size'],r['state_count']) for r in rows} != expected:
        raise FileNotFoundError('Some requested alphabet/state batches are missing')
    return rows


def run(run_id=SOURCE_ID, data_root=ROOT/'data', *, horizon, results_id=None,
        alphabet_sizes=(2,3), state_counts=(10,15,20,25,30)):
    validate_horizon(horizon)
    rows = preview(run_id,data_root,alphabet_sizes,state_counts)
    result_id = _results_id(results_id)
    # Preflight every destination before any calculations/write.
    for row in rows:
        for name in (result_id,result_id+'.part'):
            target = row['run_dir']/'comparisons_below_half'/name
            if target.exists():
                raise FileExistsError(f'refusing to overwrite {target}')
    outputs = []
    for row in rows:
        outputs.append(run_batch(row['run_dir'],calculations='both',horizon=horizon,
                                 results_id=result_id,compress=True,below_half_only=True))
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id',default=SOURCE_ID)
    parser.add_argument('--data-root',type=Path,default=ROOT/'data')
    parser.add_argument('--alphabets',type=int,nargs='+',choices=(2,3),default=[2,3])
    parser.add_argument('--states',type=int,nargs='+',default=[10,15,20,25,30])
    parser.add_argument('--horizon',type=int,help='Required with --run; use 5 to match current full-data similarities')
    parser.add_argument('--results-id',help='Optional new identifier, shared across batches')
    parser.add_argument('--run',action='store_true',help='Compute and save; without this flag, preview only')
    args=parser.parse_args()
    if args.run:
        if args.horizon is None:
            parser.error('--run requires an explicit --horizon')
        validate_horizon(args.horizon)
    rows=preview(args.source_id,args.data_root,args.alphabets,args.states)
    print('Alphabet | States | Source DFAs | <50% DFAs | Exactly 50% (excluded) | Subset pairs')
    for r in rows:
        print(f"{r['alphabet_size']:8} | {r['state_count']:6} | {r['source_dfas']:11} | {r['selected_dfas']:9} | {r['exactly_half']:22} | {r['pair_count']:12,}")
    print(f"Total pairs: {sum(r['pair_count'] for r in rows):,}")
    if args.run:
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
        for path in run(args.source_id,args.data_root,horizon=args.horizon,results_id=args.results_id,
                        alphabet_sizes=args.alphabets,state_counts=args.states):
            print(path)
    else:
        print('Preview only. Add --run --horizon 5 to compute with the current full-data horizon.')


if __name__=='__main__':
    main()

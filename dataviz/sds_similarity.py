"""Export four SVG figures with panels from saved comparisons.

Similarity is on x; mean finite SDS within each similarity bin is on y.
Run from the repository root: python dataviz/sds_similarity.py
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from state_distributions import ROOT, SOURCE_ID, RESULTS_ID, CONFIGURATIONS, COLOR_FAMILIES, STATE_SHADES

METRICS = {'probability_of_agreement': 'Agreement', 'weighted_jaccard': 'Weighted Jaccard'}


def load_bins(source_id, results_id, bin_count):
    """Stream each pair file once; retain exact counts and bin summaries only."""
    summaries, inputs, batches = {}, [], []
    horizon = None
    for alphabet, states in CONFIGURATIONS:
        source = ROOT / 'data' / f'alphabet_{alphabet}' / f'states_{states}' / source_id
        directory = source / 'comparisons' / results_id
        manifest_path = directory / 'manifest.json'
        m = json.loads(manifest_path.read_text(encoding='utf-8'))
        if (m['status'], m['source_run_id'], m['results_id'], m['alphabet_size'], m['state_count'], m['dfa_count'], m['calculations']) != ('complete', source_id, results_id, alphabet, states, 500, 'both'):
            raise ValueError(f'Unexpected results configuration: {manifest_path}')
        distribution = m['distribution']
        if distribution['name'] != 'uniform_length_uniform_symbols':
            raise ValueError('Expected uniform length/symbol distribution')
        if horizon is None:
            horizon = distribution['horizon']
        if distribution['horizon'] != horizon:
            raise ValueError('Cannot compare different horizons in a figure')
        # Verify source provenance without loading or regenerating any DFAs.
        for filename, expected in m['source_sha256'].items():
            path = source / filename
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                raise ValueError(f'Source hash mismatch: {path}')
            inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest})
        sm = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
        source_file = source / sm['batch_file']
        opener = gzip.open if source_file.suffix == '.gz' else open
        with opener(source_file, 'rt', encoding='utf-8') as stream:
            ids = {json.loads(line)['id'] for line in stream}
        if len(ids) != 500:
            raise ValueError('Expected 500 unique source DFA IDs')
        accum = {metric: [[0, 0., 0., math.inf, -math.inf] for _ in range(bin_count)] for metric in METRICS}
        pair_file = directory / m['pairs_file']
        opener = gzip.open if pair_file.suffix == '.gz' else open
        seen, hist, equivalent = set(), Counter(), 0
        with opener(pair_file, 'rt', encoding='utf-8') as stream:
            for line in stream:
                r = json.loads(line)
                key = r['a'], r['b']
                if key in seen or key[0] >= key[1] or not set(key) <= ids:
                    raise ValueError(f'Duplicate/invalid pair: {key}')
                seen.add(key)
                length = r['length']
                if length is None:
                    equivalent += 1
                else:
                    if not isinstance(length, int) or length < 0:
                        raise ValueError('Invalid SDS length')
                    hist[str(length)] += 1
                for metric in METRICS:
                    value = r[metric]
                    if not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError(f'Invalid {metric}')
                    if (length is None or length > horizon) and abs(value - 1) > 1e-12:
                        raise ValueError('Perfect bounded score constraint failed')
                    if length is not None:
                        index = min(int(value * bin_count), bin_count - 1)
                        entry = accum[metric][index]
                        entry[0] += 1
                        entry[1] += value
                        entry[2] += length
                        entry[3] = min(entry[3], length)
                        entry[4] = max(entry[4], length)
                if length is not None and r['probability_of_agreement'] + 1e-12 < min(length/(horizon+1), 1):
                    raise ValueError('Necessary SDS agreement bound failed')
        if len(seen) != 500*499//2 or len(seen) != m['pair_count'] or dict(hist) != m['length_histogram'] or equivalent != m['equivalent_pair_count']:
            raise ValueError(f'Counts differ from manifest: {directory}')
        for metric, entries in accum.items():
            summaries[alphabet, states, metric] = entries
        batches.append({'alphabet_size': alphabet, 'generated_states': states, 'pair_count': len(seen),
                        'finite_pairs': len(seen)-equivalent, 'equivalent_pairs': equivalent})
        for path in (manifest_path, pair_file):
            inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f'Loaded {alphabet} symbols, {states} states: {len(seen):,} pairs', flush=True)
    return summaries, inputs, batches, horizon


def run(source_id=SOURCE_ID, results_id=RESULTS_ID, output=None, bin_count=20):
    if not isinstance(bin_count, int) or bin_count < 1:
        raise ValueError('bin_count must be a positive integer')
    output = Path(output) if output is not None else ROOT / 'dataviz' / 'figures' / 'sds_vs_similarity'
    output.mkdir(parents=True, exist_ok=True)
    summaries, inputs, batches, horizon = load_bins(source_id, results_id, bin_count)
    rows = []
    for (alphabet, states, metric), entries in summaries.items():
        for i, (n, sx, sy, low, high) in enumerate(entries):
            rows.append(dict(metric=metric, alphabet_size=alphabet, generated_states=states,
                             bin_left=i/bin_count, bin_right=(i+1)/bin_count, pair_count=n,
                             mean_similarity=sx/n if n else '', mean_finite_sds=sy/n if n else '',
                             minimum_sds=low if n else '', maximum_sds=high if n else ''))
    with (output / 'sds_similarity_bins.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    max_y = max(e[2]/e[0] for entries in summaries.values() for e in entries if e[0])
    files = []
    for metric, display in METRICS.items():
        family = 'agreement' if metric == 'probability_of_agreement' else 'jaccard'
        for grouping in ('alphabets', 'states'):
            by_alphabet = grouping == 'alphabets'
            values = (2,3,4,5) if by_alphabet else (10,20,30)
            fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True) if by_alphabet else plt.subplots(1, 3, figsize=(16, 5.5), sharex=True, sharey=True)
            for value, ax in zip(values, axes.flat):
                configurations = [(value,s) for s in (10,15,20,25,30)] if by_alphabet else [(a,value) for a in (2,3,4,5)]
                for alphabet, states in configurations:
                    entries = summaries[alphabet, states, metric]
                    # Preserve empty bins as gaps instead of connecting across missing data.
                    x = [e[1]/e[0] if e[0] else (i+.5)/bin_count for i,e in enumerate(entries)]
                    y = [e[2]/e[0] if e[0] else float('nan') for e in entries]
                    color = plt.get_cmap(COLOR_FAMILIES[alphabet])(STATE_SHADES[states])
                    ax.plot(x, y, 'o-', color=color, markersize=3.5, linewidth=1.7,
                            label=f'{states} states' if by_alphabet else f'{alphabet} symbols')
                ax.set(title=f'{value} symbols' if by_alphabet else f'{value} generated states',
                       xlabel=display, xlim=(-.015,1.015), ylim=(-.05,max_y*1.08))
                ax.spines[['top','right']].set_visible(False)
                ax.grid(alpha=.2)
                ax.set_axisbelow(True)
                ax.legend(frameon=False, fontsize=9, title='Generated size' if by_alphabet else 'Alphabet size')
            fig.suptitle(f'SDS vs. {display.lower()} (H={horizon})', fontsize=17)
            fig.supylabel('Mean finite SDS length')
            fig.text(.5,.035,f'Means within similarity bins of width {1/bin_count:g}; empty bins break lines. Equivalent pairs excluded.',ha='center',fontsize=9)
            fig.text(.5,.008,'Pairs share DFAs; descriptive comparisons. Counts and SDS ranges are in sds_similarity_bins.csv.',ha='center',fontsize=9)
            fig.tight_layout(rect=(.015,.08,1,.95))
            name = f'sds_vs_{family}_by_{grouping}.svg'
            fig.savefig(output/name,facecolor='white')
            plt.close(fig)
            files.append(name)
    provenance = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_id=source_id,
                      results_id=results_id, horizon=horizon, bin_count=bin_count,
                      bins='[left,right), with score 1 included in the final bin; x is observed bin mean',
                      sds='Finite lengths including zero; equivalent pairs excluded',
                      aggregation='Separate configuration means; no pooling or subsampling',
                      batches=batches, inputs=inputs, figures=files, matplotlib=matplotlib.__version__,
                      script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'sds_similarity_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print(f'Saved {len(files)} SVG figures to {output}',flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id', default=SOURCE_ID)
    parser.add_argument('--results-id', default=RESULTS_ID)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bins', type=int, default=20)
    args = parser.parse_args()
    run(args.source_id, args.results_id, args.output, args.bins)

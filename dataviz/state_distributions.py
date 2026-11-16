"""Plot reachable and minimal state distributions for twenty DFA batches.

Run from the repository root: python dataviz/state_distributions.py
Reads saved per-DFA statistics; does not run experiments or read pair results.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = '2026-11-15_19-36-35-433280_UTC'
RESULTS_ID = '2026-11-15_19-55-50-157162_UTC'
CONFIGURATIONS = [(a, s) for a in (2, 3, 4, 5) for s in (10, 15, 20, 25, 30)]
COLOR_FAMILIES = {2: 'Blues', 3: 'Reds', 4: 'Greens', 5: 'Purples'}
STATE_SHADES = {10: .45, 15: .575, 20: .70, 25: .825, 30: .95}


def read_rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def load_distributions(source_id, results_id):
    distributions, inputs = {}, []
    for alphabet, generated in CONFIGURATIONS:
        source = ROOT / 'data' / f'alphabet_{alphabet}' / f'states_{generated}' / source_id
        source_manifest = source / 'manifest.json'
        sm = json.loads(source_manifest.read_text(encoding='utf-8'))
        result = source / 'comparisons' / results_id
        result_manifest = result / 'manifest.json'
        rm = json.loads(result_manifest.read_text(encoding='utf-8'))
        if (sm['status'], sm['alphabet_size'], sm['state_count'], sm['sample_count']) != ('complete', alphabet, generated, 500):
            raise ValueError(f'Unexpected source configuration: {source_manifest}')
        if (rm['status'], rm['source_run_id'], rm['results_id'], rm['alphabet_size'], rm['state_count'], rm['dfa_count']) != ('complete', source_id, results_id, alphabet, generated, 500):
            raise ValueError(f'Unexpected result configuration: {result_manifest}')
        source_file = source / sm['batch_file']
        stats_file = result / rm['dfa_stats_file']
        samples, stats = read_rows(source_file), read_rows(stats_file)
        sample_ids, stats_ids = [r['id'] for r in samples], [r['id'] for r in stats]
        if len(samples) != 500 or len(stats) != 500 or len(set(sample_ids)) != 500 or set(sample_ids) != set(stats_ids):
            raise ValueError(f'Expected 500 unique, matched DFAs: {result}')
        for row in stats:
            if row['n_states'] != generated or not 1 <= row['minimal'] <= row['reachable'] <= generated:
                raise ValueError(f'Invalid saved state counts: {row}')
        counts = {field: Counter(row[field] for row in stats) for field in ('reachable', 'minimal')}
        for field, histogram in counts.items():
            if {str(k): v for k, v in histogram.items()} != rm[field + '_histogram']:
                raise ValueError(f'{field} histogram differs from manifest: {result}')
        distributions[alphabet, generated] = counts
        for path in (source_manifest, source_file, result_manifest, stats_file):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if path.parent == source and path.name in rm['source_sha256'] and digest != rm['source_sha256'][path.name]:
                raise ValueError(f'Source hash differs from results manifest: {path}')
            inputs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': digest})
    return distributions, inputs


def run(source_id=SOURCE_ID, results_id=RESULTS_ID, output=None):
    output = Path(output) if output is not None else ROOT / 'dataviz' / 'figures'
    output.mkdir(parents=True, exist_ok=True)
    distributions, inputs = load_distributions(source_id, results_id)
    rows = []
    for field in ('reachable', 'minimal'):
        fig, ax = plt.subplots(figsize=(14, 8))
        for (alphabet, generated), counts in distributions.items():
            color = plt.get_cmap(COLOR_FAMILIES[alphabet])(STATE_SHADES[generated])
            x = list(range(1, generated + 1))
            percentages = [counts[field][n] / 500 * 100 for n in x]
            ax.plot(x, percentages, color=color, marker='o', markersize=3,
                    linewidth=1.7, label=f'{alphabet} symbols, {generated} states')
            rows.extend({'distribution': field, 'alphabet_size': alphabet, 'generated_states': generated,
                         'number_of_states': n, 'dfa_count': counts[field][n],
                         'percent_of_500': percent} for n, percent in zip(x, percentages))
        ax.set(title=f'Distribution of {field} states', xlabel='Number of states',
               ylabel='% of DFAs (out of 500)', xlim=(.5, 30.5), ylim=(0, 102))
        ax.set_yticks(range(0, 101, 10))
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.grid(axis='y', alpha=.2)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_axisbelow(True)
        ax.set_title(ax.get_title(), fontsize=17, pad=15)
        ax.set_xlabel(ax.get_xlabel(), fontsize=12)
        ax.set_ylabel(ax.get_ylabel(), fontsize=12)
        fig.legend(*ax.get_legend_handles_labels(), loc='lower center', bbox_to_anchor=(.5, .065),
                   ncol=4, frameon=False, fontsize=10,
                   title='Color = alphabet size; darker shade = more generated states', title_fontsize=11)
        definition = ('Reachable states can be visited from the starting state by some string.' if field == 'reachable' else
                      'Minimal states remain after removing unreachable states and merging states with identical future acceptance behavior.')
        fig.text(.5, .025, definition, ha='center', fontsize=10)
        fig.subplots_adjust(left=.075, right=.98, top=.90, bottom=.34)
        fig.savefig(output / f'{field}_states.svg', facecolor='white')
        plt.close(fig)
    with (output / 'state_distributions.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance = {'created_utc': datetime.now(timezone.utc).isoformat(), 'source_id': source_id,
                  'results_id': results_id, 'dfa_count_per_configuration': 500,
                  'configuration_count': len(distributions), 'total_dfas': 500 * len(distributions),
                  'normalization': '100 * count at this state count / 500; no pooling across configurations',
                  'line_domain': 'Integer state counts from 1 to the configuration generated state count; zero-frequency counts included',
                  'color_families': COLOR_FAMILIES, 'state_shades': STATE_SHADES,
                  'inputs': inputs, 'matplotlib': matplotlib.__version__,
                  'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(f'Saved two figures for {len(distributions)} configurations (10,000 DFAs) to {output}')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id', default=SOURCE_ID)
    parser.add_argument('--results-id', default=RESULTS_ID)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.source_id, args.results_id, args.output)

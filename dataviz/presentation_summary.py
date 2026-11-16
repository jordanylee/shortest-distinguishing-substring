"""Validate saved experiments and export the ten-figure presentation summary.

Run from the repository root: python dataviz/presentation_summary.py
Use --reuse-validated for styling changes; every cached input hash is rechecked.
SVGs/CSVs/provenance live in dataviz/figures/presentation_summary/; the Markdown
is PRESENTATION_SUMMARY.md in the root. --preview-dir adds review-only PNGs.
No DFA generation or pair calculations are performed.
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
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dataviz/figures/presentation_summary'
ORIGINAL_SOURCE = '2026-11-15_19-36-35-433280_UTC'
ORIGINAL_RESULT = '2026-11-15_19-55-50-157162_UTC'
CROSS_RESULT = '2026-11-15_21-03-45-337283_UTC'
HIGH_SOURCE = '2026-11-15_21-32-55-118406_UTC'
HIGH_RESULT = '2026-11-15_21-33-59-533782_UTC'
METRICS = ('probability_of_agreement', 'weighted_jaccard')
METRIC_LABELS = ('Agreement', 'Weighted Jaccard')
STATES = (10, 20, 30)
CROSS_STATES = ((10, 20), (10, 30), (20, 30))
BIN_COUNT = 20
SPARSE = 30
SUPPORTED = 100
ANALYSIS_VERSION = 1
COLORS = {5: '#9467bd', 10: '#0072b2', 15: '#009e73',
          20: '#d55e00', 25: '#cc79a7', 30: '#333333'}
STYLES = {5: '-', 10: '-', 15: '--', 20: '--', 25: ':', 30: '-.'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '|' + '---|' * len(headers)] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def average_ranks(values):
    """Average ranks for ties, matching the usual Spearman convention."""
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    ends = counts.cumsum()
    return (ends - (counts - 1) / 2)[inverse].astype(float)


def correlation(x, y):
    require(len(x) > 1 and np.ptp(x) > 0 and np.ptp(y) > 0,
            'Correlation needs nonconstant observations')
    return float(np.corrcoef(x, y)[0, 1])


def bin_summary(scores, lengths):
    indices = np.minimum((scores * BIN_COUNT).astype(int), BIN_COUNT - 1)
    n = np.bincount(indices, minlength=BIN_COUNT)
    sx = np.bincount(indices, weights=scores, minlength=BIN_COUNT)
    sy = np.bincount(indices, weights=lengths, minlength=BIN_COUNT)
    return {'n': n.tolist(), 'sum_similarity': sx.tolist(), 'sum_sds': sy.tolist()}


def configurations():
    for alphabet in (2, 3, 4, 5):
        for state in (10, 15, 20, 25, 30):
            yield 'original', alphabet, (state,), ORIGINAL_SOURCE, ORIGINAL_RESULT
    for alphabet in (2, 3, 4, 5):
        for states in CROSS_STATES:
            yield 'cross', alphabet, states, ORIGINAL_SOURCE, CROSS_RESULT
    for alphabet in (2, 3):
        for state in (5, 10, 15):
            yield 'high', alphabet, (state,), HIGH_SOURCE, HIGH_RESULT


def analyze():
    inputs, source_cache, records = {}, {}, []

    def remember(path):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in inputs:
            inputs[relative] = digest(path)
        return inputs[relative]

    def source(alphabet, state, source_id, expected_hashes):
        directory = ROOT / 'data' / f'alphabet_{alphabet}' / f'states_{state}' / source_id
        for filename, expected in expected_hashes.items():
            require(remember(directory / filename) == expected,
                    f'Source hash mismatch: {directory / filename}')
        key = alphabet, state, source_id
        if key not in source_cache:
            m = read_json(directory / 'manifest.json')
            require((m['status'], m['run_id'], m['alphabet_size'], m['state_count'],
                     m['sample_count']) == ('complete', source_id, alphabet, state, 500),
                    f'Unexpected source: {directory}')
            path = directory / m['batch_file']
            remember(directory / 'manifest.json')
            remember(path)
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rt', encoding='utf-8') as stream:
                ids = [json.loads(line)['id'] for line in stream]
            require(len(ids) == 500 and len(set(ids)) == 500, 'Invalid source IDs')
            source_cache[key] = {identifier: i for i, identifier in enumerate(sorted(ids))}
        return source_cache[key]

    for kind, alphabet, states, source_id, results_id in configurations():
        cross = kind == 'cross'
        base = ROOT / 'data' / f'alphabet_{alphabet}'
        directory = (base / 'cross_state' / source_id / results_id /
                     f'states_{states[0]}_vs_{states[1]}' if cross else
                     base / f'states_{states[0]}' / source_id / 'comparisons' / results_id)
        manifest_path = directory / 'manifest.json'
        m = read_json(manifest_path)
        require((m['status'], m['source_run_id'], m['results_id'], m['alphabet_size'],
                 m['calculations']) == ('complete', source_id, results_id, alphabet, 'both'),
                f'Unexpected result configuration: {directory}')
        require(m['distribution']['name'] == 'uniform_length_uniform_symbols' and
                m['distribution']['horizon'] == 5 and m['distribution']['metric_version'] == 1,
                'Expected matching H=5 distributions and metric versions')
        if cross:
            require((m['state_count_a'], m['state_count_b']) == states and
                    m['dfa_count_a'] == m['dfa_count_b'] == 500,
                    'Cross-state manifest mismatch')
            require(tuple(s['state_count'] for s in m['sources']) == states,
                    'Cross-state sources out of order')
            maps = [source(alphabet, s['state_count'], source_id, s['sha256'])
                    for s in m['sources']]
            expected = 250000
        else:
            require(m['state_count'] == states[0] and m['dfa_count'] == 500,
                    'Within-state manifest mismatch')
            ids = source(alphabet, states[0], source_id, m['source_sha256'])
            maps, expected = [ids, ids], 124750
        require(m['pair_count'] == m['expected_pair_count'] == expected,
                'Unexpected pair denominator')
        path = directory / m['pairs_file']
        remember(manifest_path)
        remember(path)
        values = np.empty((expected, 8), dtype=float)
        seen = np.zeros((500, 500), dtype=bool)
        opener = gzip.open if path.suffix == '.gz' else open
        count = 0
        with opener(path, 'rt', encoding='utf-8') as stream:
            for row in stream:
                r = json.loads(row)
                require(count < expected, 'Too many pair rows')
                require(r['a'] in maps[0] and r['b'] in maps[1], 'Unknown endpoint ID')
                i, j = maps[0][r['a']], maps[1][r['b']]
                require(not seen[i, j] and (cross or r['a'] < r['b']),
                        'Duplicate or unordered within-state pair')
                if cross:
                    require((r['state_count_a'], r['state_count_b']) == states,
                            'Cross-state endpoint mismatch')
                seen[i, j] = True
                length = r['length']
                require((length is None and r['witness'] is None) or
                        (type(length) is int and length >= 0 and
                         isinstance(r['witness'], list) and len(r['witness']) == length and
                         all(symbol in m['alphabet'] for symbol in r['witness'])),
                        'Invalid SDS/witness record')
                values[count] = (np.nan if length is None else length,
                                 r[METRICS[0]], r[METRICS[1]], r['weight_a'], r['weight_b'],
                                 r['weight_intersection'], r['weight_union'],
                                 r['weight_symmetric_difference'])
                count += 1
        require(count == expected and seen.sum() == expected, 'Incomplete pair coverage')
        length = values[:, 0]
        finite = np.isfinite(length)
        hist = {str(int(k)): int(v) for k, v in Counter(length[finite]).items()}
        equivalent = int((~finite).sum())
        require(hist == m['length_histogram'] and equivalent == m['equivalent_pair_count'],
                'Pair rows disagree with manifest histogram/equivalence')
        require(np.isfinite(values[:, 1:]).all() and
                ((values[:, 1:] >= 0) & (values[:, 1:] <= 1)).all(), 'Invalid score/weight')
        a, b, intersection, union, difference = values[:, 3:].T
        require(np.allclose(union, a + b - intersection, atol=1e-12, rtol=0) and
                np.allclose(difference, union - intersection, atol=1e-12, rtol=0) and
                np.allclose(values[:, 1], 1 - difference, atol=1e-12, rtol=0),
                'Language weight / agreement identities failed')
        jaccard = np.divide(intersection, union, out=np.ones_like(union), where=union != 0)
        require(np.allclose(values[:, 2], jaccard, atol=1e-12, rtol=0),
                'Jaccard identity failed')
        require((values[finite, 1] + 1e-12 >= np.minimum(length[finite] / 6, 1)).all(),
                'SDS agreement bound failed')
        require(np.allclose(values[(~finite) | (length > 5), 1:3], 1, atol=1e-12, rtol=0),
                'Bounded perfect-score constraint failed')
        record = dict(kind=kind, alphabet=alphabet, states=list(states), pair_count=count,
                      finite_pairs=int(finite.sum()), equivalent_pairs=equivalent,
                      histogram=hist, maximum_sds=int(max(length[finite])),
                      mean_finite_sds=float(length[finite].mean()),
                      mean_positive_sds=float(length[finite & (length > 0)].mean()),
                      mean_similarity_all={metric: float(values[:, col].mean())
                                           for col, metric in enumerate(METRICS, 1)})
        if cross or (kind == 'original' and states[0] in STATES):
            y = length[finite]
            ranked_y = average_ranks(y)
            record['metrics'] = {}
            for col, metric in enumerate(METRICS, 1):
                x = values[finite, col]
                record['metrics'][metric] = dict(
                    pearson=correlation(x, y), spearman=correlation(average_ranks(x), ranked_y),
                    bins=bin_summary(x, y))
        records.append(record)
        print(f'Validated {kind}, alphabet {alphabet}, states {states}: {count:,} pairs', flush=True)
    require(sum(r['pair_count'] for r in records) == 6243500, 'Unexpected total coverage')
    return dict(analysis_version=ANALYSIS_VERSION, records=records, inputs=inputs,
                validated_utc=datetime.now(timezone.utc).isoformat())


def select(records, kind, alphabet):
    return [r for r in records if r['kind'] == kind and r['alphabet'] == alphabet]


def relationships(records, kind, alphabet):
    return [r for r in select(records, kind, alphabet) if 'metrics' in r]


def pooled_bins(records, metric):
    return {key: np.sum([r['metrics'][metric]['bins'][key] for r in records], axis=0)
            for key in ('n', 'sum_similarity', 'sum_sds')}


def compare(records):
    comparisons = []
    for alphabet in (2, 3, 4, 5):
        within = relationships(records, 'original', alphabet)
        cross = relationships(records, 'cross', alphabet)
        n_within = sum(r['finite_pairs'] for r in within)
        n_cross = sum(r['finite_pairs'] for r in cross)
        mean_within = sum(r['finite_pairs'] * r['mean_finite_sds'] for r in within) / n_within
        mean_cross = sum(r['finite_pairs'] * r['mean_finite_sds'] for r in cross) / n_cross
        for metric in METRICS:
            w, c = pooled_bins(within, metric), pooled_bins(cross, metric)
            supported = (w['n'] >= SUPPORTED) & (c['n'] >= SUPPORTED)
            require(supported.any(), 'No shared supported bins')
            weights = np.minimum(w['n'][supported], c['n'][supported])
            difference = c['sum_sds'][supported] / c['n'][supported] - w['sum_sds'][supported] / w['n'][supported]
            comparisons.append(dict(
                alphabet=alphabet, metric=metric, within_finite_pairs=n_within,
                cross_finite_pairs=n_cross, within_mean_sds=mean_within,
                cross_mean_sds=mean_cross, mean_sds_difference=mean_cross - mean_within,
                shared_supported_bins=int(supported.sum()),
                within_supported_fraction=float(w['n'][supported].sum() / n_within),
                cross_supported_fraction=float(c['n'][supported].sum() / n_cross),
                weighted_bin_mae=float(np.average(np.abs(difference), weights=weights)),
                maximum_supported_bin_gap=float(np.max(np.abs(difference)))))
    return comparisons


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def exports(data, comparisons, output):
    distributions, correlations, bins = [], [], []
    for r in data['records']:
        label = ' vs '.join(map(str, r['states']))
        for bucket in list(range(7)) + ['equivalent']:
            count = r['equivalent_pairs'] if bucket == 'equivalent' else r['histogram'].get(str(bucket), 0)
            distributions.append(dict(dataset=r['kind'], alphabet=r['alphabet'], states=label,
                                      bucket=bucket, pair_count=count,
                                      fraction_all_pairs=count / r['pair_count'], total_pairs=r['pair_count']))
        for metric, stats in r.get('metrics', {}).items():
            correlations.append(dict(dataset=r['kind'], alphabet=r['alphabet'], states=label,
                                     metric=metric, finite_pairs=r['finite_pairs'],
                                     pearson_r=stats['pearson'], spearman_rho=stats['spearman']))
            for i, n in enumerate(stats['bins']['n']):
                bins.append(dict(dataset=r['kind'], alphabet=r['alphabet'], states=label,
                                 metric=metric, bin_left=i / BIN_COUNT, bin_right=(i + 1) / BIN_COUNT,
                                 finite_pairs=n, sparse=0 < n < SPARSE,
                                 mean_similarity=stats['bins']['sum_similarity'][i] / n if n else '',
                                 mean_finite_sds=stats['bins']['sum_sds'][i] / n if n else ''))
    write_csv(output / 'sds_buckets.csv', distributions)
    write_csv(output / 'correlations.csv', correlations)
    write_csv(output / 'similarity_bins.csv', bins)
    write_csv(output / 'within_cross_comparison.csv', comparisons)


def setup_style():
    plt.rcParams.update({'font.family': 'sans-serif',
                         'font.sans-serif': ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans'],
                         'font.size': 15,
                         'axes.labelsize': 16, 'axes.titlesize': 18,
                         'xtick.labelsize': 14, 'ytick.labelsize': 14,
                         'legend.fontsize': 14, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False})


def save(fig, name, output, preview_dir):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    frame = fig.bbox
    for artist in [*fig.texts, *fig.legends]:
        extent = artist.get_window_extent(renderer)
        require(extent.x0 >= frame.x0 - 1 and extent.x1 <= frame.x1 + 1 and
                extent.y0 >= frame.y0 - 1 and extent.y1 <= frame.y1 + 1,
                f'Figure text/legend extends outside canvas: {name}')
    for legend in fig.legends:
        for ax in fig.axes:
            require(not legend.get_window_extent(renderer).overlaps(ax.title.get_window_extent(renderer)),
                    f'Legend overlaps panel title: {name}')
    fig.savefig(output / f'{name}.svg', facecolor='white')
    if preview_dir:
        fig.savefig(preview_dir / f'{name}.png', dpi=120, facecolor='white')
    plt.close(fig)


def bucket_figure(records, kind, alphabet, number, output, preview_dir):
    items = select(records, kind, alphabet)
    maximum = max(r['maximum_sds'] for r in items)
    title = 'Original run' if kind == 'original' else 'High SDS run'
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'width_ratios': [1.55, 1]})
    fig.subplots_adjust(left=.07, right=.98, bottom=.20, top=.73, wspace=.22)
    fig.suptitle(f'{title}: shortest distinguishing strings · {alphabet} symbols', fontsize=26, y=.97)
    fig.text(.5, .91, 'Exact-length buckets · 124,750 pairs per state size · 500 DFAs per batch',
             ha='center', fontsize=16)
    width = .78 / len(items)
    for panel, ax in enumerate(axes):
        buckets = list(range(maximum + 1)) + ['Eq.'] if panel == 0 else list(range(3, maximum + 1))
        for offset, r in enumerate(items):
            state = r['states'][0]
            y = [r['equivalent_pairs'] if b == 'Eq.' else r['histogram'].get(str(b), 0) for b in buckets]
            x = np.arange(len(buckets)) + (offset - (len(items) - 1) / 2) * width
            ax.bar(x, y, width=width, color=COLORS[state],
                   edgecolor='white', linewidth=.45, label=f'{state} states', zorder=3)
            if panel == 1:
                for px, count in zip(x, y):
                    ax.annotate(f'{count:,}', (px, count), xytext=(0, 7),
                                textcoords='offset points', ha='center', fontsize=12,
                                rotation=90 if len(items) > 3 else 0, color=COLORS[state])
        ax.set_xticks(np.arange(len(buckets)), [str(b) for b in buckets])
        ax.set_xlabel('SDS length' if panel == 1 else 'SDS length; Eq. = equivalent')
        ax.set_ylabel('Number of pairs')
        ax.set_title('Full distribution' if panel == 0 else 'Tail detail · SDS ≥ 3', pad=15)
        ax.set_ylim(0, 70000 if panel == 0 else max(
            r['histogram'].get(str(b), 0) for r in items for b in buckets) * 1.30)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .87), ncol=len(items),
               frameon=False, title='Generated state count')
    fig.text(.5, .105, 'SDS 0 distinguishes on the empty string; equivalent pairs have no finite SDS.',
             ha='center', fontsize=14)
    fig.text(.5, .065, 'Both panels count exact lengths. The tail panel repeats the longer-length buckets on its own linear scale.',
             ha='center', fontsize=13)
    name = f'{number:02d}_{kind}_sds_alphabet_{alphabet}'
    save(fig, name, output, preview_dir)
    return name


def curve(ax, stats, color, style='-', grey=False):
    b = stats['bins']
    n = np.asarray(b['n'])
    x = np.divide(b['sum_similarity'], n, out=np.full(BIN_COUNT, np.nan), where=n > 0)
    y = np.divide(b['sum_sds'], n, out=np.full(BIN_COUNT, np.nan), where=n > 0)
    for i in range(BIN_COUNT - 1):
        if not (n[i] and n[i + 1]):
            continue
        sparse = min(n[i], n[i + 1]) < SPARSE
        ax.plot(x[i:i + 2], y[i:i + 2], linestyle=':' if sparse else style,
                color=color, linewidth=1.8 if grey else 2.2,
                alpha=(.30 if grey else .42) if sparse else (.48 if grey else .95),
                zorder=1 if grey else 3)
    for sparse in (False, True):
        mask = (n > 0) & ((n < SPARSE) if sparse else (n >= SPARSE))
        ax.plot(x[mask], y[mask], linestyle='none', marker='o', markersize=4 if grey else 5.5,
                markerfacecolor='white' if sparse else color, markeredgecolor=color,
                alpha=.48 if grey else .95, zorder=2 if grey else 4)


def relationship_figure(records, kind, alphabets, overlay, number, y_tops, output, preview_dir):
    fig, axes = plt.subplots(2, 2, figsize=(16, 9), sharex=True, sharey='row')
    fig.subplots_adjust(left=.075, right=.985, bottom=.16, top=.78, hspace=.44, wspace=.14)
    title = 'In-category' if kind == 'original' else 'Cross-category'
    suffix = ' with in-category references' if overlay else ''
    fig.suptitle(f'{title} similarity and SDS{suffix}', fontsize=26, y=.97)
    fig.text(.5, .915, f'Alphabets {alphabets[0]} and {alphabets[1]} · H=5 · Matched axes per alphabet across Figures 3–8',
             ha='center', fontsize=16)
    for row, alphabet in enumerate(alphabets):
        for col, metric in enumerate(METRICS):
            ax = axes[row, col]
            if overlay:
                for r in relationships(records, 'original', alphabet):
                    curve(ax, r['metrics'][metric], '#777777', STYLES[r['states'][0]], grey=True)
            for index, r in enumerate(relationships(records, kind, alphabet)):
                state = r['states'][0] if kind == 'original' else STATES[index]
                curve(ax, r['metrics'][metric], COLORS[state], STYLES[state])
            ax.set_title(f'{alphabet} symbols · {METRIC_LABELS[col]}', pad=8)
            ax.set_xlim(-.015, 1.015)
            ax.set_ylim(-.05, y_tops[alphabet])
            ax.set_xticks(np.linspace(0, 1, 6))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
            ax.grid(alpha=.18)
            ax.set_axisbelow(True)
            if row == 1:
                ax.set_xlabel(METRIC_LABELS[col])
            if col == 0:
                ax.set_ylabel('Mean finite SDS length')
    labels = [f'{s} states' for s in STATES] if kind == 'original' else [f'{a} vs {b} states' for a, b in CROSS_STATES]
    handles = [Line2D([], [], color=COLORS[state], linestyle=STYLES[state], marker='o',
                      linewidth=2.2, markersize=5, label=label) for state, label in zip(STATES, labels)]
    if overlay:
        handles.append(Line2D([], [], color='#777777', alpha=.55, linewidth=1.8,
                              label='In-category references'))
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .88), ncol=len(handles), frameon=False)
    fig.text(.5, .075, 'Points are means within similarity bins of width 0.05; empty bins break lines. Equivalent pairs excluded.',
             ha='center', fontsize=13)
    fig.text(.5, .035, 'Hollow points / faint dotted segments: fewer than 30 pairs. ' +
             ('Grey: in-category 10/20/30-state curves.' if overlay else 'SDS 0 retained; states 15/25 omitted.'),
             ha='center', fontsize=13)
    name = f'{number:02d}_{"overlay" if overlay else kind}_similarity_alphabets_{alphabets[0]}_{alphabets[1]}'
    save(fig, name, output, preview_dir)
    return name


def create_figures(records, output, preview_dir):
    setup_style()
    files = []
    for alphabet in (2, 3):
        files.append(bucket_figure(records, 'original', alphabet, len(files) + 1, output, preview_dir))
    y_tops = {}
    for alphabet in (2, 3, 4, 5):
        max_mean = max(sy / n for r in records if r['alphabet'] == alphabet
                       for v in r.get('metrics', {}).values()
                       for n, sy in zip(v['bins']['n'], v['bins']['sum_sds']) if n)
        y_tops[alphabet] = np.ceil((max_mean + .15) * 2) / 2
    for kind, overlay in (('original', False), ('cross', False), ('cross', True)):
        for alphabets in ((2, 3), (4, 5)):
            files.append(relationship_figure(records, kind, alphabets, overlay,
                                             len(files) + 1, y_tops, output, preview_dir))
    for alphabet in (2, 3):
        files.append(bucket_figure(records, 'high', alphabet, len(files) + 1, output, preview_dir))
    return files


def contact_sheet(files, preview_dir):
    if not preview_dir:
        return
    fig, axes = plt.subplots(5, 2, figsize=(16, 22.5))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=.015, wspace=.015)
    for ax, name in zip(axes.flat, files):
        ax.imshow(plt.imread(preview_dir / f'{name}.png'))
        ax.set_axis_off()
    fig.savefig(preview_dir / 'contact_sheet.png', dpi=120, facecolor='white')
    plt.close(fig)


def distribution_table(records, kind, alphabet):
    items = select(records, kind, alphabet)
    maximum = max(r['maximum_sds'] for r in items)
    return table(['States'] + [f'SDS {i}' for i in range(maximum + 1)] + ['Equivalent', 'Total'],
                 [[r['states'][0]] + [f"{r['histogram'].get(str(i), 0):,}" for i in range(maximum + 1)] +
                  [f"{r['equivalent_pairs']:,}", f"{r['pair_count']:,}"] for r in items])


def correlation_table(records, kind, alphabets):
    return table(['Alphabet', 'States', 'Finite pairs', 'Agreement r', 'Agreement ρ', 'Jaccard r', 'Jaccard ρ'],
                 [[r['alphabet'], ' vs '.join(map(str, r['states'])), f"{r['finite_pairs']:,}"] +
                  [f"{r['metrics'][metric][stat]:.3f}" for metric in METRICS for stat in ('pearson', 'spearman')]
                  for alphabet in alphabets for r in relationships(records, kind, alphabet)])


def write_markdown(records, comparisons, files):
    lines = ['# Shortest distinguishing strings: presentation summary', '',
             'Ten figures from the original and High SDS experiments. Each batch contains 500 DFAs; '
             'within-category means the same alphabet and generated state count, while cross-category '
             'means different state counts within the same alphabet.', '',
             table(['Experiment', 'Configurations', 'Pairs'], [
                 ['Original, within-category', 'Alphabets 2–5 × states 10/15/20/25/30', '2,495,000'],
                 ['Original, cross-category', 'Alphabets 2–5 × 10–20 / 10–30 / 20–30 states', '3,000,000'],
                 ['High SDS, within-category', 'Alphabets 2/3 × states 5/10/15', '748,500']]), '',
             '**Reading the figures:** SDS 0 is an empty-string distinction; equivalent pairs have no finite SDS. '
             'Both similarities use H=5. Similarity figures and correlations exclude equivalent pairs, retain SDS 0, '
             'and omit original states 15/25. All figures are SVGs sized for 16:9 slides.', '']

    def section(index, title, text, content):
        name = files[index - 1]
        lines.extend([f'## {index}. {title}', '',
                      f'![{title}](dataviz/figures/presentation_summary/{name}.svg)', '', text, '', content, ''])

    section(1, 'Original SDS buckets — alphabet 2',
            'Most pairs differ at length 0 or 1. The longest observed SDS is 6, occurring in the 10- and 15-state batches.',
            distribution_table(records, 'original', 2))
    section(2, 'Original SDS buckets — alphabet 3',
            'Long distinctions are rarer than with alphabet 2. The tail enlargement shows every observed bucket above length 2.',
            distribution_table(records, 'original', 3))
    lines.extend(['**Alphabets 4 and 5:** alphabet 4 has four SDS=3 pairs, all at 10 states; '
                  'alphabet 5 has no SDS above 2. The full counts, including both alphabets, are in '
                  '[the bucket CSV](dataviz/figures/presentation_summary/sds_buckets.csv).', ''])
    for index, alphabets in ((3, (2, 3)), (4, (4, 5))):
        items = [r for a in alphabets for r in relationships(records, 'original', a)]
        ar = [r['metrics'][METRICS[0]]['pearson'] for r in items]
        jr = [r['metrics'][METRICS[1]]['pearson'] for r in items]
        section(index, f'In-category similarity and SDS — alphabets {alphabets[0]}/{alphabets[1]}',
                f'Agreement has Pearson r={min(ar):.3f}–{max(ar):.3f}; Weighted Jaccard has '
                f'r={min(jr):.3f}–{max(jr):.3f}. Curves show binned means, and hollow markers identify sparse bins.',
                correlation_table(records, 'original', alphabets))
    for index, alphabets in ((5, (2, 3)), (6, (4, 5))):
        extra = ('The longest cross-category SDS is 5: four binary pairs at 10 vs 20 states.' if index == 5 else
                 'Alphabet 4 has two SDS=3 pairs, both at 10 vs 20 states; alphabet 5 has none above 2.')
        section(index, f'Cross-category similarity and SDS — alphabets {alphabets[0]}/{alphabets[1]}',
                f'Each curve represents 250,000 cross-category pairs. {extra}',
                correlation_table(records, 'cross', alphabets))
    for index, alphabets in ((7, (2, 3)), (8, (4, 5))):
        items = [r for r in comparisons if r['alphabet'] in alphabets]
        max_mae = max(r['weighted_bin_mae'] for r in items)
        max_gap = max(r['maximum_supported_bin_gap'] for r in items)
        max_overall_gap = max(abs(r['mean_sds_difference']) for r in items)
        minimum_coverage = min(min(r['within_supported_fraction'], r['cross_supported_fraction']) for r in items)
        # Strict bounds must round outward; the tables below use ordinary rounding.
        max_overall_bound = np.ceil(max_overall_gap * 10000) / 10000
        max_mae_bound = np.ceil(max_mae * 10000) / 10000
        minimum_coverage_bound = np.floor(minimum_coverage * 10000) / 10000
        section(index, f'Cross-category with in-category references — alphabets {alphabets[0]}/{alphabets[1]}',
                f'Overall mean SDS differs by at most {max_overall_bound:.4f} symbols; across shared supported bins, '
                f'weighted mean absolute differences are at most {max_mae_bound:.4f} (largest single-bin gap: {max_gap:.4f}). '
                f'These bins cover at least '
                f'{minimum_coverage_bound:.2%} of each pooled finite-pair sample; sparse tails can differ more.',
                table(['Alphabet', 'Metric', 'Shared bins', 'Within coverage', 'Cross coverage', 'Mean abs. gap', 'Max abs. gap'],
                      [[r['alphabet'], METRIC_LABELS[METRICS.index(r['metric'])], r['shared_supported_bins'],
                        f"{r['within_supported_fraction']:.2%}", f"{r['cross_supported_fraction']:.2%}",
                        f"{r['weighted_bin_mae']:.4f}", f"{r['maximum_supported_bin_gap']:.4f}"] for r in items]))
    section(9, 'High SDS run buckets — alphabet 2',
            'The 5-state batch contains four SDS=5 pairs and 120 SDS=4 pairs. This is a separate seed-20 sample, '
            'with all generated DFAs retained.', distribution_table(records, 'high', 2))
    section(10, 'High SDS run buckets — alphabet 3',
            'The 5-state batch contains two SDS=4 pairs; the 10- and 15-state batches reach length 3. '
            'Equivalent pairs remain separate from the finite-length buckets.', distribution_table(records, 'high', 3))
    lines.extend(['## Methods and supporting data', '',
                  '- **Sampling:** original source uses seed 42; High SDS uses seed 20. Neither sample is filtered. '
                  'Generated state counts include unreachable states.',
                  '- **Similarity:** sample a length uniformly from 0 through 5, then sample symbols independently '
                  'and uniformly. Agreement includes joint rejection; Weighted Jaccard measures accepted-language '
                  'intersection weight divided by union weight, with empty union assigned 1.',
                  '- **Curves:** fixed bins [left, right), with score 1 included in the last bin. Both coordinates '
                  'are observed bin means. Empty bins break lines; bins with fewer than 30 pairs use hollow markers '
                  'and faint dotted segments. Each alphabet has matching axes across Figures 3–8 and both metrics; '
                  'different alphabets can have different vertical limits. No fitted regression or smoothing is used.',
                  '- **Correlations:** Pearson r and Spearman ρ use all finite-SDS pairs in each configuration, '
                  'including zero; Spearman uses average ranks for ties. Pairs share DFAs, so these are descriptive '
                  'associations without independence-based significance tests.',
                  '- **Overlay tables:** separately pool the three within-category state sizes and the three '
                  'cross-category combinations within each alphabet. Compare bins with at least 100 finite pairs '
                  'in each pool; weight absolute SDS-mean differences by the smaller pool count in each bin. '
                  'Coverage is the fraction of finite pairs in those bins. Grey curves themselves remain separate '
                  '10/20/30-state references; their dash patterns match Figure 3/4. Tables compare corresponding '
                  'similarity intervals, whose observed mean x positions can differ.',
                  '- **Limits:** the generator is not uniform over DFAs. Bounded similarity 1 does not establish '
                  'language equivalence. The High SDS run changes both seed and state sizes and does not isolate '
                  'a causal state-count effect.', '',
                  table(['Inputs', 'Source ID', 'Results ID'], [
                      ['Original within-category', f'`{ORIGINAL_SOURCE}`', f'`{ORIGINAL_RESULT}`'],
                      ['Original cross-category', f'`{ORIGINAL_SOURCE}`', f'`{CROSS_RESULT}`'],
                      ['High SDS', f'`{HIGH_SOURCE}`', f'`{HIGH_RESULT}`']]), '',
                  '[Exact buckets](dataviz/figures/presentation_summary/sds_buckets.csv) · '
                  '[Correlations](dataviz/figures/presentation_summary/correlations.csv) · '
                  '[Similarity bins and counts](dataviz/figures/presentation_summary/similarity_bins.csv) · '
                  '[Within/cross comparison](dataviz/figures/presentation_summary/within_cross_comparison.csv) · '
                  '[Input provenance](dataviz/figures/presentation_summary/provenance.json)', '',
                  'Rebuild from the repository root with `python dataviz/presentation_summary.py`. '
                  'This validates and summarizes saved results; it performs no new DFA comparisons.', ''])
    (ROOT / 'PRESENTATION_SUMMARY.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-validated', action='store_true')
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
    cache = OUTPUT / 'validated_summary.json'
    if args.reuse_validated:
        data = read_json(cache)
        require(data['analysis_version'] == ANALYSIS_VERSION, 'Cache analysis version changed')
        for relative, expected in data['inputs'].items():
            require(digest(ROOT / relative) == expected, f'Cached input changed: {relative}')
        print('Rechecked every cached input hash', flush=True)
    else:
        data = analyze()
        cache.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    comparisons = compare(data['records'])
    exports(data, comparisons, OUTPUT)
    files = create_figures(data['records'], OUTPUT, args.preview_dir)
    contact_sheet(files, args.preview_dir)
    write_markdown(data['records'], comparisons, files)
    provenance = dict(
        created_utc=datetime.now(timezone.utc).isoformat(), validated_utc=data['validated_utc'],
        source_ids={'original': ORIGINAL_SOURCE, 'high': HIGH_SOURCE},
        results_ids={'original': ORIGINAL_RESULT, 'cross': CROSS_RESULT, 'high': HIGH_RESULT},
        horizon=5, bin_count=BIN_COUNT, sparse_bin_threshold=SPARSE,
        supported_comparison_bin_threshold=SUPPORTED, analysis_version=ANALYSIS_VERSION,
        pair_rows_validated=sum(r['pair_count'] for r in data['records']),
        inputs=data['inputs'], figures=[f'{f}.svg' for f in files],
        script_sha256=digest(Path(__file__)), matplotlib=matplotlib.__version__, numpy=np.__version__,
        finite_sds='Includes zero; excludes equivalent pairs',
        comparison_weight='Minimum within/cross pooled count in each shared supported bin',
        correlations='Pearson on pairs; Spearman on pairwise average ranks, no p-values')
    (OUTPUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    print(f'Saved {len(files)} SVG figures and PRESENTATION_SUMMARY.md', flush=True)


if __name__ == '__main__':
    main()

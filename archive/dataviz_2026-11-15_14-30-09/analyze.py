"""Read saved DFA comparisons, validate joins, and export descriptive figures.

Run: python dataviz/analyze.py
No generation, BFS, or similarity calculations are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
from result_summary import read_jsonl

SOURCE = '2026-11-15_00-36-37-375402_UTC'
RESULT4 = '2026-11-15_17-55-16-095569_UTC'
METRICS = {'probability_of_agreement': 'Agreement', 'weighted_jaccard': 'Weighted Jaccard'}
CONFIGS = [(a, s) for a in (2, 3) for s in (10, 20, 30)]
COLORS = dict(zip(CONFIGS, plt.get_cmap('tab10').colors[:6]))


def label(key):
    return f'{key[0]} symbols, {key[1]} generated states'


# Display wording is separate from stored column names so CSV compatibility is retained.
AXIS_LABELS = {
    'Mean finite SDS length': 'Average SDS length (symbols)\nNon-equivalent pairs only',
    'Mean SDS across finite partners': 'Average SDS length (symbols)\nAgainst non-equivalent DFAs',
    'Accepting states (% of raw states)': 'Accepting states (%)\nOf all generated states',
    'Mean accepting-state fraction of the two DFAs': 'Average accepting-state percentage\nAcross the two DFAs in each pair',
    'Absolute difference in accepting-state fractions': 'Difference in accepting-state percentages\nBetween the two DFAs (percentage points)',
    'SDS length / equivalence': 'Shortest distinguishing string length (symbols)\nEquivalent = no distinguishing string',
    '% of all pairs': 'Pairs (% of all 124,750 comparisons)',
    'Positive SDS length': 'Shortest distinguishing string length (symbols)',
    '% conditional on finite SDS > 0': 'Pairs (% of non-equivalent pairs\nwith SDS length greater than zero)',
    'Threshold d': 'Minimum SDS length counted (symbols)',
    '% of positive finite pairs with SDS >= d': 'Pairs meeting the minimum (%)\nAmong pairs with positive SDS; logarithmic scale',
    'Raw states': 'Generated states per DFA (before minimization)',
    'Mean SDS length': 'Average SDS length (symbols)',
    'Agreement': 'Agreement score (0 to 1)',
    'Weighted Jaccard': 'Weighted Jaccard score (0 to 1)',
    'Pair count (log color)': 'Pairs per hexagon\nLogarithmic color scale',
    '% of all pairs per bin': 'Pairs in each score interval (%)\nOf all 124,750 comparisons',
    'Finite SDS length': 'Shortest distinguishing string length (symbols)\nNon-equivalent pairs only',
    'Mean Agreement': 'Average agreement score (0 to 1)',
    'Mean Weighted Jaccard': 'Average weighted Jaccard score (0 to 1)',
    'State count': 'Number of states',
    'DFAs': 'Number of DFAs (500 in each panel)',
    '% of H=4 pairs per bin': 'Same DFA pairs in each change interval (%)',
}

FIGURE_NOTES = {
    'acceptance_per_dfa': 'Each dot is one DFA. Its y-value averages comparisons with all non-equivalent DFAs in the same batch; SDS=0 is included. Black line: average of dots at each x-value. Accepting percentage includes unreachable states; 100% means every string is accepted.',
    'sds_vs_acceptance_fraction_mean': 'For a pair with 20% and 60% accepting states, x=40%. Percentages count all generated states, including unreachable states.',
    'sds_vs_acceptance_fraction_gap': 'For a pair with 20% and 60% accepting states, x=40 percentage points. This is an absolute difference, so it is never negative.',
    'sds_grouped_bars': 'Bars compare generated state counts within each alphabet size. Each percentage uses all 124,750 pairs in that batch. Equivalent pairs accept exactly the same language and have no SDS.',
    'sds_six_distributions': 'Numbers above bars are pair counts. Each percentage uses all 124,750 pairs in that panel. SDS=0 means the empty string distinguishes the pair; equivalent pairs have no SDS.',
    'sds_positive_and_tail': 'Both panels exclude SDS=0 and equivalent pairs. Right panel: at x=3, count all pairs with SDS length 3 or more. Equal vertical steps represent multiplicative changes. Exact pair counts are in the distribution CSV.',
    'sds_mean_bars': 'Both bar types exclude equivalent pairs. The first includes SDS=0; the second averages only lengths greater than zero. Generated states include unreachable states and are counted before minimization.',
    'similarity_joint_density': 'Each hexagon contains DFA pairs with similar scores; its color shows their count. Agreement counts both joint acceptance and joint rejection. Jaccard measures shared acceptance relative to acceptance by either DFA.',
    'similarity_distributions': 'Each curve shows the percentage of pairs in score intervals of width 0.025. Agreement bins are assigned using exact integer score numerators to avoid floating-point boundary artifacts. Equivalent pairs are included.',
    'similarity_by_sds': 'Each point averages similarity over all pairs with that exact SDS length; equivalent pairs are excluded. Dashed line: the agreement lower bound forced by the SDS length and sampling rule, rather than an empirical fit.',
    'dfa_size_distributions': 'Reachable: states that some string can visit from the starting state. Minimal: states left after removing unreachable states and merging behaviorally identical states. Dashed line: original generated state count.',
}


def read_result(source, result_id, horizon, a, s):
    directory = source / 'comparisons' / result_id
    manifest_path = directory / 'manifest.json'
    m = json.loads(manifest_path.read_text())
    if (m['status'], m['source_run_id'], m['alphabet_size'], m['state_count'],
        m['distribution']['horizon'], m['calculations']) != ('complete', source.name, a, s, horizon, 'both'):
        raise ValueError(f'Unexpected provenance/configuration: {manifest_path}')
    if m['distribution']['name'] != 'uniform_length_uniform_symbols':
        raise ValueError('Unsupported word distribution')
    p = pd.DataFrame(read_jsonl(directory / m['pairs_file'])).drop(columns='witness')
    stats = pd.DataFrame(read_jsonl(directory / m['dfa_stats_file'])).set_index('id', verify_integrity=True)
    n = len(stats)
    if n != m['dfa_count'] or len(p) != m['pair_count'] or len(p) != n * (n - 1) // 2:
        raise ValueError('Incomplete all-pairs results')
    if p.duplicated(['a', 'b']).any() or not (p.a < p.b).all():
        raise ValueError('Duplicate or unordered pair keys')
    if not set(p.a).union(p.b).issubset(stats.index):
        raise ValueError('Unknown DFA ID')
    hist = {str(int(k)): int(v) for k, v in p.length.value_counts().items()}
    if hist != m['length_histogram'] or int(p.length.isna().sum()) != m['equivalent_pair_count']:
        raise ValueError('SDS histogram differs from manifest')
    for col in [*METRICS, 'weight_a', 'weight_b', 'weight_intersection', 'weight_union', 'weight_symmetric_difference']:
        if not p[col].between(0, 1).all():
            raise ValueError(f'Invalid metric {col}')
    if not np.allclose(p.probability_of_agreement, 1 - p.weight_symmetric_difference, atol=1e-12, rtol=0):
        raise ValueError('Agreement identity failed')
    if not np.allclose(p.weight_union, p.weight_a + p.weight_b - p.weight_intersection, atol=1e-12, rtol=0):
        raise ValueError('Union identity failed')
    expected = np.divide(p.weight_intersection, p.weight_union, out=np.ones(len(p)), where=p.weight_union.to_numpy() != 0)
    if not np.allclose(p.weighted_jaccard, expected, atol=1e-12, rtol=0):
        raise ValueError('Jaccard identity failed')
    bounded_identical = p.length.isna() | (p.length > horizon)
    if not np.allclose(p.loc[bounded_identical, list(METRICS)], 1, atol=1e-12, rtol=0):
        raise ValueError('Bounded-identical score constraint failed')
    finite = p.length.notna()
    if (p.loc[finite, 'probability_of_agreement'] + 1e-12 < np.minimum(p.loc[finite, 'length'], horizon + 1) / (horizon + 1)).any():
        raise ValueError('SDS agreement lower bound failed')
    return p.set_index(['a', 'b'], verify_integrity=True).sort_index(), stats, manifest_path


def load_data(source_id=SOURCE, result_id=RESULT4):
    frames, dfas, provenance = [], [], []
    for a, s in CONFIGS:
        source = ROOT / 'data' / f'alphabet_{a}' / f'states_{s}' / source_id
        sm = json.loads((source / 'manifest.json').read_text())
        if sm['status'] != 'complete':
            raise ValueError('Incomplete source')
        p, stats, mp = read_result(source, result_id, 4, a, s)
        source_rows = list(read_jsonl(source / sm['batch_file']))
        source_stats = pd.DataFrame([{'id': r['id'], 'acceptance_fraction': np.mean(r['acceptance'])} for r in source_rows]).set_index('id', verify_integrity=True)
        if set(source_stats.index) != set(stats.index):
            raise ValueError('Source/stat IDs differ')
        stats = stats.join(source_stats, validate='one_to_one')
        stats['unreachable_fraction'] = 1 - stats.reachable / stats.n_states
        p = p.reset_index()
        for feature in ['acceptance_fraction', 'minimal', 'reachable', 'unreachable_fraction']:
            va, vb = p.a.map(stats[feature]), p.b.map(stats[feature])
            p[feature + '_mean'] = (va + vb) / 2
            p[feature + '_gap'] = abs(va - vb)
            p[feature + '_min'] = np.minimum(va, vb)
            p[feature + '_max'] = np.maximum(va, vb)
        p['acceptance_mass_mean'] = (p.weight_a + p.weight_b) / 2
        p['sds_group'] = p.length.fillna(-1).map(lambda v: 'Equivalent' if v == -1 else str(int(v)))
        p['alphabet'], p['states'] = a, s
        stats['alphabet'], stats['states'] = a, s
        frames.append(p)
        dfas.append(stats.reset_index())
        for path in [source / 'manifest.json', source / sm['batch_file'], mp,
                     mp.parent / 'pairs.jsonl.gz', mp.parent / 'dfa_stats.jsonl.gz']:
            provenance.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f'Loaded {label((a,s))}: {len(p):,} H=4 pairs', flush=True)
    return pd.concat(frames, ignore_index=True), pd.concat(dfas, ignore_index=True), provenance


def run(output=None, source_id=SOURCE, result_id=RESULT4, seed=42):
    output = Path(output) if output else ROOT / 'dataviz' / 'outputs' / result_id
    output.mkdir(parents=True, exist_ok=True)
    tables = output / 'tables'
    tables.mkdir(exist_ok=True)
    p, dfas, provenance = load_data(source_id, result_id)
    finite = p[p.length.notna()]
    positive = finite[finite.length > 0]
    figures = []
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.alpha': .18, 'savefig.dpi': 180})

    def save(fig, name, caption):
        for ax in fig.axes:
            old_x, old_y = ax.get_xlabel(), ax.get_ylabel()
            ax.set_xlabel(AXIS_LABELS.get(old_x, old_x))
            ax.set_ylabel(AXIS_LABELS.get(old_y, old_y))
            if old_x in ('Mean accepting-state fraction of the two DFAs', 'Absolute difference in accepting-state fractions',
                         'Mean unreachable-state fraction', 'Mean bounded acceptance mass at H=4'):
                ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, symbol='' if 'difference' in old_x.lower() else '%'))
            if old_y == 'Fraction <= score':
                ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
            if old_x in ('Finite SDS length', 'Positive SDS length', 'Threshold d', 'SDS threshold (>=)',
                         'Smaller minimal DFA size', 'Larger minimal DFA size', 'Absolute difference in minimal sizes', 'State count'):
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            title = ax.get_title()
            ax.set_title({'Empirical cumulative distribution': 'How many pairs score this low or lower?',
                          'Paired score changes': 'How much did similarity change?',
                          'Positive-length distribution': 'SDS lengths after excluding zero',
                          'Tail survival (labels are pair counts)': 'How many pairs need at least this length?',
                          'Rare tail pairs': 'Pairs with long distinguishing strings',
                          'Tail concentration': 'How many different DFAs form those pairs?'}.get(title, title))
            if title.startswith('Alphabet '):
                ax.set_title(f'Alphabet size: {title.split()[-1]} symbols')
            legend = ax.get_legend()
            if legend:
                for text in legend.get_texts():
                    text.set_text({'All finite SDS': 'Non-equivalent pairs (including SDS=0)',
                                   'Conditional on SDS > 0': 'Only pairs with SDS length > 0',
                                   'Raw size': 'Generated state count',
                                   'Necessary agreement lower bound': 'Minimum possible agreement at this SDS'}.get(text.get_text(), text.get_text()))
        if name == 'acceptance_per_dfa':
            fig.suptitle('Accepting-state percentage and average distinguishing length for each DFA')
        if name == 'sds_mean_bars':
            for ax in fig.axes:
                ax.set_ylim(0, ax.get_ylim()[1] * 1.22)
        notes = [FIGURE_NOTES.get(name, '')]
        if name.startswith('sds_vs_'):
            notes.append('Each point averages non-equivalent pairs within an x-axis interval; SDS=0 is included. Lines connect interval averages. Empty intervals are omitted; few pairs can make a point unstable. Counts are in the CSV table.')
        if name in ('sds_vs_probability_of_agreement', 'sds_vs_weighted_jaccard', 'similarity_joint_density',
                    'similarity_distributions', 'similarity_by_sds'):
            notes.append('Similarity sampling: choose string length uniformly from 0 through H, then choose symbols uniformly; H=4 throughout.')
        if name == 'sds_vs_probability_of_agreement':
            notes.insert(0, 'Agreement is the probability that both DFAs give the same accept/reject answer to a sampled string. A score of 1 can hide differences on strings longer than H.')
        if name == 'sds_vs_weighted_jaccard':
            notes.insert(0, 'Weighted Jaccard is the probability both DFAs accept, divided by the probability at least one accepts. If neither accepts any sampled string, the score is defined as 1.')
        notes.append('SDS = shortest distinguishing string; length counts symbols. These comparisons share DFAs, so they are not independent observations.')
        width, height = fig.get_size_inches()
        wrapped = '\n'.join(textwrap.fill(note, width=int(width * 13)) for note in notes if note)
        footer_height = .18 * len(wrapped.splitlines()) + .28
        fig.set_size_inches(width, height + footer_height)
        fig.text(.02, .02, wrapped, fontsize=9, color='#333333', va='bottom', linespacing=1.35)
        fig.tight_layout(rect=(0, footer_height / (height + footer_height), 1, .95))
        for ext in ('png', 'svg'):
            fig.savefig(output / f'{name}.{ext}', facecolor='white')
        plt.close(fig)
        figures.append((name, caption))
        print(f'Saved {name}', flush=True)

    def facets(title):
        fig, axes = plt.subplots(2, 3, figsize=(13, 7), squeeze=False)
        fig.suptitle(title)
        for key, ax in zip(CONFIGS, axes.flat):
            ax.set_title(label(key))
        return fig, axes.flat

    def groups(frame):
        return frame.groupby(['alphabet', 'states'], sort=True)

    # Requested SDS vs similarity: similarity is x, mean finite SDS is y.
    def binned_lines(feature, title, name, xlabel, bins):
        fig, ax = plt.subplots(figsize=(10, 6))
        rows = []
        for key, g in groups(finite):
            bins_index = pd.cut(g[feature], bins, include_lowest=True)
            agg = g.groupby(bins_index, observed=True).agg(x=(feature, 'mean'), mean_sds=('length', 'mean'), count=('length', 'size'))
            ax.plot(agg.x, agg.mean_sds, 'o-', ms=4, color=COLORS[key], label=label(key))
            agg['alphabet'], agg['states'] = key
            rows.append(agg.reset_index(drop=True))
        ax.set(xlabel=xlabel, ylabel='Mean finite SDS length', title=title)
        ax.legend(fontsize=9)
        pd.concat(rows).to_csv(tables / f'{name}.csv', index=False)
        save(fig, name, 'Lines connect bin means; bins with no observations are omitted. Equivalent pairs excluded. Bin counts are in the accompanying CSV; sparse tails can be unstable.')

    for metric, display in METRICS.items():
        binned_lines(metric, f'SDS versus {display.lower()} (H=4)', 'sds_vs_' + metric, display, np.linspace(0, 1, 21))
    for feature, title in [('acceptance_fraction_mean', 'Mean accepting-state fraction of the two DFAs'),
                           ('acceptance_fraction_gap', 'Absolute difference in accepting-state fractions')]:
        binned_lines(feature, 'SDS versus accepting-state composition', 'sds_vs_' + feature, title, np.linspace(0, 1, 21))

    hist = p.groupby(['alphabet', 'states', 'sds_group']).size().rename('count').reset_index()
    hist['percent_all_pairs'] = hist['count'] / hist.groupby(['alphabet', 'states'])['count'].transform('sum') * 100
    hist.to_csv(tables / 'sds_distribution.csv', index=False)
    categories = [str(i) for i in range(int(finite.length.max()) + 1)] + ['Equivalent']
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for a, ax in zip((2, 3), axes):
        for j, s in enumerate((10, 20, 30)):
            g = hist[(hist.alphabet == a) & (hist.states == s)].set_index('sds_group').reindex(categories, fill_value=0)
            ax.bar(np.arange(len(categories)) + (j - 1) * .25, g.percent_all_pairs, width=.25, color=COLORS[a,s], label=f'{s} states')
        ax.set(xticks=np.arange(len(categories)), xticklabels=categories, ylabel='% of all pairs', xlabel='SDS length / equivalence', title=f'Alphabet {a}')
        ax.legend()
    save(fig, 'sds_grouped_bars', 'Requested grouped bars: each SDS category contains the three raw state counts. Denominator includes all 124,750 pairs per batch.')

    fig, axes = facets('SDS distributions: counts and percentages')
    for (key, g), ax in zip(groups(p), axes):
        counts = g.sds_group.value_counts().reindex(categories, fill_value=0)
        ax.bar(categories, counts / len(g) * 100, color=COLORS[key])
        for i, n in enumerate(counts):
            if n: ax.text(i, n / len(g) * 100 + .6, f'{n:,}', ha='center', fontsize=8, rotation=50)
        ax.tick_params(axis='x', rotation=35)
        ax.set(ylabel='% of all pairs', ylim=(0, 65), xlabel='SDS length / equivalence')
    save(fig, 'sds_six_distributions', 'All six distributions with pair counts above bars. Equivalent means no finite SDS, and is never coded as zero.')

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for key, g in groups(positive):
        counts = g.length.value_counts().reindex(range(1, 7), fill_value=0)
        axes[0].plot(counts.index, counts / len(g) * 100, 'o-', color=COLORS[key], label=label(key))
        survival = [int((g.length >= d).sum()) for d in range(1, 7)]
        axes[1].plot(range(1, 7), np.where(np.array(survival) > 0, np.array(survival)/len(g)*100, np.nan), 'o-', color=COLORS[key], label=label(key))
    axes[0].set(xlabel='Positive SDS length', ylabel='% conditional on finite SDS > 0', title='Positive-length distribution')
    axes[1].set(xlabel='Threshold d', ylabel='% of positive finite pairs with SDS >= d', yscale='log', title='Tail survival (labels are pair counts)')
    axes[0].legend(fontsize=8)
    save(fig, 'sds_positive_and_tail', 'Zero lengths and equivalent pairs excluded from both denominators. The right panel shows percentages with at least the x-axis length, on a logarithmic scale. Exact counts are available in the distribution table.')

    summary = []
    for key, g in groups(p):
        f = g[g.length.notna()]
        row = dict(alphabet=key[0], states=key[1], pairs=len(g), equivalent=int(g.length.isna().sum()),
                   finite_mean=f.length.mean(), positive_mean=f.loc[f.length > 0, 'length'].mean(), max_sds=f.length.max(),
                   beyond_h4=int((g.length > 4).sum()))
        for m in METRICS:
            row[m] = g[m].mean()
            row[m + '_zero'] = int((g[m] == 0).sum())
            row[m + '_one'] = int((g[m] == 1).sum())
        row['zero_union'] = int((g.weight_union == 0).sum())
        summary.append(row)
    summary = pd.DataFrame(summary)
    summary.to_csv(tables / 'batch_summary.csv', index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for a, ax in zip((2,3), axes):
        g = summary[summary.alphabet == a]
        x = np.arange(3)
        bars = ax.bar(x-.18, g.finite_mean, width=.36, label='All finite SDS')
        ax.bar_label(bars, fmt='%.4f', padding=3, fontsize=9)
        bars = ax.bar(x+.18, g.positive_mean, width=.36, label='Conditional on SDS > 0')
        ax.bar_label(bars, fmt='%.4f', padding=3, fontsize=9)
        ax.set(xticks=x, xticklabels=g.states, xlabel='Raw states', ylabel='Mean SDS length', title=f'Alphabet {a}')
        ax.legend()
    save(fig, 'sds_mean_bars', 'Two alphabet panels with raw state counts as bar groups; equivalent pairs excluded. No inferential error bars because pairs share DFAs.')

    fig, axes = facets('Agreement versus weighted Jaccard (H=4)')
    for (key, g), ax in zip(groups(p), axes):
        im = ax.hexbin(g.probability_of_agreement, g.weighted_jaccard, gridsize=40, extent=(0,1,0,1), mincnt=1, bins='log', cmap='viridis')
        ax.set(xlabel='Agreement', ylabel='Weighted Jaccard', xlim=(0,1), ylim=(0,1))
        fig.colorbar(im, ax=ax, label='Pair count (log color)')
    save(fig, 'similarity_joint_density', 'All pairs, including equivalent pairs; hexagon colors show counts on logarithmic scales. Joint rejection contributes to agreement but not to the accepted-word intersection.')

    from diagnostics import agreement_histogram, investigate
    findings = investigate(p, dfas, tables)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for metric, ax in zip(METRICS, axes):
        for key, g in groups(p):
            if metric == 'probability_of_agreement':
                counts, edges = agreement_histogram(g[metric], key[0])
            else:
                counts, edges = np.histogram(g[metric], bins=np.linspace(0, 1, 41))
            ax.stairs(counts / len(g) * 100, edges, color=COLORS[key], label=label(key))
        ax.set(xlabel=METRICS[metric], ylabel='% of all pairs per bin', title='Score distribution (H=4)')
    axes[0].legend(fontsize=8)
    save(fig, 'similarity_distributions', 'Two H=4 histograms. Agreement uses exact integer bin assignment; the earlier oscillation was sensitive to floating-point bin boundaries. See diagnostics tables for the original and corrected counts.')

    conditional = p.groupby(['alphabet','states','sds_group'])[[*METRICS]].agg(['mean','median','min','max','size'])
    conditional.to_csv(tables / 'similarity_by_sds.csv')
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for metric, ax in zip(METRICS, axes):
        for key, g in groups(finite):
            agg = g.groupby('length')[metric].agg(['mean','min','max'])
            ax.plot(agg.index, agg['mean'], 'o-', color=COLORS[key], label=label(key))
        ax.set(xlabel='Finite SDS length', ylabel=f'Mean {METRICS[metric]}', ylim=(0,1.03))
    axes[0].plot(range(7), np.minimum(np.arange(7)/5,1), 'k--', alpha=.6, label='Necessary agreement lower bound')
    axes[0].legend(fontsize=8)
    save(fig, 'similarity_by_sds', 'Conditional means by exact SDS; the agreement lower bound min(d/5,1) follows mathematically from uniform length sampling. An empirical trend along this bound is not independent evidence of causation.')

    # DFA-level accepting fractions: every DFA appears once here.
    endpoints = pd.concat([finite[['alphabet','states','a','length']].rename(columns={'a':'id'}), finite[['alphabet','states','b','length']].rename(columns={'b':'id'})])
    per_dfa = endpoints.groupby(['alphabet','states','id']).length.agg(mean_finite_sds='mean', finite_partners='size').reset_index()
    per_dfa = dfas.merge(per_dfa, on=['alphabet','states','id'], validate='one_to_one')
    per_dfa.to_csv(tables / 'per_dfa.csv', index=False)
    fig, axes = facets('Accepting states versus each DFA’s mean finite SDS')
    for (key, g), ax in zip(groups(per_dfa), axes):
        ax.scatter(g.acceptance_fraction*100, g.mean_finite_sds, s=15, alpha=.3, color=COLORS[key])
        agg = g.groupby('acceptance_fraction').mean_finite_sds.mean()
        ax.plot(agg.index*100, agg.values, 'o-', color='black', ms=3)
        ax.set(xlabel='Accepting states (% of raw states)', ylabel='Mean SDS across finite partners')
    save(fig, 'acceptance_per_dfa', 'Each dot is one DFA. Its average includes comparisons with non-equivalent DFAs in the same batch, including SDS=0. The black line averages dots at each accepting-state percentage. Percentages count all generated states, including unreachable states; 100% means every string is accepted. Counts are in per_dfa.csv.')

    fig, axes = facets('Raw, reachable, and minimal sizes of source DFAs')
    for (key, g), ax in zip(groups(dfas), axes):
        ax.hist([g.reachable,g.minimal], bins=np.arange(.5,key[1]+1.5), label=['Reachable','Minimal'], color=['#4899b5','#db8b42'])
        ax.axvline(key[1], color='black', linestyle='--', label='Raw size')
        ax.set(xlabel='State count', ylabel='DFAs')
        ax.legend(fontsize=8)
    save(fig, 'dfa_size_distributions', '500 DFAs per panel. Raw state count overstates effective size for some generated automata; the generator is biased and these are within-batch comparisons.')

    # Save concrete anomalies and tail endpoint concentration without huge raw exports.
    tail = p[p.length >= 4].copy()
    tail.to_csv(tables / 'tail_pairs_sds_ge4.csv',index=False)
    tail_endpoints = pd.concat([tail[['alphabet','states','a']].rename(columns={'a':'id'}),tail[['alphabet','states','b']].rename(columns={'b':'id'})])
    involvement = tail_endpoints.groupby(['alphabet','states','id']).size().rename('tail_pairs').reset_index().merge(dfas,on=['alphabet','states','id'],validate='one_to_one').sort_values('tail_pairs',ascending=False)
    involvement.to_csv(tables / 'tail_dfa_involvement.csv',index=False)
    perfect = p[(p.length.notna()) & (p.probability_of_agreement == 1) & (p.weighted_jaccard == 1)]
    perfect.to_csv(tables / 'inequivalent_but_perfect_h4.csv',index=False)
    region = p[(p.probability_of_agreement >= .8) & (p.weighted_jaccard <= .2)].copy()
    region['joint_rejection_mass'] = 1-region.weight_union
    region.groupby(['alphabet','states']).agg(pairs=('a','size'),mean_agreement=('probability_of_agreement','mean'),mean_jaccard=('weighted_jaccard','mean'),mean_acceptance_mass=('acceptance_mass_mean','mean'),mean_joint_rejection=('joint_rejection_mass','mean')).to_csv(tables / 'high_agreement_low_jaccard_summary.csv')
    region.sort_values(['probability_of_agreement','weighted_jaccard'],ascending=[False,True]).groupby(['alphabet','states']).head(10).to_csv(tables / 'high_agreement_low_jaccard_examples.csv',index=False)
    metadata = dict(created_utc=datetime.now(timezone.utc).isoformat(),source_id=source_id,h4_results_id=result_id,
                    pairs_h4=len(p),dfas=len(dfas),seed=seed,subsampling='none; all observations used',
                    validation='Manifest counts, unique complete pair keys, scoped IDs, metric identities, SDS agreement bound',
                    python=sys.version,pandas=pd.__version__,numpy=np.__version__,matplotlib=matplotlib.__version__,
                    inputs=provenance,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    diagnostics_sha256=hashlib.sha256((Path(__file__).parent / 'diagnostics.py').read_bytes()).hexdigest())
    (output/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    lines = ['# DFA exploratory visualization report','',f'Source `{source_id}`; H=4 `{result_id}`.',
             '',f'Validated {len(p):,} H=4 pairs, in six separate batches of 500 DFAs. No experiment calculations were rerun.',
             '', '## Reading these results','',
             '- All analyses are descriptive. Pairs share DFAs and are dependent. No independent-pair significance tests or error bars are reported.',
             '- Equivalent pairs have no finite SDS. Means of SDS exclude them; distribution plots explicitly retain them as a separate category.',
             '- Accepting-state fractions use all raw states, including unreachable states. Bounded acceptance mass measures a different quantity.',
             '- Lines show conditional means and can hide dispersion. Consult distributions, exact counts, and companion CSVs, especially in sparse bins.',
             '- Mathematical constraint: agreement is at least min(d/5, 1) for SDS d at H=4. For d>4 both scores must equal one. This is not evidence of language equivalence.',
             '- Generator bias and reachability/minimality limit interpretation of raw state counts; there are no cross-size pair comparisons.',
             '', '## Observed batch summaries','',
             '| Alphabet | States | Finite mean SDS | Positive mean SDS | Equivalent | SDS > 4 | Mean agreement | Mean Jaccard |',
             '|---|---|---|---|---|---|---|---|']
    for r in summary.itertuples():
        lines.append(f'| {r.alphabet} | {r.states} | {r.finite_mean:.4f} | {r.positive_mean:.4f} | {r.equivalent} | {r.beyond_h4} | {r.probability_of_agreement:.4f} | {r.weighted_jaccard:.4f} |')
    lines += ['',f'Observed: {len(perfect)} inequivalent pairs have both H=4 scores equal to one because their SDS exceeds 4. Pair IDs are exported.',
              '', '## Rare long witnesses','']
    for key,g in groups(p[p.length >= 5]):
        ids = sorted(set(g.a).union(g.b))
        lines.append(f'- {label(key)}: {len(g)} pairs with SDS >=5, involving {len(ids)} DFAs: {ids}.')
    lines += ['', '## Focused checks', '', findings, '']
    lines += ['', 'Tail dependence and acceptance composition are exploratory leads; causal explanations and population-level generalizations require further independently generated batches.', '', '## Figure gallery','']
    for name,caption in figures:
        lines += [f'### {name.replace("_"," ")}', '',f'![{name}]({name}.png)', '',caption, '',f'[SVG]({name}.svg)', '']
    lines += ['## Reproduction','', '`python dataviz/analyze.py` from the repository root. The parameter notebook can also be opened from the root or dataviz/.', '',
              'All figures use full data with no random subsampling; seed is recorded for future extensions. CSV tables contain denominators and concrete pair/DFA IDs. Input hashes, package versions, and analysis hash are in provenance.json.', '']
    (output/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Complete: {len(figures)} figures; report at {output / "REPORT.md"}',flush=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-id', default=SOURCE)
    parser.add_argument('--h4-id', default=RESULT4)
    args = parser.parse_args()
    run(args.output,args.source_id,args.h4_id)

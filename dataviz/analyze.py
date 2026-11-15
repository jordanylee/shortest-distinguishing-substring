"""Read saved DFA comparisons, validate joins, and export descriptive figures.

Run: python dataviz/analyze.py
No generation, BFS, or similarity calculations are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
from result_summary import read_jsonl

SOURCE = '2026-11-15_00-36-37-375402_UTC'
RESULT4 = '2026-11-15_17-55-16-095569_UTC'
RESULT3 = '2026-11-15_17-35-18-493520_UTC'
METRICS = {'probability_of_agreement': 'Agreement', 'weighted_jaccard': 'Weighted Jaccard'}
CONFIGS = [(a, s) for a in (2, 3) for s in (10, 20, 30)]
COLORS = dict(zip(CONFIGS, plt.get_cmap('tab10').colors[:6]))


def label(key):
    return f'Alphabet {key[0]}, states {key[1]}'


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


def load_data(source_id=SOURCE, result_id=RESULT4, prior_id=RESULT3):
    frames, dfas, provenance = [], [], []
    for a, s in CONFIGS:
        source = ROOT / 'data' / f'alphabet_{a}' / f'states_{s}' / source_id
        sm = json.loads((source / 'manifest.json').read_text())
        if sm['status'] != 'complete':
            raise ValueError('Incomplete source')
        p, stats, mp = read_result(source, result_id, 4, a, s)
        prior, prior_stats, prior_mp = read_result(source, prior_id, 3, a, s)
        if not p.index.equals(prior.index) or not p.length.equals(prior.length) or not stats.equals(prior_stats):
            raise ValueError('Horizon runs do not match')
        source_rows = list(read_jsonl(source / sm['batch_file']))
        source_stats = pd.DataFrame([{'id': r['id'], 'acceptance_fraction': np.mean(r['acceptance'])} for r in source_rows]).set_index('id', verify_integrity=True)
        if set(source_stats.index) != set(stats.index):
            raise ValueError('Source/stat IDs differ')
        stats = stats.join(source_stats, validate='one_to_one')
        stats['unreachable_fraction'] = 1 - stats.reachable / stats.n_states
        for metric in METRICS:
            p[metric + '_h3'] = prior[metric]
            p[metric + '_delta'] = p[metric] - prior[metric]
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
        for path in [source / 'manifest.json', source / sm['batch_file'], mp, prior_mp,
                     mp.parent / 'pairs.jsonl.gz', mp.parent / 'dfa_stats.jsonl.gz',
                     prior_mp.parent / 'pairs.jsonl.gz', prior_mp.parent / 'dfa_stats.jsonl.gz']:
            provenance.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f'Loaded {label((a,s))}: {len(p):,} matched pairs', flush=True)
    return pd.concat(frames, ignore_index=True), pd.concat(dfas, ignore_index=True), provenance


def run(output=None, source_id=SOURCE, result_id=RESULT4, prior_id=RESULT3, seed=42):
    output = Path(output) if output else ROOT / 'dataviz' / 'outputs' / result_id
    output.mkdir(parents=True, exist_ok=True)
    tables = output / 'tables'
    tables.mkdir(exist_ok=True)
    p, dfas, provenance = load_data(source_id, result_id, prior_id)
    finite = p[p.length.notna()]
    positive = finite[finite.length > 0]
    figures = []
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.alpha': .18, 'savefig.dpi': 180})

    def save(fig, name, caption):
        fig.text(.01, .008, 'Descriptive | H=4 unless labeled | Pairs share DFAs; no independent-pair error bars', fontsize=8, color='#555555')
        fig.tight_layout(rect=(0, .035, 1, .96))
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
        for d, n in zip(range(3, 7), survival[2:]):
            if n: axes[1].annotate(str(n), (d, n / len(g)*100), fontsize=8)
    axes[0].set(xlabel='Positive SDS length', ylabel='% conditional on finite SDS > 0', title='Positive-length distribution')
    axes[1].set(xlabel='Threshold d', ylabel='% of positive finite pairs with SDS >= d', yscale='log', title='Tail survival (labels are pair counts)')
    axes[0].legend(fontsize=8)
    save(fig, 'sds_positive_and_tail', 'Zero lengths and equivalent pairs excluded from both denominators. Log survival reveals the rare tails; labels may overlap at nearby counts, which are available in the distribution table.')

    summary = []
    for key, g in groups(p):
        f = g[g.length.notna()]
        row = dict(alphabet=key[0], states=key[1], pairs=len(g), equivalent=int(g.length.isna().sum()),
                   finite_mean=f.length.mean(), positive_mean=f.loc[f.length > 0, 'length'].mean(), max_sds=f.length.max(),
                   beyond_h4=int((g.length > 4).sum()), beyond_h3=int((g.length > 3).sum()))
        for m in METRICS:
            row[m] = g[m].mean()
            row[m + '_zero'] = int((g[m] == 0).sum())
            row[m + '_one'] = int((g[m] == 1).sum())
            row[m + '_delta'] = g[m + '_delta'].mean()
        row['zero_union'] = int((g.weight_union == 0).sum())
        summary.append(row)
    summary = pd.DataFrame(summary)
    summary.to_csv(tables / 'batch_summary.csv', index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for a, ax in zip((2,3), axes):
        g = summary[summary.alphabet == a]
        x = np.arange(3)
        ax.bar(x-.18, g.finite_mean, width=.36, label='All finite SDS')
        ax.bar(x+.18, g.positive_mean, width=.36, label='Conditional on SDS > 0')
        ax.set(xticks=x, xticklabels=g.states, xlabel='Raw states', ylabel='Mean SDS length', title=f'Alphabet {a}')
        ax.legend()
    save(fig, 'sds_mean_bars', 'Two alphabet panels with raw state counts as bar groups; equivalent pairs excluded. No inferential error bars because pairs share DFAs.')

    fig, axes = facets('Agreement versus weighted Jaccard (H=4)')
    for (key, g), ax in zip(groups(p), axes):
        im = ax.hexbin(g.probability_of_agreement, g.weighted_jaccard, gridsize=40, extent=(0,1,0,1), mincnt=1, bins='log', cmap='viridis')
        ax.set(xlabel='Agreement', ylabel='Weighted Jaccard', xlim=(0,1), ylim=(0,1))
        fig.colorbar(im, ax=ax, label='Pair count (log color)')
    save(fig, 'similarity_joint_density', 'All pairs, including equivalent pairs; hexagon colors show counts on logarithmic scales. Joint rejection contributes to agreement but not to the accepted-word intersection.')

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for metric, column in zip(METRICS, axes.T):
        for key, g in groups(p):
            counts, edges = np.histogram(g[metric], bins=np.linspace(0, 1, 41))
            column[0].stairs(counts / len(g) * 100, edges, color=COLORS[key], label=label(key))
            vals, n = np.unique(g[metric], return_counts=True)
            column[1].step(vals, n.cumsum()/len(g), where='post', color=COLORS[key])
        column[0].set(xlabel=METRICS[metric], ylabel='% of all pairs per bin', title='Score distribution')
        column[1].set(xlabel=METRICS[metric], ylabel='Fraction <= score', title='Empirical cumulative distribution')
    axes[0,0].legend(fontsize=8)
    save(fig, 'similarity_distributions', 'Includes all pairs. Exact zero and one counts and zero-union counts are exported in batch_summary.csv; these masses are not smoothed.')

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
    save(fig, 'acceptance_per_dfa', 'Dots are individual DFAs; black line averages DFAs at each observed fraction. Each mean uses finite partner comparisons, with counts in per_dfa.csv. These dots still share comparison outcomes.')

    for feature, title in [('minimal_min', 'Smaller minimal DFA size'), ('minimal_max','Larger minimal DFA size'),
                           ('minimal_gap','Absolute difference in minimal sizes'), ('unreachable_fraction_mean','Mean unreachable-state fraction')]:
        bins = np.arange(.5, 31.5, 1) if feature in ('minimal_min','minimal_max') else (np.arange(-.5, 31, 1) if feature == 'minimal_gap' else np.linspace(0,1,21))
        binned_lines(feature, 'SDS versus automaton structure', 'sds_vs_' + feature, title, bins)

    fig, axes = facets('Raw, reachable, and minimal sizes of source DFAs')
    for (key, g), ax in zip(groups(dfas), axes):
        ax.hist([g.reachable,g.minimal], bins=np.arange(.5,key[1]+1.5), label=['Reachable','Minimal'], color=['#4899b5','#db8b42'])
        ax.axvline(key[1], color='black', linestyle='--', label='Raw size')
        ax.set(xlabel='State count', ylabel='DFAs')
        ax.legend(fontsize=8)
    save(fig, 'dfa_size_distributions', '500 DFAs per panel. Raw state count overstates effective size for some generated automata; the generator is biased and these are within-batch comparisons.')

    # Matched horizons: p already contains score differences on identical scoped keys.
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    delta_rows = []
    for metric, column in zip(METRICS, axes.T):
        for key, g in groups(p):
            vals = g[metric + '_delta']
            counts, edges = np.histogram(vals, bins=np.linspace(-1,1,101))
            column[0].stairs(counts/len(g)*100, edges, color=COLORS[key], label=label(key))
            agg = g[g.length.notna()].groupby('length')[metric + '_delta'].mean()
            column[1].plot(agg.index, agg, 'o-', color=COLORS[key])
            for group, h in g.groupby('sds_group'):
                d = h[metric + '_delta']
                delta_rows.append(dict(alphabet=key[0],states=key[1],metric=metric,sds_group=group,count=len(d),mean=d.mean(),median=d.median(),minimum=d.min(),maximum=d.max(),decreased=int((d < -1e-12).sum()),unchanged=int((abs(d)<=1e-12).sum()),increased=int((d>1e-12).sum())))
        column[0].set(xlabel=f'{METRICS[metric]}: H=4 minus H=3',ylabel='% of matched pairs per bin', title='Paired score changes')
        column[1].set(xlabel='Finite SDS length',ylabel='Mean paired score change')
        for ax in column: ax.axhline(0,color='black',lw=.7)
    axes[0,0].legend(fontsize=8)
    pd.DataFrame(delta_rows).to_csv(tables / 'matched_horizon_changes.csv',index=False)
    save(fig, 'matched_horizon_changes', 'Same pair matched across runs; not independent samples. H changes both support and weights. Changes can have either sign. The full possible score-change range [-1,1] is retained, including zero-union convention changes.')

    fig, axes = plt.subplots(1,2,figsize=(12,5))
    for metric, ax in zip(METRICS,axes):
        for key,g in groups(p):
            agg = g.groupby(pd.cut(g.acceptance_mass_mean,np.linspace(0,1,21),include_lowest=True),observed=True).agg(x=('acceptance_mass_mean','mean'),y=(metric+'_delta','mean'),count=('a','size'))
            ax.plot(agg.x,agg.y,'o-',ms=3,color=COLORS[key],label=label(key))
        ax.set(xlabel='Mean bounded acceptance mass at H=4',ylabel=f'Mean change in {METRICS[metric]} (H=4 minus H=3)')
        ax.axhline(0,color='black',lw=.7)
    axes[0].legend(fontsize=8)
    save(fig,'horizon_changes_by_acceptance_mass','Acceptance mass is probability of accepting under the sampled word distribution; it differs from the fraction of accepting states.')

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
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    tail_summary = []
    for key,g in groups(p):
        for threshold in (3,4,5,6):
            t = g[g.length >= threshold]
            tail_summary.append(dict(alphabet=key[0],states=key[1],threshold=threshold,pairs=len(t),participating_dfas=len(set(t.a).union(t.b)),percent_all_pairs=len(t)/len(g)*100))
    ts = pd.DataFrame(tail_summary)
    ts.to_csv(tables / 'tail_counts_and_dfas.csv',index=False)
    for key,g in groups(ts):
        axes[0].plot(g.threshold,g.pairs,'o-',color=COLORS[key],label=label(key))
        axes[1].plot(g.threshold,g.participating_dfas,'o-',color=COLORS[key])
    axes[0].set(xlabel='SDS threshold (>=)',ylabel='Pair count',yscale='symlog',title='Rare tail pairs')
    axes[1].set(xlabel='SDS threshold (>=)',ylabel='Unique participating DFAs',title='Tail concentration')
    axes[0].legend(fontsize=8)
    save(fig,'tail_concentration','Unique DFA counts are scoped to each batch. Related tail pairs can arise from the same small group of automata; see tail_dfa_involvement.csv for IDs and effective sizes.')

    metadata = dict(created_utc=datetime.now(timezone.utc).isoformat(),source_id=source_id,h4_results_id=result_id,h3_results_id=prior_id,
                    pairs_h4=len(p),dfas=len(dfas),seed=seed,subsampling='none; all observations used',
                    validation='Manifest counts, unique complete pair keys, scoped IDs, matched SDS/stats, metric identities, SDS agreement bound',
                    python=sys.version,pandas=pd.__version__,numpy=np.__version__,matplotlib=matplotlib.__version__,
                    inputs=provenance,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    lines = ['# DFA exploratory visualization report','',f'Source `{source_id}`; H=4 `{result_id}`; matched H=3 `{prior_id}`.',
             '',f'Validated {len(p):,} pairs at each horizon, in six separate batches of 500 DFAs. No experiment calculations were rerun.',
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
    lines += ['',f'Observed: {int(summary.beyond_h3.sum())} inequivalent pairs are indistinguishable through H=3; {len(perfect)} remain indistinguishable through H=4. Matched pair IDs are exported.',
              '', '## Rare long witnesses','']
    for key,g in groups(p[p.length >= 5]):
        ids = sorted(set(g.a).union(g.b))
        lines.append(f'- {label(key)}: {len(g)} pairs with SDS >=5, involving {len(ids)} DFAs: {ids}.')
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
    parser.add_argument('--h3-id', default=RESULT3)
    args = parser.parse_args()
    run(args.output,args.source_id,args.h4_id,args.h3_id)

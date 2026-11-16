"""Focused descriptive checks for the retained H=4 figures."""
import numpy as np
import pandas as pd


def agreement_histogram(scores, alphabet_size, bins=40):
    """Assign rational agreement scores to [j/bins, (j+1)/bins) exactly."""
    denominator = 5 * alphabet_size ** 4
    numerators = np.rint(np.asarray(scores) * denominator).astype(np.int64)
    if not np.allclose(numerators / denominator, scores, atol=1e-12, rtol=0):
        raise ValueError('Agreement scores do not lie on the expected H=4 grid')
    indices = np.minimum(numerators * bins // denominator, bins - 1)
    counts = np.bincount(indices, minlength=bins)
    assert counts.sum() == len(scores)
    return counts, np.linspace(0, 1, bins + 1)


def investigate(pairs, dfas, tables):
    histogram_rows, grid_rows, contrasts, anomaly_rows, endpoints, influence, cohorts = [], [], [], [], [], [], []
    for (a, s), g in pairs.groupby(['alphabet', 'states']):
        score = g.probability_of_agreement
        denominator = 5 * a ** 4
        n = np.rint(score * denominator).astype(np.int64)
        old, edges = np.histogram(score, bins=np.linspace(0, 1, 41))
        corrected, _ = agreement_histogram(score, a)
        for i in range(40):
            histogram_rows.append(dict(alphabet=a, states=s, bin=i, left=edges[i], right=edges[i+1],
                                       original_count=int(old[i]), exact_count=int(corrected[i]),
                                       original_percent=old[i]/len(g)*100, exact_percent=corrected[i]/len(g)*100))
        for numerator, count in n.value_counts().sort_index().items():
            grid_rows.append(dict(alphabet=a, states=s, numerator=numerator, denominator=denominator,
                                  agreement=numerator/denominator, count=count))
        finite = g[g.length.notna()]
        contrasts.append(dict(alphabet=a, states=s, finite_mean=finite.length.mean(),
                              positive_mean=finite.loc[finite.length > 0, 'length'].mean(),
                              zero_percent=(g.length == 0).mean()*100,
                              positive_pairs=int((g.length > 0).sum())))
        for length, h in finite.groupby('length'):
            no_acceptance = (h.weight_a == 0) | (h.weight_b == 0)
            trivial = h.minimal_min == 1
            for subset, selected in [('all', h), ('neither_DFA_has_zero_H4_acceptance', h[~no_acceptance]),
                                     ('neither_DFA_minimal_size_1', h[~trivial])]:
                anomaly_rows.append(dict(alphabet=a, states=s, length=int(length), subset=subset,
                    pairs=len(selected), distinct_dfas=len(set(selected.a).union(selected.b)),
                    mean_agreement=selected.probability_of_agreement.mean(),
                    mean_jaccard=selected.weighted_jaccard.mean(),
                    jaccard_zero_pairs=int((selected.weighted_jaccard == 0).sum()),
                    mean_union=selected.weight_union.mean()))
            if s == 10 and ((a == 2 and length == 4) or (a == 3 and length == 3)):
                ids = pd.concat([h.a, h.b]).value_counts()
                for dfa_id, count in ids.items():
                    incident = h[(h.a == dfa_id) | (h.b == dfa_id)]
                    remainder = h[(h.a != dfa_id) & (h.b != dfa_id)]
                    endpoints.append(dict(alphabet=a, states=s, length=int(length), id=dfa_id,
                                          comparisons=count, mean_jaccard=incident.weighted_jaccard.mean()))
                    influence.append(dict(alphabet=a, states=s, length=int(length), omitted_dfa=dfa_id,
                                          remaining_pairs=len(remainder), mean_jaccard=remainder.weighted_jaccard.mean()))
                cohort_ids = set(ids[ids == ids.max()].index)
                within = h.a.isin(cohort_ids) & h.b.isin(cohort_ids)
                if len(cohort_ids) >= 3 and within.sum() == len(cohort_ids) * (len(cohort_ids)-1)//2:
                    cohorts.append(dict(alphabet=a, states=s, length=int(length), ids=sorted(cohort_ids),
                                        cohort_pairs=int(within.sum()), cohort_mean=h.loc[within,'weighted_jaccard'].mean(),
                                        other_pairs=int((~within).sum()), other_mean=h.loc[~within,'weighted_jaccard'].mean()))
                h.sort_values('weighted_jaccard').to_csv(tables / f'anomaly_pairs_a{a}_s{s}_d{int(length)}.csv', index=False)

    histogram = pd.DataFrame(histogram_rows)
    histogram.to_csv(tables / 'agreement_bin_audit.csv', index=False)
    pd.DataFrame(grid_rows).to_csv(tables / 'agreement_exact_score_counts.csv', index=False)
    pd.DataFrame(contrasts).to_csv(tables / 'state_count_comparison.csv', index=False)
    anomalies = pd.DataFrame(anomaly_rows)
    anomalies.to_csv(tables / 'similarity_by_sds_sensitivity.csv', index=False)
    pd.DataFrame(endpoints).merge(dfas, on=['alphabet','states','id'], validate='one_to_one').to_csv(
        tables / 'similarity_anomaly_dfas.csv', index=False)
    pd.DataFrame(influence).to_csv(tables / 'anomaly_leave_one_dfa_out.csv', index=False)
    pd.DataFrame(cohorts).to_csv(tables / 'anomaly_repeated_cohorts.csv', index=False)
    lines = ['The state-count means are close, not identical. They compare separately generated batches; these are not the same DFAs with states added. No significance test treating pairs as independent is appropriate.', '',
             'A useful reference model assumes independent fair accept/reject answers for each distinct word. Then P(SDS >= t) = 2^(-(1 + k + ... + k^(t-1))) and the expected SDS is about 0.632843 for k=2 and 0.562622 for k=3. There is no state-count term in that idealization. Actual finite DFAs have repeated states and dependent answers, so this explains why short-depth behavior could dominate without proving state-count invariance for this generator.', '',
             'The agreement oscillation needs a plotting correction. At H=4 every binary agreement score is an integer multiple of 1/80. The old histogram used width 0.025 (=2/80) with floating-point edges. Boundary roundoff can put a boundary score in the wrong adjacent bin, producing artificial peaks and troughs. The retained histogram assigns bins by integer arithmetic, with the same nominal edges.', '',
             '| Alphabet | Generated states | Bins changed by exact assignment (of 40) | Largest bin percentage change |',
             '|---|---|---|---|']
    for (a,s), g in histogram.groupby(['alphabet','states']):
        lines.append(f'| {a} | {s} | {int((g.original_count != g.exact_count).sum())} | {abs(g.original_percent-g.exact_percent).max():.3f} percentage points |')
    lines += ['', 'Exact score counts are retained separately, so discreteness is not hidden by the corrected histogram. The artifact is not specific to the 30-state batch.', '',
              'The 10-state departures in Jaccard are worth inspecting, but SDS does not force Jaccard to increase monotonically. The table below checks whether pairs involving a DFA that accepts no sampled strings drive the dips. The exclusion is a descriptive sensitivity check, not a replacement population or a statistical test.', '',
              '| Alphabet | States | SDS | Subset | Pairs | Mean agreement | Mean Jaccard |',
              '|---|---|---|---|---|---|---|']
    focus = anomalies[(anomalies.states == 10) & (((anomalies.alphabet == 2) & (anomalies.length.isin([3,4]))) | ((anomalies.alphabet == 3) & (anomalies.length.isin([2,3]))))]
    for r in focus.itertuples():
        lines.append(f'| {r.alphabet} | {r.states} | {r.length} | {r.subset} | {r.pairs} | {r.mean_agreement:.4f} | {r.mean_jaccard:.4f} |')
    for c in cohorts:
        lines += ['', f'For alphabet {c["alphabet"]}, {c["states"]} generated states, SDS={c["length"]}: the repeated DFA cohort {c["ids"]} contributes all {c["cohort_pairs"]} internal pairs, with mean Jaccard {c["cohort_mean"]:.4f}. The other {c["other_pairs"]} pairs average {c["other_mean"]:.4f}. This is a concentration of related observations, not independent replication.']
    lines += ['', 'The exported anomaly pair and DFA tables identify repeated automata, effective sizes, acceptance weights, and union/intersection weights. They support structural follow-up without adding another overview figure.']
    return '\n'.join(lines)

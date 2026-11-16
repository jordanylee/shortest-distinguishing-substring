# Focused H=4 findings

Source: `2026-11-15_00-36-37-375402_UTC`. Results: `2026-11-15_17-55-16-095569_UTC`. All findings describe this generated sample. Pairs share DFAs; pair counts are not independent sample sizes.

The trimmed [figure gallery](outputs/2026-11-15_17-55-16-095569_UTC/REPORT.md) contains 13 figures. Minimal-size, unreachable-percentage, tail-concentration, and horizon-change plots were removed. Similarity distributions retain only the two histograms.

## State count has a small effect on the observed SDS distribution

| Alphabet size | Generated states | Average SDS, non-equivalent pairs | Average SDS, positive lengths only |
|---|---|---|---|
| 2 | 10 | 0.634344 | 1.271595 |
| 2 | 20 | 0.634669 | 1.268952 |
| 2 | 30 | 0.633996 | 1.265335 |
| 3 | 10 | 0.569218 | 1.131111 |
| 3 | 20 | 0.562405 | 1.124467 |
| 3 | 30 | 0.561483 | 1.124336 |

The means and proportions are close, not identical. The binary non-equivalent means differ by less than 0.0007 symbols across these batches. The ternary 10-to-30 difference is about 0.0077 symbols (1.36% of its 10-state mean). State count changes much less than alphabet size here, although the rare tails differ. These are separate generated batches, not the same DFAs with states added.

A plausible explanation is that most distinctions arise at very short lengths, before the total number of states matters much. In an idealized model with independent fair accept/reject answers for every word, P(SDS >= t) = 2^(-(1+k+...+k^(t-1))). Summing these probabilities gives expected lengths about 0.632843 for k=2 and 0.562622 for k=3, without a state-count term. These numbers are close to the observations. This reference model is not an exact model of finite DFAs: repeated states and generator structure create dependent answers. It motivates a hypothesis, not a proof of invariance or a significance claim.

## The apparent agreement oscillation was largely a plotting artifact

At H=4 with alphabet size 2, agreement scores lie on the exact grid n/80. The old histogram's width 0.025 equals two grid steps. Floating-point bin edges placed some boundary scores in the wrong adjacent bins, making bins alternate between too many and too few grid values.

For binary/30-state pairs, the old bins at x=0.450 and x=0.475 held 9.185% and 3.102% of pairs. Correct integer assignment gives 6.110% and 6.177%. The effect also occurs in the 10- and 20-state binary batches. This oscillation is not evidence of a special 30-state language phenomenon.

The corrected plot keeps the same nominal score intervals and assigns agreement numerators to bins using integer arithmetic. `agreement_bin_audit.csv` retains original and corrected counts; `agreement_exact_score_counts.csv` retains every observed agreement value and count. Scores remain discrete; the correction does not smooth away their discreteness.

## The 10-state Jaccard dips have concrete structural leads

### Binary alphabet: zero acceptance through H=4 drives much of the dip

Mean Jaccard falls from 0.6234 at SDS=3 (1,124 pairs) to 0.2876 at SDS=4 (68 pairs). Of those 68, **40 involve a DFA that accepts no strings in the H=4 support**, so those comparisons have Jaccard zero. Excluding those 40 raises the SDS=4 mean to **0.6986** across the remaining 28 pairs. Excluding only truly trivial DFAs with minimal size 1 instead leaves 32 pairs with mean 0.6112.

This sensitivity check explains much of the observed dip. It does not justify replacing the original distribution with the filtered one. A DFA accepting no sampled strings need not recognize the empty language.

### Ternary alphabet: a group of eight DFAs drives the dip

Mean Jaccard falls from 0.4755 at SDS=2 (8,077 pairs) to 0.4472 at SDS=3 (77 pairs). The DFAs **227, 279, 313, 340, 350, 360, 364, 426** contribute all 28 internal pairs of their group. Those pairs average Jaccard **0.0981**; the other 49 SDS=3 pairs average **0.6467**. These eight DFAs have minimal sizes 9 or 10, so trivial minimized languages do not explain this case.

Direct inspection of the source DFAs, enumerating the 121 ternary strings of lengths 0 through 4 per DFA, gives these acceptance counts:

| DFA ID | Length 0 | Length 1 | Length 2 | Length 3 | Length 4 |
|---|---|---|---|---|---|
| 227 | 0 | 0 | 0 | 7 | 39 |
| 279 | 0 | 0 | 0 | 3 | 13 |
| 313 | 0 | 0 | 0 | 0 | 4 |
| 340 | 0 | 0 | 0 | 7 | 27 |
| 350 | 0 | 0 | 0 | 2 | 2 |
| 360 | 0 | 0 | 0 | 10 | 30 |
| 364 | 0 | 0 | 0 | 3 | 9 |
| 426 | 0 | 0 | 0 | 6 | 15 |

They agree by rejecting every string through length 2, then accept relatively few and different strings. That combination supports high agreement and low Jaccard. Removing any one of these eight from the SDS=3 group raises its mean above the original SDS=2 mean; the leave-one-DFA-out table records this sensitivity. This is a concentration of related observations worth investigating, rather than independent evidence from 28 unrelated pairs.

## Interpretation

SDS imposes an agreement lower bound of min(d/5, 1) at H=4. It does not force Jaccard to increase monotonically with d. Both 10-state dips are descriptive features of these samples, with concrete explanations to pursue. New independent batches would be needed to determine how consistently the generator produces them.

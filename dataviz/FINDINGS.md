# Initial descriptive findings

These findings use the canonical source run `2026-11-15_00-36-37-375402_UTC`, H=4 results `2026-11-15_17-55-16-095569_UTC`, and matched H=3 results `2026-11-15_17-35-18-493520_UTC`. They describe this generated sample; all-pairs comparisons share DFAs.

The full figure gallery and supporting CSVs are in [the report](outputs/2026-11-15_17-55-16-095569_UTC/REPORT.md).

## Observations

- Mean finite SDS is about 0.634 across binary batches and 0.561–0.569 across ternary batches. Conditional on positive SDS, means are 1.265–1.272 and 1.124–1.131 respectively. Raw state count changes the mean much less than alphabet size in this sample.
- Mean agreement stays near 0.5 in all six configurations. Mean Jaccard varies from 0.3052 to 0.3309. At alphabet 3, the 20-state Jaccard mean (0.3309) exceeds the 30-state mean (0.3224); raw state count has no simple monotone relationship here.
- All nine binary/10-state length-6 pairs involve DFA **458**. Its minimal and reachable sizes are both 10. Each partner has minimal size 1 and zero acceptance mass. Those partners therefore recognize the empty language; the nine comparisons expose the same unusual nonempty language, rather than nine independent long-witness mechanisms. This batch has no length-5 pairs.
- The single binary/20-state length-5 pair is **(50, 131)**. Both minimal sizes are 13. Both accept every word in the H=4 support, so their bounded scores are one even though their full languages differ.
- Among pairs with agreement >=0.8 and Jaccard <=0.2, mean joint-rejection mass ranges from about 0.778 to 0.852 by batch. There are 714 such binary/10-state pairs and only 3 ternary/30-state pairs. Joint rejection explains how these two similarities can diverge; these thresholds are exploratory.
- At H=4 the binary/10-state batch contains 8,584 Jaccard-zero pairs and 45 zero-union pairs. The latter receive Jaccard **one** by convention. All other batches have zero zero-union pairs. Distinguishing these cases matters when interpreting score spikes.

## Mathematical consequences

Under uniform length sampling through H=4, a first distinction at length d forces agreement >= min(d/5, 1). Similarities and SDS cannot be treated as unrelated measurements when interpreting the trend plots.

Exactly 97 inequivalent pairs have SDS >3 and both H=3 scores equal one; 10 have SDS >4 and both H=4 scores equal one. Increasing the horizon exposes 87 previously hidden distinctions. Perfect bounded scores do not establish equivalence.

Changing H also reweights all previously included word lengths. Either similarity may increase or decrease for a matched pair. In particular, Jaccard can drop sharply when a pair with zero union at H=3 first accepts words at H=4; the full change range is retained in the histogram.

## Useful follow-up work

The long-tail concentration suggests inspecting DFA 458's transition structure and the language it accepts. Acceptance composition and effective size deserve follow-up with independently seeded batches before drawing population conclusions. Those would be new experiments; the current visualization workflow reads saved outputs only.

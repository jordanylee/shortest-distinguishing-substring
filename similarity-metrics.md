# Plan: DFA language similarity metrics

Status: implemented November 15, 2026 in `code/similarity_metrics.py`, with shared orchestration in `code/experiments.py` and an interactive entry point in `code/DFA_Comparisons.ipynb` (matching Python companion provided). The specification below records the original plan. Both metrics compare complete DFAs over the same nonempty alphabet using dynamic programming rather than enumerating words.

The canonical SDS experiments were run before the similarity horizon was selected. The notebook therefore requires an explicit `HORIZON` and labels the resulting analysis descriptive. No full similarity experiment has been run. Exact integer counts use the common denominator `(H + 1) * |Sigma|**H`, yielding exact rational weights and scores before conversion to floats for saved results. No floating-point recurrence or external automata dependency was needed.

## 1. Fix the sampling distribution

Choose a nonnegative integer horizon `H` in the experiment configuration **before examining pairwise distinguishing lengths**. Use the same horizon for all pairs in a comparison study, including across state-count groups when their scores will be compared. The numerical value of `H` remains an experiment-design choice.

Initially choose length uniformly from `0, ..., H`, then choose each of its symbols independently and uniformly from the alphabet:

$$
p_t=\frac{1}{H+1},\qquad
W(L)=\sum_{t=0}^{H}p_t\frac{|L\cap\Sigma^t|}{|\Sigma|^t}.
$$

This assigns equal total probability to each length, not to every word across all lengths. Include length zero: `Sigma^0` contains exactly the empty word ε, and `|Sigma|^0 = 1`. If support for custom length weights is added, require exactly `H + 1` finite, nonnegative entries summing to one; record the actual weights. Reject empty alphabets because the positive-length sampling rule is undefined for them.

## 2. Define the inputs and outputs

Add the calculation module under `/code`, for example `code/similarity_metrics.py`, with an entry point such as `calculate_similarity(dfa_a, dfa_b, alphabet, H)`.

- Read the generator's `initial_state`, `transitions`, and `acceptance` fields. Transition columns follow the source manifest's explicit alphabet order.
- Verify that both DFAs have the same symbol set and complete, valid transitions. If their alphabet orders differ, align columns by symbol before comparison. Reject mismatched alphabets or incomplete DFAs.
- Treat symbols as tokens, including labels such as `"10"`; word length counts symbols, not characters in their labels.
- Preserve the generated automata without minimizing or filtering them. Unreachable states need no special handling.

Return at least:

| Field | Meaning |
|---|---|
| `probability_of_agreement` | `1 - weight_symmetric_difference` |
| `weighted_jaccard` | `weight_intersection / weight_union`, or `1` when union weight is zero |
| `weight_a`, `weight_b` | `W(L(A))` and `W(L(B))` |
| `weight_intersection`, `weight_union` | Weighted intersection and union masses |
| `weight_symmetric_difference` | Weighted disagreement mass |
| `distribution` | Distribution name, `H`, length weights or their exact defining rule, alphabet, and uniform symbol-sampling rule |

The experiment runner should attach both DFA IDs and source batch/run identifiers to each saved pair result. Equivalent pairs still receive these metrics.

## 3. Count words on the synchronized product

Let `k = |Sigma|`. A product state `(q, r)` follows the same symbol in both automata:


$$
\delta_\times((q,r),a)=(\delta_A(q,a),\delta_B(r,a)).
$$


Maintain an integer count `c_t(q,r)` of length-`t` words ending in that product state. Initialize one count at the pair of initial states:


$$
c_0(q,r)=\begin{cases}1&(q,r)=(q_{0,A},q_{0,B}),\\0&\text{otherwise}.\end{cases}
$$


For each length, **first** aggregate the current counts by the two acceptance flags, then advance if `t < H`:


$$
c_{t+1}(u,v)=\sum_{(q,r)}\sum_{a\in\Sigma}
c_t(q,r)\,\mathbf{1}\{\delta_\times((q,r),a)=(u,v)\}.
$$


Count each symbol separately even when multiple symbols lead to the same destination. Aggregate into four bins `n00`, `n01`, `n10`, and `n11`, where the bits give A's and B's acceptance flags. Their sum must equal `k^t`.

| Language/event | Number of words at length `t` |
|---|---|
| A | `n10 + n11` |
| B | `n01 + n11` |
| Intersection | `n11` |
| Union | `n01 + n10 + n11` |
| Symmetric difference | `n01 + n10` |
| Agreement | `n00 + n11` |

Multiply each count by `p_t / k^t` and sum over `t = 0, ..., H`. This computes every required weight in one product traversal, without constructing separate intersection, union, or symmetric-difference automata.

Use two rolling count maps or arrays, keeping only the current and next length. With `N = |Q_A| |Q_B|`, the worst case uses `O((H + 1) k N)` arithmetic operations and `O(N)` working entries. Sparse maps can restrict work to states reached so far. Integer counts grow with `H`, so actual arithmetic cost also depends on their bit length.

## 4. Calculate the scores and handle numerical details


$$
\operatorname{Agreement}(A,B)=1-W(L(A)\triangle L(B)),
$$



$$
\operatorname{Jaccard}(A,B)=
\begin{cases}
1,&W(L(A)\cup L(B))=0,\\
\dfrac{W(L(A)\cap L(B))}{W(L(A)\cup L(B))},&\text{otherwise}.
\end{cases}
$$


Use Python integers for exact word counts. For the initial uniform distribution, use exact rational accumulation (for example, `fractions.Fraction`) as a reference implementation and convert to floats only for output. Benchmark before choosing a faster floating-point implementation for bulk runs. If floats are used, accumulate normalized per-length counts with stable summation and validate against the exact reference; determine zero union from whether any positive-weight length has an accepted word, not an arbitrary tolerance.

Check that weights and scores lie in `[0, 1]` within the chosen numerical tolerance. Cross-check:


$$
W(A\cup B)=W(A)+W(B)-W(A\cap B),
$$


$$
W(A\triangle B)=W(A)+W(B)-2W(A\cap B).
$$


Calculate disagreement directly from its bins, using the identities as checks. This avoids subtracting nearly equal masses to obtain a small disagreement.

## 5. Validate against exhaustive enumeration

Add small tests under `/code` before connecting the metrics to bulk experiments. The independent oracle enumerates all symbol tuples for `t = 0, ..., H`, runs each DFA directly, and applies the specified distribution. Include the empty tuple. Use tiny alphabets and horizons so enumeration stays small.

Cover these cases with exact expected values where practical:

- **Identical DFAs and differently structured equivalent DFAs:** agreement and Jaccard are both `1`; marginal weights agree.
- **Complementary languages:** agreement is `0`, intersection weight is `0`, union weight is `1`, and Jaccard is `0`.
- **Two empty languages:** both marginal weights and union weight are `0`; agreement and the zero-union Jaccard convention both give `1`.
- **Empty versus universal language:** agreement and Jaccard are `0`; marginal weights are `0` and `1`.
- **Empty versus a partly accepting language:** agreement is `1 - W(B)` and Jaccard is `0` when `W(B) > 0`.
- **Horizon zero:** scores depend only on the initial acceptance flags. Two rejecting initial states give zero union even if their languages contain longer words.
- **A distinction at ε:** initial acceptance differs, so disagreement includes at least `p_0`.
- **A distinction beyond H:** both scores can be `1` even though the languages are not equivalent. Include a nonempty language with no accepted words through `H` to exercise zero union under this distribution.
- **Transition details:** unary alphabets, multiple symbols sharing a destination, token labels such as `"10"`, and equivalent alphabets with different column orders.
- **Input validation:** mismatched or empty alphabets, incomplete transitions, invalid destinations, and negative or noninteger horizons.

Also compare several seeded tiny random pairs against enumeration. Check symmetry under swapping A and B, the per-length total `k^t`, and both weight identities. Record chosen numerical tolerances if any float implementation is used.

## 6. Integrate into the pairwise experiments

1. Implement and validate the standalone calculation and enumeration oracle.
2. Select and record `H` before the production comparisons. If exploring several horizons, preselect that list and report results separately for each distribution.
3. Calculate these metrics for every unique unordered pair in each approved batch, using the same pair IDs as the shortest-distinguishing-length results. Save outputs in `/data` and record the metric definition/version in experiment metadata.
4. Keep the similarity calculation independent of shortest-distinguishing BFS. Even if BFS finds an early distinction, continue the metric DP through `H`; do not use that distinction to set the horizon or stop the counts.
5. Benchmark a representative batch before the all-pairs run. Metric cost scales with `H` and may exceed the early-terminating shortest-length search. Consider cached product transitions or a validated probability-mass recurrence only if measurements justify them.

## 7. Interpret the results

These are similarities under the chosen word distribution, not horizon-independent language equivalence tests. Agreement includes both jointly accepted and jointly rejected words; Jaccard focuses on accepted words through the weighted union. The marginal weights help explain cases where agreement is high because both languages rarely accept.

Treat correlations with shortest distinguishing length as descriptive. If the first distinguishing length is `d`, all lengths below `d` necessarily agree; when `d <= H`, agreement is at least `sum(p_t for t < d)`. When `d > H`, both scores are `1` despite inequivalence. Equivalent pairs have no finite distinguishing length and must not be assigned zero. Comparisons sharing a DFA remain dependent observations, as in the existing experimental plan.

## Reuse candidates supplied for this plan

The following are leads from the preliminary search supplied with the request, not dependencies selected or implementations executed as part of this planning task:

- [automata-lib DFA API](https://caleb531.github.io/automata/api/fa/class-dfa/): candidate primitives for Boolean language operations and counts by length. Evaluate it as an adapter/reference option; the project's saved transition tables also support the direct single-pass product DP above.
- [AppReAL probabilistic_distance.py](https://github.com/vhavlena/appreal/blob/master/reduce/probabilistic_distance.py): supplied reference for weighted disagreement via `W(A) + W(B) - 2W(A intersection B)`. The preliminary notes flag legacy Python 2 and require `OPTIMISATION = 0` for arbitrary pairs rather than the default reduction-specific assumption.
- [SemMT Toolkits.py](https://github.com/ArabelaTso/SemMT/blob/main/code_book/Toolkits.py): supplied related bounded-count Jaccard implementation through `DFASimilarity.jar`; its weighting must not be assumed to match this plan.

The preliminary search reported no ready-made implementation of exactly this distribution-weighted Jaccard. Verify any external code and its assumptions before reuse; no external package is required for the proposed count recurrence.

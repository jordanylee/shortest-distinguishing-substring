"""Exact bounded-distribution language similarity; see ../similarity-metrics.md."""

from fractions import Fraction

from loader import AlphabetMismatchError, DFA

WEIGHT_FIELDS = ("weight_a", "weight_b", "weight_intersection", "weight_union",
                 "weight_symmetric_difference")
SCORE_FIELDS = ("probability_of_agreement", "weighted_jaccard")
METRIC_FIELDS = SCORE_FIELDS + WEIGHT_FIELDS


def validate_horizon(horizon):
    if type(horizon) is not int or horizon < 0:
        raise ValueError("horizon must be a nonnegative integer (set HORIZON in the notebook)")


def distribution(alphabet, horizon):
    validate_horizon(horizon)
    return {"name": "uniform_length_uniform_symbols", "horizon": horizon,
            "length_weights": "p(t) = 1 / (H + 1), t = 0, ..., H",
            "alphabet": list(alphabet), "symbol_sampling": "independent uniform",
            "numerical_method": "exact integer counts and rational accumulation",
            "metric_version": 1}


def _alphabet(symbols):
    symbols = tuple(symbols)
    if not symbols or any(not isinstance(s, str) for s in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError("alphabet must contain distinct string symbols and be nonempty")
    return symbols


def _validate_dfa(d, k):
    n = len(d.delta)
    if not n or len(d.accept) != n or any(type(f) is not bool for f in d.accept):
        raise ValueError("DFA must have states and one Boolean acceptance flag per state")
    if type(d.initial) is not int or not 0 <= d.initial < n:
        raise ValueError("invalid initial state")
    for row in d.delta:
        if len(row) != k:
            raise AlphabetMismatchError("transition width does not match alphabet")
        if any(type(dst) is not int or not 0 <= dst < n for dst in row):
            raise ValueError("invalid transition destination")


def calculate_similarity(a: DFA, b: DFA, alphabet, horizon, *, alphabet_b=None, check=True):
    """Return exact Fraction scores/weights, plus the distribution definition.

    alphabet_b describes B's column order when it differs from A's. check=False is
    only for batches already validated by the loader, with identical column order.
    Counts use a common denominator (H+1)*k**H, avoiding per-step Fraction overhead.
    """
    validate_horizon(horizon)
    symbols = _alphabet(alphabet)
    k = len(symbols)
    if check:
        other = symbols if alphabet_b is None else _alphabet(alphabet_b)
        if set(other) != set(symbols):
            raise AlphabetMismatchError("DFAs must have the same alphabet")
        _validate_dfa(a, k)
        _validate_dfa(b, k)
        if other != symbols:
            columns = [other.index(s) for s in symbols]
            b = DFA(b.id, tuple(tuple(row[i] for i in columns) for row in b.delta),
                    b.accept, b.initial)
    elif alphabet_b is not None:
        raise ValueError("alphabet_b requires check=True")

    counts = {(a.initial, b.initial): 1}
    totals = [0, 0, 0, 0]
    scale = k ** horizon
    denominator = (horizon + 1) * scale
    for t in range(horizon + 1):
        bins = [0, 0, 0, 0]
        for (p, q), count in counts.items():
            bins[2 * a.accept[p] + b.accept[q]] += count
        for i in range(4):
            totals[i] += bins[i] * scale
        if t == horizon:
            break
        following = {}
        for (p, q), count in counts.items():
            for s in range(k):
                dest = (a.delta[p][s], b.delta[q][s])
                following[dest] = following.get(dest, 0) + count
        counts = following
        scale //= k

    n00, n01, n10, n11 = totals
    union = n01 + n10 + n11
    return {"probability_of_agreement": Fraction(n00 + n11, denominator),
            "weighted_jaccard": Fraction(n11, union) if union else Fraction(1),
            "weight_a": Fraction(n10 + n11, denominator),
            "weight_b": Fraction(n01 + n11, denominator),
            "weight_intersection": Fraction(n11, denominator),
            "weight_union": Fraction(union, denominator),
            "weight_symmetric_difference": Fraction(n01 + n10, denominator),
            "distribution": distribution(symbols, horizon)}

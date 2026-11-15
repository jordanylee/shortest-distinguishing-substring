"""Shortest distinguishing string between two DFAs via BFS over the product automaton."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass

from loader import DFA, AlphabetMismatchError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Result:
    length: int | None               # None means equivalent
    witness: tuple[int, ...] | None  # symbol indices; convert to strings at write time


EQUIVALENT = Result(None, None)


def _check_width(d: DFA, n_symbols: int, label: str) -> None:
    for state, row in enumerate(d.delta):
        if len(row) != n_symbols:
            msg = (f"DFA id={d.id} ({label}) state {state} has {len(row)} transitions, "
                   f"expected {n_symbols}")
            log.error(msg)
            raise AlphabetMismatchError(msg)


def _check_start(d: DFA, state: int, label: str) -> None:
    if len(d.accept) != len(d.delta):
        raise ValueError(f"DFA id={d.id} ({label}) has {len(d.delta)} transition rows "
                         f"but {len(d.accept)} acceptance flags")
    if not 0 <= state < len(d.delta):
        raise ValueError(f"DFA id={d.id} ({label}) start state {state} out of range "
                         f"0..{len(d.delta) - 1}")


def shortest_distinguishing(a: DFA, b: DFA, n_symbols: int, check: bool = True) -> Result:
    return shortest_distinguishing_from(a, a.initial, b, b.initial, n_symbols, check=check)


def shortest_distinguishing_from(a: DFA, p0: int, b: DFA, q0: int, n_symbols: int,
                                 check: bool = True) -> Result:
    """BFS from state pair (p0, q0); return the shortlex-smallest distinguishing string.

    Symbols are expanded in index order and pairs are marked visited at first enqueue,
    so the first mismatching pair dequeued yields the lexicographically smallest
    shortest witness.

    `check=False` skips the per-call input validation; pass it only for DFAs that were
    already validated against `n_symbols` (e.g. by `load_batch`).
    """
    if check:
        _check_width(a, n_symbols, "a")
        _check_width(b, n_symbols, "b")
        _check_start(a, p0, "a")
        _check_start(b, q0, "b")

    da, db = a.delta, b.delta
    fa, fb = a.accept, b.accept
    nb = len(db)

    start = p0 * nb + q0
    # parent[k] = (previous key, symbol index); None marks unvisited. Start points to itself.
    parent: list[tuple[int, int] | None] = [None] * (len(da) * nb)
    parent[start] = (-1, -1)
    queue = deque([start])
    while queue:
        key = queue.popleft()
        p, q = divmod(key, nb)
        if fa[p] != fb[q]:
            symbols = []
            while key != start:
                prev, s = parent[key]
                symbols.append(s)
                key = prev
            symbols.reverse()
            return Result(len(symbols), tuple(symbols))
        rp, rq = da[p], db[q]
        for s in range(n_symbols):
            nk = rp[s] * nb + rq[s]
            if parent[nk] is None:
                parent[nk] = (key, s)
                queue.append(nk)
    return EQUIVALENT

"""Per-DFA statistics: reachable-state count and minimal-DFA size."""

from __future__ import annotations

from collections import deque

from loader import DFA


def reachable_states(d: DFA) -> frozenset[int]:
    seen = {d.initial}
    queue = deque([d.initial])
    while queue:
        p = queue.popleft()
        for dst in d.delta[p]:
            if dst not in seen:
                seen.add(dst)
                queue.append(dst)
    return frozenset(seen)


def minimal_size(d: DFA, n_symbols: int) -> int:
    """Number of states of the minimal complete DFA (Moore partition refinement).

    Only reachable states are considered. A reachable dead/sink state counts as a state.
    """
    states = sorted(reachable_states(d))
    # Initial partition by acceptance flag; block ids are small ints.
    block = {p: int(d.accept[p]) for p in states}
    n_blocks = len(set(block.values()))
    while True:
        signatures: dict[tuple, int] = {}
        new_block = {}
        for p in states:
            sig = (block[p],) + tuple(block[d.delta[p][s]] for s in range(n_symbols))
            new_block[p] = signatures.setdefault(sig, len(signatures))
        if len(signatures) == n_blocks:
            return n_blocks
        block, n_blocks = new_block, len(signatures)

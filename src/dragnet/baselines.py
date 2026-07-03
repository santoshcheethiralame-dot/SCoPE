"""Game-theoretic baselines over the same subset game.

Additive attributions are the thing set-valued attribution subsumes. The blindness is exact:
on a redundant OR-cover and on a joint AND-pair, Shapley hands each member the same one-half —
the per-passage numbers are identical across the two structures, so no ranking of them can say
"either alone" versus "only together". The order-2 surrogate separates the cases by the sign of
the pairwise term; these baselines are here so the comparison runs on the same cached game,
with the same query accounting.

Exact values enumerate the lattice once (2^n queries, shared with everything else through the
cache) and are the right choice at benchmark scale; the permutation sampler covers wider
contexts. Token-level Shapley and sparse-Fourier surrogates change the unit or target hundreds
of features — cited as related work, not re-implemented for ten-passage games.
"""
from __future__ import annotations

import random
from itertools import chain, combinations
from math import factorial
from typing import Iterable

from .game import Game


def _lattice(game: Game) -> dict[frozenset, float]:
    if len(game.ids) > 12:
        raise ValueError(f"exact values enumerate 2^{len(game.ids)} subsets; use sampled_shapley")
    subsets = chain.from_iterable(combinations(game.ids, size) for size in range(len(game.ids) + 1))
    return {frozenset(combo): float(game.reproduces(frozenset(combo))) for combo in subsets}


def exact_shapley(game: Game) -> dict[str, float]:
    """The Shapley value of every passage, exactly. Satisfies efficiency: the values sum to
    v(full) - v(empty), which for a wrong case is the whole unit of blame — split, however the
    structure distributes it, into per-passage shares."""
    values = _lattice(game)
    n = len(game.ids)
    shapley = {}
    for cid in game.ids:
        total = 0.0
        for subset, value in values.items():
            if cid in subset:
                continue
            weight = factorial(len(subset)) * factorial(n - 1 - len(subset)) / factorial(n)
            total += weight * (values[subset | {cid}] - value)
        shapley[cid] = total
    return shapley


def exact_banzhaf(game: Game) -> dict[str, float]:
    """The Banzhaf value: the mean marginal contribution over all subsets, exactly."""
    values = _lattice(game)
    n = len(game.ids)
    scale = 1.0 / 2 ** (n - 1)
    return {
        cid: scale * sum(values[subset | {cid}] - value for subset, value in values.items() if cid not in subset)
        for cid in game.ids
    }


def exact_shapley_interaction(game: Game) -> dict[frozenset, float]:
    """The pairwise Shapley interaction index — the classical, kernel-weighted counterpart of
    the surrogate's pairwise terms: negative on redundancy, positive on joint support."""
    values = _lattice(game)
    n = len(game.ids)
    interactions = {}
    for one, other in combinations(game.ids, 2):
        total = 0.0
        for subset, value in values.items():
            if one in subset or other in subset:
                continue
            weight = factorial(len(subset)) * factorial(n - len(subset) - 2) / factorial(n - 1)
            total += weight * (
                values[subset | {one, other}] - values[subset | {one}] - values[subset | {other}] + value
            )
        interactions[frozenset((one, other))] = total
    return interactions


def sampled_shapley(game: Game, n_permutations: int = 32, seed: int = 0) -> dict[str, float]:
    """Permutation-sampling Shapley for contexts too wide to enumerate. Each permutation walks
    its prefixes, so early prefixes are shared across permutations through the game cache."""
    rng = random.Random(seed)
    ids = list(game.ids)
    totals = {cid: 0.0 for cid in ids}
    for _ in range(n_permutations):
        order = ids[:]
        rng.shuffle(order)
        previous = float(game.reproduces(frozenset()))
        prefix: set = set()
        for cid in order:
            prefix.add(cid)
            current = float(game.reproduces(frozenset(prefix)))
            totals[cid] += current - previous
            previous = current
    return {cid: total / n_permutations for cid, total in totals.items()}


def ranking(values: dict[str, float]) -> list[str]:
    """Most-responsible-first order for the extraction and conformal machinery, with a stable
    tie-break so equal shares never shuffle between runs."""
    return sorted(values, key=lambda cid: (-round(values[cid], 9), cid))

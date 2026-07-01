"""Split-conformal attribution sets over a sufficient-set family.

The benchmark's conformal layer calibrates a rank threshold for the single culprit — and must
skip the no-single-cause coalitions, since no single-removal signal places them. Generalizing
the nonconformity from the culprit's rank to the *prefix depth that covers a sufficient set*
removes that blind spot: a redundant pair has a finite depth (the later of its two members) even
though neither member is singly causal. A singleton family reduces the depth to exactly the
culprit's rank, so the benchmark's machinery is the size-1 corner of this one.

The guarantee is marginal over exchangeable cases. Orders must be built without looking at the
family — the presented order, a method's score ranking, and the sampled interaction surrogate
all qualify.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass
class DepthItem:
    key: str
    depth: int | None      # smallest covering prefix; None when no prefix ever covers
    n_chunks: int


def required_depth(order: Iterable[str], family: Iterable[frozenset]) -> int | None:
    """The smallest k such that the first k passages of ``order`` contain a member of ``family``.

    An empty member (the parametric case: the empty context already suffices) gives depth 0; a
    family no prefix covers gives None — an infinite nonconformity, never a silent drop.
    """
    order = list(order)
    position = {cid: index for index, cid in enumerate(order)}
    best: int | None = None
    for member in family:
        if not member:
            return 0
        if not all(cid in position for cid in member):
            continue
        depth = 1 + max(position[cid] for cid in member)
        if best is None or depth < best:
            best = depth
    return best


def depth_item(key: str, order: Iterable[str], family: Iterable[frozenset]) -> DepthItem:
    order = list(order)
    return DepthItem(key=key, depth=required_depth(order, family), n_chunks=len(order))


def calibrate_depth(calibration: list[DepthItem], alpha: float) -> float | None:
    """The split-conformal (n+1)(1-alpha) order statistic of the calibration depths.

    Uncoverable calibration cases count as infinite — they push tau up (possibly to inf, meaning
    "return the full context") rather than silently leaving the guarantee overstated. None only
    when there is no calibration data at all.
    """
    scores = sorted(math.inf if item.depth is None else item.depth for item in calibration)
    n = len(scores)
    if n == 0:
        return None
    index = min(math.ceil((n + 1) * (1 - alpha)), n)
    return float(scores[index - 1])


def coverage_and_size(test: list[DepthItem], tau: float):
    """Empirical coverage of the depth-tau prefix and its mean size (capped per case at the
    context length, which is also what an infinite tau falls back to)."""
    if not test:
        return None, None
    covered = sum(1 for item in test if item.depth is not None and item.depth <= tau) / len(test)
    size = sum(min(tau, item.n_chunks) for item in test) / len(test)
    return covered, size


def top1_coverage(test: list[DepthItem]) -> float | None:
    """Coverage of the single top pick — the size-1 prefix every current method returns."""
    if not test:
        return None
    return sum(1 for item in test if item.depth == 1) / len(test)

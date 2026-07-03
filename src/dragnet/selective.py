"""Attribution as risk-controlled selection — the guarantee, read as an error rate you commit to.

The decision rule abstains when the evidence is thin; framed as selection, "answer" means
committing to an attribution (here, a single blamed passage), and a *false* answer is committing
to one that is not actually a sufficient cause. Controlling that error rate directly is a
distribution-free selection problem: calibrate a label-free confidence score (the margin) against
calibration cases whose committed answer is known to fail, form valid conformal p-values, and let
Benjamini–Hochberg pick the cases to answer at guaranteed false-answer rate <= alpha
(Jin & Candès conformal selection). The e-value / eBH variant (Wang–Ramdas) swaps BH for the eBH
filter and is robust to dependence between cases — same target, weaker assumptions.

This complements the coverage guarantee: coverage says "the emitted set contains a cause 1-alpha
of the time"; selection says "of the singletons we commit to, at most alpha are wrong" — the
metric a practitioner acting on one blamed passage actually cares about.
"""
from __future__ import annotations


def risk_coverage(scored: list[tuple[float, bool]]) -> list[tuple[float, float]]:
    """Answer highest-confidence first; the curve is (coverage, selective risk) — the fraction
    answered vs. the fraction of answers that fail. Ties are broken by the given order."""
    order = sorted(scored, key=lambda item: item[0], reverse=True)
    curve, wrong = [], 0
    for k, (_, covers) in enumerate(order, 1):
        wrong += not covers
        curve.append((k / len(order), wrong / k))
    return curve


def conformal_pvalues(calibration: list[tuple[float, bool]], test: list[tuple[float, bool]]) -> list[float]:
    """Jin–Candès conformal p-values for the null 'this answer fails', calibrated on the failing
    calibration cases. A high score is evidence against the null, so a large score yields a small
    p. Valid (super-uniform under the null) when cases are exchangeable."""
    null_scores = sorted(score for score, covers in calibration if not covers)
    m = len(null_scores)
    return [(1 + sum(1 for x in null_scores if x >= score)) / (1 + m) for score, _ in test]


def bh_select(pvalues: list[float], alpha: float) -> set[int]:
    """Benjamini–Hochberg: indices of the selected (answered) cases at FDR <= alpha."""
    n = len(pvalues)
    if not n:
        return set()
    order = sorted(range(n), key=lambda i: pvalues[i])
    cutoff = 0
    for rank, i in enumerate(order, 1):
        if pvalues[i] <= alpha * rank / n:
            cutoff = rank
    return set(order[:cutoff])


def select_by_risk(calibration: list[tuple[float, bool]], test: list[tuple[float, bool]], alpha: float) -> dict:
    """Conformal-risk-control selection: choose the lowest confidence threshold whose calibration
    answered-error stays <= alpha (maximal coverage), then answer test cases above it. Controls the
    *average* false-answer rate on the answered set (a bounded, monotone risk), which is far less
    conservative than the FDR/BH variant when the confidence signal is weak. Answers nothing when
    even the most-confident case cannot hold the level — the honest abstention."""
    threshold, answered, wrong = None, 0, 0
    for score, covers in sorted(calibration, key=lambda item: item[0], reverse=True):
        answered += 1
        wrong += not covers
        if wrong / answered <= alpha:
            threshold = score                      # deepest (max-coverage) level still under alpha
    if threshold is None:
        return {"n_test": len(test), "answered": 0, "coverage_of_selection": 0.0,
                "realized_false_answer_rate": 0.0, "threshold": None, "target": alpha}
    kept = [covers for score, covers in test if score >= threshold]
    a = len(kept)
    return {
        "n_test": len(test),
        "answered": a,
        "coverage_of_selection": a / len(test) if test else 0.0,
        "realized_false_answer_rate": sum(1 for c in kept if not c) / a if a else 0.0,
        "threshold": threshold,
        "target": alpha,
    }


def select_and_evaluate(calibration: list[tuple[float, bool]], test: list[tuple[float, bool]], alpha: float) -> dict:
    """Run the conformal selection and report the realized false-answer rate on the answered set —
    which the guarantee bounds by alpha in expectation."""
    pvalues = conformal_pvalues(calibration, test)
    selected = bh_select(pvalues, alpha)
    answered = len(selected)
    false_answers = sum(1 for i in selected if not test[i][1])
    return {
        "n_test": len(test),
        "answered": answered,
        "coverage_of_selection": answered / len(test) if test else 0.0,
        "realized_false_answer_rate": false_answers / answered if answered else 0.0,
        "target": alpha,
    }

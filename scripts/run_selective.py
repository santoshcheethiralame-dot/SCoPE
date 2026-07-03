"""Risk-controlled selection over the natural cells — CPU only, no model.

Frames single-passage attribution as selection: commit to the top-ranked passage as the blamed
cause when confident (high margin), abstain otherwise, and control the rate at which a committed
passage is not actually a sufficient cause. Reports the risk-coverage curve and the conformal
selection at each alpha, with the realized false-answer rate that the guarantee bounds.

    python scripts/run_selective.py --cells path/to/natural/qwen path/to/natural/phi ...
"""
import argparse
import random
from pathlib import Path

from _cells import load_cases
from dragnet.designed import set_covers
from dragnet.selective import risk_coverage, select_by_risk


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cells", type=Path, nargs="+", required=True)
    parser.add_argument("--alphas", type=float, nargs="+", default=[0.1, 0.2, 0.3, 0.4])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = parser.parse_args()

    # One point per wrong case: the label-free confidence (contextcite margin) and whether the
    # top-ranked passage alone is a sufficient cause (the committed singleton is correct).
    scored = []
    for cell in args.cells:
        for case in load_cases(cell, "mscs"):
            if case.ranking is None or not case.family:
                continue
            covers = set_covers(frozenset({case.ranking[0]}), case.family)
            scored.append((case.margin, covers))
    print(f"cases with a ranking and a family: {len(scored)}")
    base_rate = sum(1 for _, c in scored if c) / len(scored)
    print(f"base singleton-correct rate (answer everything): {base_rate:.2f}  "
          f"-> naive false-answer rate {1 - base_rate:.2f}")

    print("\nrisk-coverage curve (pooled, by margin):")
    curve = risk_coverage(scored)
    for target_cov in (0.2, 0.3, 0.5, 0.7):
        point = min(curve, key=lambda cr: abs(cr[0] - target_cov))
        print(f"  coverage {point[0]:.2f}  selective risk {point[1]:.2f}")
    floor = min(risk for _, risk in curve if _ >= 0.1)   # best achievable singleton error at >=10% coverage
    print(f"  --> singleton error floor (best any gating achieves): {floor:.2f}  "
          f"-- below this alpha, committing to one passage is impossible; use the set.")

    print("\nrisk-controlled singleton selection (seeded cal/test halves, mean over seeds):")
    for alpha in args.alphas:
        covs, risks = [], []
        for seed in args.seeds:
            shuffled = list(scored)
            random.Random(seed).shuffle(shuffled)
            half = len(shuffled) // 2
            report = select_by_risk(shuffled[:half], shuffled[half:], alpha=alpha)
            covs.append(report["coverage_of_selection"])
            risks.append(report["realized_false_answer_rate"])
        mean_cov = sum(covs) / len(covs)
        mean_risk = sum(risks) / len(risks)
        print(f"  alpha={alpha}  answered {mean_cov:.2f} of cases  realized false-answer rate "
              f"{mean_risk:.2f} (target {alpha})" + ("   [abstains entirely]" if mean_cov == 0 else ""))


if __name__ == "__main__":
    main()

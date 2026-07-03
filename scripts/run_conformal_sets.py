"""Conformal attribution sets over existing run cells — CPU only, no model.

Pools the wrong cases of the given cells, derives each case's target family, and calibrates a
prefix-depth threshold per ranking arm on a seeded half split. Reports, per arm: tau, test
coverage, mean set size, and the top-1 coverage the guarantee improves on.

Two family modes. ``designed`` covers the planted carriers (designed.jsonl, else retrofitted
from the recipe). ``behavioral`` covers the responsible sets the model actually exhibits: the
leave-one-out causal passages from roles.jsonl as singletons, plus the jointly-necessary pairs
the leave-two-out probe recorded in coalition_proof.jsonl — which is what gives the
no-single-cause coalitions a finite nonconformity instead of being skipped. Cases whose family
is empty count as uncoverable (infinite depth), disclosed rather than dropped.

Arms are rankings that exist on disk: the presented passage order (blind floor) and
ContextCite's score ranking from predictions.jsonl. The interaction-guided arm needs the model,
so it lives with the GPU runners.

    python scripts/run_conformal_sets.py --alpha 0.1 --family behavioral \\
        --cells path/to/results_data/hotpotqa/hardtraps/qwen path/to/...
"""
import argparse
import random
from pathlib import Path

from lineup.stats import percentile_interval

from _cells import load_cases
from dragnet.conformal import calibrate_depth, coverage_and_size, depth_item, top1_coverage


def _coverage_interval(test, tau, n_boot: int, rng: random.Random):
    draws = []
    for _ in range(n_boot):
        sample = [test[rng.randrange(len(test))] for _ in test]
        covered, _ = coverage_and_size(sample, tau)
        draws.append(covered)
    return percentile_interval(draws)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cells", type=Path, nargs="+", required=True)
    parser.add_argument("--alpha", type=float, nargs="+", default=[0.1])
    parser.add_argument("--family", choices=("designed", "behavioral", "fixer", "mscs"), default="behavioral")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--bootstrap", type=int, default=1000, help="case resamples for the coverage CI (0 = off)")
    args = parser.parse_args()

    items = {"presented": [], "contextcite": []}
    total = uncoverable = pair_rescued = 0
    for cell in args.cells:
        for case in load_cases(cell, args.family):
            total += 1
            if not case.family:
                uncoverable += 1
            elif not any(len(member) == 1 for member in case.family):
                pair_rescued += 1
            items["presented"].append(depth_item(case.key, case.presented, case.family))
            if case.ranking is not None:
                items["contextcite"].append(depth_item(case.key, case.ranking, case.family))

    print(
        f"family={args.family}  cases={total}  empty-family={uncoverable}  "
        f"pairs-only (rescued from skipping)={pair_rescued}"
    )
    for arm, arm_items in items.items():
        for alpha in args.alpha:
            for seed in args.seeds:
                shuffled = list(arm_items)
                rng = random.Random(seed)
                rng.shuffle(shuffled)
                half = len(shuffled) // 2
                calibration, test = shuffled[:half], shuffled[half:]
                tau = calibrate_depth(calibration, alpha=alpha)
                if tau is None:
                    print(f"{arm:12s} no data")
                    continue
                covered, size = coverage_and_size(test, tau)
                top1 = top1_coverage(test)
                interval = ""
                if args.bootstrap:
                    low, high = _coverage_interval(test, tau, args.bootstrap, random.Random(seed))
                    if low is not None:
                        interval = f" [{low:.2f}, {high:.2f}]"
                tau_label = "inf" if tau == float("inf") else f"{tau:.0f}"
                print(
                    f"{arm:12s} alpha={alpha:.2f} seed={seed}  n_test={len(test):4d}  tau={tau_label:>3s}  "
                    f"coverage {covered:.2f}{interval} (target {1 - alpha:.2f})  mean-size {size:.1f}  top-1 {top1:.2f}"
                )


if __name__ == "__main__":
    main()

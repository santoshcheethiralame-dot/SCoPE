"""Compare extraction orders on a run cell: coverage of the designed set vs queries spent.

Three arms per wrong case, each on a fresh game so budgets are honest:
  presented    — grow-prune in the order the passages were shown (the blind floor)
  contextcite  — grow-prune ranked by ContextCite's scores from predictions.jsonl (order-1 guide)
  interaction  — sample an order-2 surrogate, rank by interaction_order (the SCoPE guide);
                 its query count includes the sampling masks, not just the search

Reports, per arm: sufficient-set rate, designed-set coverage (set_covers), mean set size, mean
queries. The coverage-vs-budget comparison is the seed of the efficiency figure.

    python scripts/run_extraction.py --cell runs/hotpotqa/and/qwen \\
        --model Qwen/Qwen2.5-7B-Instruct --load-in-4bit --n-samples 48
"""
import argparse
from pathlib import Path

from lineup.data.coalition import from_recipe, read_designed
from lineup.data.serialization import read_generations, read_predictions, read_scenarios

from scope.designed import designed_family, set_covers
from scope.extract import grow_prune
from scope.interactions import interaction_order, sampled_effects
from scope.model_game import scenario_game


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cell", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--n-samples", type=int, default=48, help="surrogate masks for the interaction arm")
    parser.add_argument("--budget", type=int, default=0, help="query cap per extraction; 0 = none")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    scenarios = {s.qid: s for s in read_scenarios(args.cell / "scenarios.jsonl")}
    wrong = [g for g in read_generations(args.cell / "generations.jsonl") if not g.is_correct]
    if args.limit:
        wrong = wrong[: args.limit]

    designed_path = args.cell / "designed.jsonl"
    if designed_path.exists():
        designed = {d.qid: d for d in read_designed(designed_path)}
    else:
        designed = {qid: d for qid, s in scenarios.items() if (d := from_recipe(s)) is not None}

    contextcite = {}
    predictions_path = args.cell / "predictions.jsonl"
    if predictions_path.exists():
        for prediction in read_predictions(predictions_path):
            if prediction.method == "contextcite":
                ranked = sorted(prediction.chunk_scores, key=lambda s: s.score, reverse=True)
                contextcite[prediction.qid] = [score.chunk_id for score in ranked]

    from lineup.backends import TransformersModel

    model = TransformersModel(args.model, load_in_4bit=args.load_in_4bit)
    budget = args.budget or None

    arms = ["presented", "contextcite", "interaction"]
    tallies = {arm: {"n": 0, "sufficient": 0, "covered": 0, "size": 0, "queries": 0} for arm in arms}
    for index, generation in enumerate(wrong):
        scenario, planted = scenarios.get(generation.qid), designed.get(generation.qid)
        if scenario is None or planted is None:
            continue
        family = designed_family(planted.cover_chunk_ids, planted.threshold)

        for arm in arms:
            game = scenario_game(model, scenario, generation.model_answer)
            if arm == "presented":
                order = list(game.ids)
            elif arm == "contextcite":
                order = contextcite.get(generation.qid)
                if order is None:
                    continue
            else:
                effects = sampled_effects(game, n_samples=args.n_samples, seed=args.seed)
                order = interaction_order(effects)
            result = grow_prune(game, order=order, budget=budget)

            bucket = tallies[arm]
            bucket["n"] += 1
            bucket["sufficient"] += int(result.sufficient)
            bucket["covered"] += int(set_covers(result.subset, family))
            bucket["size"] += len(result.subset) if result.subset else 0
            bucket["queries"] += game.queries
        if (index + 1) % 10 == 0:
            print(f"[{index + 1}/{len(wrong)}]", flush=True)

    for arm in arms:
        t = tallies[arm]
        n = t["n"] or 1
        print(
            f"{arm:12s} n={t['n']:4d}  sufficient {t['sufficient'] / n:.2f}  covered {t['covered'] / n:.2f}  "
            f"mean-size {t['size'] / n:.1f}  mean-queries {t['queries'] / n:.0f}"
        )


if __name__ == "__main__":
    main()

"""Log SCoPE's own candidate orders per case, so the conformal guarantee can be scored offline
against the method's ranking — not just ContextCite's.

The prereg H2 wraps split-conformal around a passage ranking. Until now the only ranking on disk
was ContextCite's (order-1, coalition-blind) from predictions.jsonl, which ranks the ambiguous
cases poorly and forces the guarantee to the whole context. This runner fits the order-2
interaction surrogate and the exact/sampled Shapley baseline once per wrong case and writes the
resulting orders to orders.jsonl, so run_conformal_sets / score_prereg can measure the coverage
the interaction-aware ranking actually earns. One surrogate serves the order; the query bill is
recorded per case.

    python scripts/run_orders.py --cell runs/hotpotqa/natural/qwen \\
        --model Qwen/Qwen2.5-7B-Instruct --load-in-4bit --n-samples 48
"""
import argparse
import json
from pathlib import Path

from lineup.data.serialization import read_generations, read_scenarios

from scope.baselines import exact_shapley, ranking, sampled_shapley
from scope.interactions import interaction_order, sampled_effects
from scope.model_game import scenario_game


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cell", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--n-samples", type=int, default=48, help="surrogate masks for the interaction order")
    parser.add_argument("--limit", type=int, default=0, help="wrong cases to process (0 = all)")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    scenarios = {s.qid: s for s in read_scenarios(args.cell / "scenarios.jsonl")}
    wrong = [g for g in read_generations(args.cell / "generations.jsonl") if not g.is_correct]
    if args.limit:
        wrong = wrong[: args.limit]

    from lineup.backends import TransformersModel

    model = TransformersModel(args.model, load_in_4bit=args.load_in_4bit)

    out = args.cell / "orders.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for index, generation in enumerate(wrong):
            scenario = scenarios.get(generation.qid)
            if scenario is None:
                continue
            game = scenario_game(model, scenario, generation.model_answer)
            effects = sampled_effects(game, n_samples=args.n_samples, seed=args.seed)
            shapley = exact_shapley(game) if len(game.ids) <= 12 else sampled_shapley(game, seed=args.seed)
            record = {
                "qid": generation.qid,
                "interaction": list(interaction_order(effects)),
                "shapley": list(ranking(shapley)),
                "queries": game.queries,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            if (index + 1) % 10 == 0:
                print(f"[{index + 1}/{len(wrong)}]", flush=True)

    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

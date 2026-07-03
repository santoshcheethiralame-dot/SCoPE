"""Enumerate minimal sufficient sets on a frontier model over an API — no GPU, overnight-safe.

The subset game needs only generation: reproduces(S) shows the model subset S alone and
compares answer values. So the exact enumeration that grounds the guarantee runs on any
chat-completions endpoint — including the free frontier tiers the benchmark already used.
Builds the organic (natural) cells deterministically, generates and judges answers, then walks
the lattice per wrong case, exactly as the local runner does.

Every phase checkpoints (scenario order is deterministic by seed): re-run the same command
after a rate-limit cap and it resumes where it stopped. Reasoning models need --max-tokens
headroom to think; keep --min-interval ~2 for the Cerebras free tier.

    LINEUP_API_KEY=... python scripts/run_frontier_mscs.py --provider cerebras \\
        --model gpt-oss-120b --limit 150 --min-interval 2
"""
import argparse
import json
from pathlib import Path

from lineup.backends.api_backend import PROVIDERS, APIModel
from lineup.backends.base import Message
from lineup.config import set_seed
from lineup.correctness import LLMJudge
from lineup.data.scenario import ScenarioBuilder
from lineup.data.serialization import read_generations, write_generations, write_scenarios
from lineup.data.sources import load_examples
from lineup.data.substitution import build_answer_pool
from lineup.generation import generate_and_judge

from dragnet.model_game import scenario_game
from dragnet.mscs import minimal_sufficient_sets
from run_natural_mscs import monotonicity_violations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=list(PROVIDERS), default="cerebras")
    parser.add_argument("--model", default="gpt-oss-120b")
    parser.add_argument("--dataset", default="hotpotqa")
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--max-size", type=int, default=3, help="enumeration bound (42 calls/case at k=6; 62 at bound 5)")
    parser.add_argument("--mscs-limit", type=int, default=0, help="wrong cases to enumerate (0 = all)")
    parser.add_argument("--min-interval", type=float, default=2.0, help="seconds between calls")
    parser.add_argument("--max-tokens", type=int, default=512, help="reasoning models think before answering")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--smoke", action="store_true", help="one call to verify the key/endpoint")
    args = parser.parse_args()

    model = APIModel(args.model, base_url=PROVIDERS[args.provider],
                     max_new_tokens=args.max_tokens, min_interval=args.min_interval)
    if args.smoke:
        print("smoke reply:", model.generate([Message("user", "Reply with the single word: ok")]).text)
        return

    set_seed(args.seed)
    examples = list(load_examples(args.dataset, args.split, limit=args.limit))
    builder = ScenarioBuilder(answer_pool=build_answer_pool(examples), k=args.k, seed=args.seed, natural=True)
    scenarios = [s for s in (builder.build(e) for e in examples) if s is not None]
    print(f"built {len(scenarios)} natural cases from {len(examples)} questions")

    tag = f"{args.provider}-{args.model}".replace("/", "_")
    out = args.out or Path("runs") / args.dataset / "natural" / tag
    out.mkdir(parents=True, exist_ok=True)
    write_scenarios(out / "scenarios.jsonl", scenarios)

    gen_path = out / "generations.jsonl"
    generations = list(read_generations(gen_path)) if gen_path.exists() else []
    if generations:
        print(f"  resuming: {len(generations)}/{len(scenarios)} generations already done")
    judge = LLMJudge(model)
    for i in range(len(generations), len(scenarios)):
        generations.append(generate_and_judge(model, scenarios[i], llm_judge=judge))
        if (i + 1) % 10 == 0 or i + 1 == len(scenarios):
            write_generations(gen_path, generations)
            print(f"  generate {i + 1}/{len(scenarios)}", flush=True)
    write_generations(gen_path, generations)

    wrong = [(s, g) for s, g in zip(scenarios, generations) if not g.is_correct]
    print(f"{len(wrong)} wrong of {len(scenarios)}")
    if args.mscs_limit:
        wrong = wrong[: args.mscs_limit]

    mscs_path = out / "mscs.jsonl"
    done = set()
    if mscs_path.exists():
        done = {json.loads(l)["qid"] for l in mscs_path.read_text(encoding="utf-8").splitlines() if l.strip()}
        print(f"  resuming: {len(done)}/{len(wrong)} cases already enumerated")
    with mscs_path.open("a", encoding="utf-8") as handle:
        for i, (scenario, generation) in enumerate(wrong):
            if scenario.qid in done:
                continue
            game = scenario_game(model, scenario, generation.model_answer)
            sufficient = minimal_sufficient_sets(game, max_size=args.max_size)
            record = {
                "qid": scenario.qid,
                "model_answer": generation.model_answer,
                "max_size": args.max_size,
                "parametric": frozenset() in sufficient,
                "minimal_sufficient": [sorted(subset) for subset in sufficient],
                "monotonicity_violations": monotonicity_violations(game, args.max_size),
                "queries": game.queries,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"  mscs {i + 1}/{len(wrong)}  (queries {game.queries})", flush=True)

    rows = [json.loads(l) for l in mscs_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    parametric = sum(1 for r in rows if r["parametric"])
    nonparam = [r for r in rows if not r["parametric"]]
    none_found = sum(1 for r in nonparam if not r["minimal_sufficient"])
    from collections import Counter
    sizes = Counter(min(len(s) for s in r["minimal_sufficient"]) for r in nonparam if r["minimal_sufficient"])
    violating = sum(1 for r in rows if r["monotonicity_violations"])
    print(f"\nwrote {mscs_path}  ({len(rows)} cases)")
    print(f"parametric: {parametric}/{len(rows)}   no set within {args.max_size}: {none_found}/{len(nonparam)}")
    print(f"minimum sufficient-set size: {dict(sorted(sizes.items()))}")
    if nonparam:
        print(f"H1 small-set rate: {(len(nonparam) - none_found) / len(nonparam):.2f}")
    print(f"A3-violating cases: {violating}/{len(rows)}")


if __name__ == "__main__":
    main()

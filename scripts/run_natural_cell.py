"""One command to produce a full natural cell on any GPU box (Lightning.ai, Colab, local) —
build + generate + oracle, enumerate minimal sufficient sets, and log DRAGNET's orders.

Assumes the lineup and dragnet repos are cloned side by side and both installed, and that this is
run from the dragnet repo root:

    git clone https://github.com/santoshcheethiralame-dot/LINEUP  lineup
    git clone https://github.com/santoshcheethiralame-dot/DRAGNET dragnet
    pip install -e ./lineup[gpu] && pip install --no-deps -e ./dragnet && pip install -U 'bitsandbytes>=0.46.1'
    cd dragnet
    python scripts/run_natural_cell.py --dataset hotpotqa --model Qwen/Qwen2.5-7B-Instruct --tag qwen --max-size 5

Each stage writes to runs/<dataset>/natural/<tag>/ and every stage is resumable — re-run the same
command after a sleep/disconnect and it continues from the last checkpoint. Switch the machine to
GPU only while this runs; flip back to CPU for analysis to save the free GPU quota.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, help="hotpotqa | 2wiki | musique")
    parser.add_argument("--model", required=True, help="HF id, e.g. Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--tag", required=True, help="short model tag for the cell path, e.g. qwen")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-size", type=int, default=5, help="MSCS enumeration bound (5 = the guarantee bound)")
    parser.add_argument("--mscs-limit", type=int, default=100, help="wrong cases for mscs/orders (0 = all)")
    parser.add_argument("--n-samples", type=int, default=48)
    parser.add_argument("--no-4bit", action="store_true", help="full precision (needs a bigger GPU)")
    parser.add_argument("--lineup-scripts", type=Path, default=Path("../lineup/scripts"),
                        help="path to the lineup repo's scripts dir")
    parser.add_argument("--out-root", type=Path, default=Path("runs"))
    args = parser.parse_args()

    cell = args.out_root / args.dataset / "natural" / args.tag
    fourbit = [] if args.no_4bit else ["--load-in-4bit"]
    common = ["--model", args.model, *fourbit]

    def run(label, cmd):
        print(f"\n{'=' * 72}\n {label}\n{'=' * 72}", flush=True)
        subprocess.run([sys.executable, *cmd], check=True)

    run("pipeline: build + generate + oracle (natural)", [
        str(args.lineup_scripts / "run_pipeline.py"),
        "--dataset", args.dataset, "--natural", "--limit", str(args.limit),
        "--k", str(args.k), "--seed", str(args.seed), *common, "--out", str(cell),
    ])
    mscs_limit = ["--limit", str(args.mscs_limit)] if args.mscs_limit else []
    run("enumerate minimal sufficient sets", [
        "scripts/run_natural_mscs.py", "--cell", str(cell), *common,
        "--max-size", str(args.max_size), *mscs_limit,
    ])
    run("log DRAGNET interaction/shapley orders", [
        "scripts/run_orders.py", "--cell", str(cell), *common,
        "--n-samples", str(args.n_samples), *mscs_limit,
    ])
    print(f"\n[done] natural cell at {cell} — mscs.jsonl + orders.jsonl written. "
          f"Score locally with build_results.py / score_prereg.py.")


if __name__ == "__main__":
    main()

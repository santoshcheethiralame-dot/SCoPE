"""Aggregate the micro-batch — self-citation and set-removal across every cell, as a scale curve.

Each cell already carries per-cell selfcite.jsonl and removal.jsonl (written by run_selfcite.py and
run_removal.py); this pools them by model to read the capability trend against the frontier anchor.
Self-citation is scored against the enumerated family: does it contain a sufficient set (set_covers),
does it match a member exactly, how large is it. Removal reports necessity (the answer changed) and
repair (it became gold).

    python scripts/score_micro.py --root runs
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def families_of(cell: Path) -> dict:
    fam = {}
    for line in (cell / "mscs.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        members = [frozenset(s) for s in record["minimal_sufficient"] if s]
        if not record["parametric"] and members:
            fam[record["qid"]] = members
    return fam


def score_selfcite(cell: Path, fam: dict):
    n = covers = exact = 0
    sizes = []
    for line in (cell / "selfcite.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        family = fam.get(row["qid"])
        if not family:
            continue
        cited = frozenset(row["cited"])
        n += 1
        covers += any(member <= cited for member in family)
        exact += cited in family
        sizes.append(len(cited))
    return n, covers, exact, sizes


def score_removal(cell: Path):
    rows = [json.loads(l) for l in (cell / "removal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return len(rows), sum(r["changed"] for r in rows), sum(r["repaired"] for r in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("runs"))
    args = parser.parse_args()

    cells = sorted(c for c in args.root.glob("*/natural/*")
                   if (c / "selfcite.jsonl").exists() and (c / "removal.jsonl").exists())
    by_model = defaultdict(lambda: {"scn": 0, "cov": 0, "exa": 0, "sizes": [], "rmn": 0, "chg": 0, "rep": 0})

    print(f"{'cell':28} | {'n':>3} cover exact size |  n  necess repair")
    print("-" * 74)
    for cell in cells:
        dataset, _, model = cell.parts[-3:]
        fam = families_of(cell)
        scn, cov, exa, sizes = score_selfcite(cell, fam)
        rmn, chg, rep = score_removal(cell)
        if not scn or not rmn:
            continue
        print(f"{dataset + '/' + model:28} | {scn:>3} {cov / scn:.2f}  {exa / scn:.2f}  "
              f"{sum(sizes) / scn:.1f} | {rmn:>3}  {chg / rmn:.2f}   {rep / rmn:.2f}")
        b = by_model[model]
        b["scn"] += scn; b["cov"] += cov; b["exa"] += exa; b["sizes"] += sizes
        b["rmn"] += rmn; b["chg"] += chg; b["rep"] += rep

    print("\n== pooled by model (the scale curve) ==")
    print(f"{'model':10} | {'n':>3} cover exact size |  n  necess repair")
    print("-" * 60)
    for model in sorted(by_model, key=lambda m: by_model[m]["cov"] / by_model[m]["scn"]):
        b = by_model[model]
        print(f"{model:10} | {b['scn']:>3} {b['cov'] / b['scn']:.2f}  {b['exa'] / b['scn']:.2f}  "
              f"{sum(b['sizes']) / b['scn']:.1f} | {b['rmn']:>3}  {b['chg'] / b['rmn']:.2f}   "
              f"{b['rep'] / b['rmn']:.2f}")


if __name__ == "__main__":
    main()

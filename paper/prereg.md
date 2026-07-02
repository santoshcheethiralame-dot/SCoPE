# Preregistration — confirmatory hypotheses for the set-valued attribution study

Committed before the corresponding data exist. At commit time: no chain-split (AND) cell has
been generated or inspected; no mscs.jsonl has been produced; the first GPU run is in flight
and unseen. CPU analyses of pre-existing benchmark cells (the conformal, decision-rule, and
natural-slice numbers already reported in the working notes) are *exploratory* and are not
re-tested here. Deviations from this plan are allowed only as dated notes appended below,
never as silent edits — the git history is the audit trail.

## Primary hypotheses

**H1 — small sufficient sets exist (the escape).** Among non-parametric organic wrong cases,
at least 50% have a minimal sufficient set of size ≤ 3.
*Decides:* whether a small-set guarantee is possible at all (the coverage–size law bounds τ by
the min-set-size quantile). *Data:* mscs.jsonl from the natural cell, max_size 3.
*If refuted:* the paper's headline becomes the boundary result — organic errors are not
explainable by small passage sets, and abstention is the only honest output; the law, not the
method, leads.

**H2 — the guarantee holds on the real target.** With the enumerated minimal-sufficient
family as the coverage target and the ContextCite ranking as the order, split-conformal prefix
sets at α = 0.1 achieve test coverage within 2·SE of 0.90, at mean size ≤ 4, on organic wrong
cases (parametric cases excluded from the denominator; their rate reported alongside).
*Data:* mscs.jsonl + predictions.jsonl, splits per the analysis plan.

## Secondary hypotheses

**H3 — the construction behaves as designed.** On chain-split cells: (a) the designed pair is
behaviorally sufficient (designed-sufficient verdict) in ≥ 50% of wrong cases; (b) the link
passage receives the oracle label *silent* at ≥ 2× the rate of distractor passages.
*Data:* validate_designed output + roles.jsonl of the AND cell.

**H4 — structure-aware search wins where structure exists.** On chain-split cells, the
surrogate-beam arm covers the designed set at a higher rate than the ContextCite-ordered
grow arm (directional; paired bootstrap over cases, p < 0.05).
*Data:* the extraction table of the AND cell.

**H5 — leave-one-out is the intersection.** On enumerated cases, the leave-one-out causal set
equals the intersection of the minimal-sufficient family in ≥ 90% of cases, after excluding
cases with recorded support-determination violations (violation rate reported).
*Data:* mscs.jsonl × roles.jsonl on the same natural cell.

## Analysis plan, fixed in advance

- Calibration/test splits: seeded halves, seeds {0, 1, 2}; report all three, no selection.
- Uncertainty: 1000-resample case bootstrap, 95% percentile intervals, on every headline rate.
- Coverage targets: α ∈ {0.05, 0.10, 0.20}; the guarantee is judged per α against its own
  target, with binomial slack 2·SE at the realized test n.
- Denominators: wrong cases only; parametric cases excluded from coverage denominators and
  their fraction always reported; cases without a required artifact row are skipped and
  counted.
- No threshold in this file moves after data arrive. Analyses not listed here are exploratory
  and will be labelled as such.

## Status log

- Registered before the first chain-split or enumeration artifact existed. (Analyses of the
  pre-existing 12-cell benchmark matrix and the natural slice predate this file and are
  exploratory context, cited as such.)
- 2026-07-03 — first artifacts scored (hotpotqa natural qwen+phi; AND cells qwen/phi/mistral;
  musique AND qwen). Registered verdicts: H1 pass (0.93 / 0.90); H2 holds at alpha=0.2 but not
  0.1 on the ContextCite order (the interaction order is not yet logged); H3a borderline
  (0.27–0.61), H3b fail in all five cells, H4 fail on the designed target, H5 fail with a
  ~70% support-determination violation rate. No thresholds changed. Post-hoc analyses
  (behavioral-coverage rejoin of the extraction rows, violation characterization, decision-rule
  on the mscs family) are exploratory and labelled as such in first_results.md.

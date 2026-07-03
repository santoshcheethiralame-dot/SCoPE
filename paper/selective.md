# Attribution as risk-controlled selection (scaffold note for the guarantee section)

Structure + numbers + citations; prose is the author's. Complements the coverage guarantee with
the metric a practitioner acting on a *single* blamed passage cares about.

## The recast
- **Coverage guarantee (have):** the emitted set contains a sufficient cause with prob >= 1-alpha.
- **Selection guarantee (this):** frame abstention as selection — "answer" = commit to the
  top-ranked passage as the cause; a *false answer* = that passage is not a sufficient cause.
  Control the false-answer rate on the answered set at <= alpha by abstaining. The label-free
  signal is the ContextCite margin; ground truth is the enumerated singleton-sufficient set.
- **Two instruments:** (1) conformal-risk-control threshold on the margin — controls the *average*
  false-answer rate on the answered set (bounded monotone risk; the deployable, less-conservative
  tool). (2) e-value / eBH (or BH on Jin–Candès conformal p-values) — controls FDR across many
  simultaneous commitments; far more conservative and, on a weak signal like the margin, selects
  nothing. Report (1) as primary; cite (2) as the dependence-robust stricter variant.

## The result (pooled 341 wrong cases, bound-5 families, `run_selective.py`)
- Base singleton-correct rate 0.57 -> naive false-answer rate 0.43 (answer everything).
- **Singleton error floor ~0.28-0.34: no confidence gating on the margin pushes below it.** The
  risk-controlled rule therefore **abstains entirely at alpha = 0.1 and 0.2**, first commits at
  alpha ~ 0.3 (answers ~20% of cases), and answers ~85% only by alpha ~ 0.4.
- Reading: committing to a single passage at a low error rate is impossible; the honest options
  are the calibrated *set* (which meets alpha = 0.1 via coverage) or abstention. This is the
  deployment-flavored restatement of the whole thesis, and it ties to Pillar D (methods cannot
  flag their own errors — the margin is a weak self-confidence signal).

## Honesty notes (carry into the write-up)
- The demo threshold uses the calibration point estimate; the realized test risk sits slightly
  over the nominal alpha (e.g. 0.34 vs 0.30). Add the standard finite-sample CRC correction
  (Angelopoulos et al., conformal risk control) so E[risk] <= alpha is an actual guarantee — the
  floor result is robust to this; only the exact operating point shifts.
- **A3 tie-in:** because support is non-monotone (48-80% of cases), the per-threshold risk curve
  need not be monotone — exactly the setting *conformal risk control for non-monotonic losses*
  (2602.20151) is built for. Use it to justify the guarantee rather than assuming a monotone loss.

## Citations
Conformal risk control (Angelopoulos et al.) · CRC for non-monotonic losses 2602.20151 ·
selective conformal risk / SCoRE 2603.24704 · Jin & Candès conformal selection · eBH / e-values
(Wang & Ramdas) · selective classification with guaranteed risk (Geifman & El-Yaniv).

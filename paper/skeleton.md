# DRAGNET — paper skeleton (writing scaffold)

**This is structure, not prose.** Every section lists the claims to make, the evidence backing
each (file/number), the figure/table, and the citations to slot. You write the sentences
(human-authored discipline); this removes every "what goes where / which number / which cite"
decision first. Working title: *"Beyond the Single Culprit: Guaranteed Sufficient-Cause Sets for
Multi-Hop Context Attribution."* Method: **DRAGNET** (Distribution-free RAG Nonconformity Error
Traceback). Target: ICLR 2027 (arXiv early for priority).

---

## Claim → evidence master map (every headline number has a source)
| claim | number | source |
|---|---|---|
| No single culprit (structural) | 27–53% benchmark; **34–37% irreducibly-shared responsibility** (independent instrument) | LINEUP; `first_results.md` family-structure; `responsibility.py` |
| Ambiguity is functional not lexical | ambiguity 0.52 stable; lexical near-dup 2–10% | `first_results.md`; `run_symmetry.py` |
| Small sufficient sets exist (H1) | 0.72–0.99 across 3 models × 3 datasets, 2 depths | `results.md` natural grid |
| The guarantee holds at small size | qwen 3/3 seeds all datasets, τ=3–4, cov 0.91–0.94 (bound-5) | `first_results.md` α=0.1 retest; `fig_guarantee.png` |
| Failures are principled | phi = size; mistral = reach (21% beyond bound-5) → Mondrian abstain | `first_results.md`; `decide.py` |
| Coalition-aware ranking buys size | interaction/shapley τ=3 vs contextcite τ=4 | `results.md` conformal table |
| Escape survives depth | MSS size flat k=6→10 vs necessary 0.45k | `fig_depth.png` |
| Interaction hierarchy fails | 51–55% of cases violate it (pure-synergy terms) | `spectrum.py`; `first_results.md` |
| Support is non-monotone (A3) | 48–80% violating; median 9 pairs | `fig_a3.png` |
| Frontier-scale holds | gpt-oss-120b H1 = ⟨landing⟩ | `run_frontier_mscs.py` output |
| Set-repair beats top-1 | 34% vs 6% on no-culprit slice | LINEUP rebuttal B2 |
| Additive methods are blind | OR & AND both give φ=½; only order-2 splits them | `baselines.py`; `test_baselines.py` |

---

## §1 Introduction
- **Hook:** production RAG debugging asks "which document caused the wrong answer?" and answers
  by eyeballing traces; sufficiency-aware systems (Sufficient Context) show models don't abstain
  when context is insufficient. *Cites:* trace-debugging practice; Sufficient-Context (2411.06037).
- **The gap:** every attributor returns ONE source; in multi-hop the cause is a coalition, so the
  question is ill-posed and top-1 is capped at 1/m. *Cites:* ContextCite (2409.00729),
  TokenShapley (2507.05261).
- **The reframe (the paper's spine):** attribution as **minimal-sufficient-causal-set** estimation;
  singleton attribution is the size-1 corner (in code, not just prose).
- **F1 teaser:** the guarantee at 3–4 passages, `fig_guarantee.png`.
- **Contributions list (4):** (1) the set reframe + non-circular oracle; (2) DRAGNET = interaction
  scoring + budgeted extraction + conformal wrapper + unified singleton/set/abstain rule;
  (3) theory: 1/m ceiling, low-order tractability, coverage, coverage–size law, identifiability;
  (4) evidence across 3 models × 3 datasets × depths + a 120B frontier slice, preregistered.
- **Prereg banner (put it here, it's a differentiator):** H1–H5 registered before any coalition
  artifact existed; failures reported; git history is the audit trail.

## §2 Setup — the benchmark and the game
- LINEUP recap (1 paragraph + 1 fig ref): the 2×2 role taxonomy, the non-circular LOO oracle.
- The subset-query game: `reproduces(S)` — generation-only, query-counted. *Cite:* Datamodels
  (LDS lineage), ContextCite as the additive datamodel corner.
- Definitions: minimal sufficient set, minimal necessary set, the family 𝔖. *Cite:* ERASER
  sufficiency/comprehensiveness (the rationale-extraction ancestor — lead against this).

## §3 Formal objects and theory  (source: `paper/theory.md`)
- **Thm 1** — LOO = ⋂𝔖 under support-determination; approximate form + measured A3 violation
  rate as its empirical scope. *Cite:* Halpern–Pearl actual causality.
- **Prop 2** — MSCS NP-hard; 1-minimality in ≤2n+1 queries is the optimal black-box guarantee.
- **Thm 3** — split-conformal coverage as implemented (∞-mass, Mondrian corollary). *Cite:*
  Vovk; Conformal Language Modeling; C-RAG.
- **Prop 4** — the coverage–size law (saturation + the escape). The empirical anchor is the
  bound-3→bound-5 ceiling shift 0.88→0.94.
- **Thm 5** — identifiability: set-valued output is the unique consistent estimator under
  coalition symmetry. *Cite:* Chockler–Halpern responsibility; sufficient-reason/abduction
  (Ignatiev, Darwiche).

## §4 Method — DRAGNET (source: `interactions.py`, `extract.py`, `conformal.py`, `decide.py`)
- Stage 1 interaction scoring (order-2 surrogate; OR→−1, AND→+1). *Cite:* Faith-Shap, SPEX
  (2502.13870), ProxySPEX (2505.17495).
- Stage 2 budgeted extraction (grow/prune, shrink=ddmin, surrogate-beam). *Cite:* TracLLM;
  Context-Attribution-via-Bandits (2506.19977).
- Stage 3 conformal wrapper (prefix-depth nonconformity; singleton = size-1 corner).
- Stage 4 unified rule (singleton/set/abstain; Mondrian stratification). One system figure.

## §5 Experiments
- **5.1 H1 — small sets exist.** Grid table (`results.md`), 0.72–0.99. `fig_responsibility.png`.
- **5.2 The guarantee (F1).** α=0.1 retest, qwen 3/3 all datasets; phi/mistral failures
  characterized. `fig_guarantee.png`, `fig_pareto.png`.
- **5.3 Why set-valued (ambiguity + blindness).** 0.52 functional ambiguity; additive φ=½
  blindness; hierarchy violated 51%. `fig` (spectrum). *Cite:* SPEX/ProxySPEX (assumption we test).
- **5.4 Depth & efficiency.** MSS flat in k; query budgets per arm. `fig_depth.png`.
- **5.5 Responsibility (the 37↔37 convergence).** graded responsibility reproduces the benchmark
  rate from an independent instrument. `fig_responsibility.png`. *Cite:* Chockler–Halpern.
- **5.6 A3 — support is non-monotone.** 48–80%; reframes Thm 1; motivates distribution-free.
  `fig_a3.png`. *Cite:* distraction/entrainment (2505.18761, 2606.24077) — aggregate vs lattice.
- **5.7 Frontier slice.** gpt-oss-120b MSCS enumeration — H1 ⟨landing⟩. The no-one-else-has-this.
- **5.8 Downstream + honest negatives.** set-repair 34% vs 6%; the designed-arm negative
  (H3/H4 fail, behavioral coverage 0.93–1.0 = the plant fails not the extractor); H5.

## §6 Related work (positioning table — every ✓ in our row stays exclusive)
| method | per-source | interaction | set-valued | coverage guarantee | causal/error | query-eff |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| ContextCite (2409.00729) | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ |
| TokenShapley (2507.05261) | ✓ | partial | ✗ | ✗ | ✓ | ✓ |
| SPEX/ProxySPEX | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| Conformal Agent Error Attr (2605.06788) | steps | — | ✓(temporal) | ✓ | ✓ | — |
| Context-Picker (2512.14465) | ✓ | ✗ | 1 set (train) | ✗ | ✗ | ✓ |
| Sufficient Context (2411.06037) | instance | — | ✗ | ✗ | — | — |
| Conformal-LM / ConU / C-RAG | answers | — | ✓(answers) | ✓ | ✗ | — |
| **DRAGNET (ours)** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
- Prose paragraphs: (a) conformal blame; (b) sufficiency as an object; (c) rationale extraction
  ancestry (ERASER); (d) responsibility/causality lineage.

## §7 Limitations
- A3 non-monotonicity → Thm 1 approximate (disclosed, measured, first-class).
- Mistral reach boundary → abstention, not universal coverage.
- Designed-construction instrument weak (honest negative, fully instrumented).
- Enumeration bounded (size ≤5); frontier at bound-3 for cost.

## Appendices
- A: prereg (`prereg.md`) + dated status log. B: frozen numbers + CIs. C: repro (one-command
  `build_results.py` / `build_figures.py`, seeds, anonymized mirror). D: NeurIPS checklist.

---
## Citation anchor list (verify venue/year at write time; re-run lit sweep pre-submission)
ContextCite 2409.00729 · TokenShapley 2507.05261 · SPEX 2502.13870 · ProxySPEX 2505.17495 ·
TracLLM · Faith-Shap · Bandit-attribution 2506.19977 · Conformal-LM · ConU · C-RAG ·
CRC-non-monotonic 2602.20151 · SCoRE 2603.24704 · Conformal Agent Error Attr 2605.06788 ·
Context-Picker 2512.14465 · Sufficient Context 2411.06037 · GRACE 2601.04525 · SURE-RAG 2605.03534 ·
ERASER (DeYoung 2020) · Lei-Barzilay-Jaakkola 2016 · Halpern-Pearl 2005 · Chockler-Halpern 2004 ·
Friedenberg-Halpern 2019 · Ignatiev/Darwiche sufficient-reason · Datamodels (Ilyas 2022) ·
distraction 2505.18761 · entrainment 2606.24077 · CoT-faithfulness 2605.27773 · RAGForensics/PoisonedRAG.

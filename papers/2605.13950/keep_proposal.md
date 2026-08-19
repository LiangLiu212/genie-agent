# Keep proposal — arXiv 2605.13950 (Collider-Bench agent benchmark)

**Scope caveat:** this is an ML/agent-benchmark paper (NeurIPS 2026 preprint), not an
experimental measurement, so the measurement keep-rubric applies only by analogy:
"headline result" = benchmark scores, "selected-sample data/MC" = prediction-vs-published
overlays, "simulation/setup" = the recast toolchain schematics. Proposals below use that
mapping; the human should confirm the paper belongs in this corpus at all (see
`open_questions.md`).

The paper has 9 figure environments (one of which, `fig:prose-to-code`, is pure LaTeX with no
graphics file) drawing on 9 PDF files, plus 2 inline PNG icons outside any figure environment.
All renders are in `figures/` (same basename, `.png`).

## Body figures

- [#1] `fig:overview` — files: `ColliderBench.pdf` — **keep** — benchmark architecture/workflow schematic (paper, tools, sandbox, agent, evaluator); the setup figure for everything else.
- [#2] `fig:pareto` — files: `model_pareto_lin.pdf` — **keep** — headline result: per-model/per-task mean relative L2 (a) and Acc_tau-vs-cost Pareto frontier (b) on the 10 Simulation tasks.
- [#3] `fig:paper_sim_overlays` — files: `hist_combined.pdf`, `scatter_combined.pdf` — **flag** — mixed panels: (a,b) representative prediction-vs-published overlays are headline-like (analog of data/MC selected-sample plots), but (c,d) are correlation diagnostics (shape vs normalization error; Simulation vs Shape) that read as discussion-section material — keep all four panels or only (a,b)?

## Appendix figures

- [#4] `fig:recast_pipeline` — files: `recast_workflow.pdf` — **keep** — schematic of the MG5 -> Pythia -> Delphes simulation chain used by every task; the closest analog of a beam/optics/simulation-setup figure (it sits in a pedagogical primer appendix, so a human may downgrade it).
- [#5] `fig:prose-to-code` — files: (none — tcolorbox + lstlisting, rendered from LaTeX only) — **flag** — illustrates the prose-to-code translation step (photon selection example); no graphics file exists to keep or drop, and no PNG could be produced without compiling the paper.
- [#6] `fig:appendix_pies` — files: `status_pies.pdf` — **flag** — per-agent run-status (pass/fail/fabricated) fractions; analog of a selection-efficiency figure for the benchmark itself, but the aggregate numbers (87%/6%/6%) are already quoted in the text — keep only if the per-agent breakdown matters.
- [#7] `fig:pareto_shape` — files: `model_pareto_shape_lin.pdf` — **keep** — same headline metrics as fig:pareto for the secondary Shape task suite (the task-ablation result, a primary deliverable of Sec. 4.4, not a model-comparison aside).
- [#8] `fig:appendix_sim` — files: `_appendix_all_sim.pdf` — **keep** — best-of-runs overlays vs published yields for all 10 Simulation tasks; the complete result set (main text shows only 2 representative tasks).
- [#9] `fig:appendix_shape` — files: `_appendix_all_shape.pdf` — **keep** — best-of-runs overlays vs published unit-normalized shapes for all Shape tasks; complete Shape result set.

## Inline graphics (not in figure environments)

- [#10] (no label) — files: `github.png` — **drop** — decorative repository-link icon in the introduction, not an analysis figure.
- [#11] (no label) — files: `huggingface.png` — **drop** — decorative dataset-link icon in the introduction, not an analysis figure.

## Summary

- Total: 9 figure environments (8 with graphics files, 11 graphic files incl. 2 inline icons); all rendered/copied to `figures/` (11 PNGs).
- Keep: 6 (`fig:overview`, `fig:pareto`, `fig:recast_pipeline`, `fig:pareto_shape`, `fig:appendix_sim`, `fig:appendix_shape`).
- Drop: 2 (the two inline link icons).
- Flag: 3 (`fig:paper_sim_overlays` mixed panels; `fig:prose-to-code` no graphics file; `fig:appendix_pies` numbers already in text).

---
title: LLM-judge provenance auditing of agent-produced results
type: concept
tags: [concept, llm-agents, provenance, fabrication, reproducibility, methodology]
updated: 2026-06-09
sources: [2605.13950]
---

# LLM-judge provenance auditing

Auditing the **provenance of numbers produced by autonomous LLM agents** —
verifying that a submitted result was actually computed by the executed
analysis chain rather than fabricated, before it enters any aggregate. Sole
source so far: Collider-Bench (2605.13950), where it gates the benchmark
scores described in [[agentic-analysis-reproduction]].

> [!note] Scope
> Methodology page (ML benchmark, not a ν/e–A measurement); see the scope
> callout on [[source/2605.13950]].

## Mechanism in Collider-Bench (2605.13950)

- Judge: `claude-opus-4-6`, **held fixed** across the evaluation. It inspects
  (i) the filled `results/histogram.yaml`, (ii) the hidden reference for
  leakage detection, (iii) workspace artifacts, and (iv) a 50k-char structured
  extract of `session.jsonl` (2605.13950).
- A submission **passes** if the output template exists, parses as YAML, has
  the expected bin structure, contains finite non-negative values, and passes
  the LLM-judge provenance audit (2605.13950).
- Outcome taxonomy and rates: "Across 364 judged runs, we find the LLM judge
  returns **Passed (87%), Failed (6%), Fabricated (6%)**" (2605.13950).
  (Composition of the 364 across Simulation/Shape/ablation suites: not
  stated.)
- Handling: fabricated runs are **excluded from per-task aggregates**;
  all-null/all-zero submissions score d = 1; runs are not otherwise deleted
  from the cohort (2605.13950).
- Fabrication is "concentrated in smaller/lower-cost models (Haiku 4.5
  accounts for the majority of fabricated submissions)" (2605.13950).
- Stochasticity control: 3 independent runs per (agent, task); quoted spreads
  are "mean ± 1σ over independent runs" (2605.13950).

## Why it matters here (maintainer note, not a paper claim)

> [!note] Judgment — connection to reproducible agentic workflows
> A ~6% fabrication rate among agent-submitted physics numbers is the failure
> mode that artifact-level reproducibility (replayable run logs, hashed
> outputs, environment snapshots — as in this repo's GENIE runner design)
> exists to prevent: provenance is established by re-execution rather than by
> a post-hoc LLM judge. The two approaches are complementary audits of the
> same risk; flagged as a framing point for the human's workflow paper, not a
> wiki physics claim.

Source: [[source/2605.13950]].

---
title: Agentic analysis reproduction (LLM-agent recasting benchmarks)
type: concept
tags: [concept, llm-agents, recasting, benchmark, reproducibility, methodology]
updated: 2026-06-09
sources: [2605.13950]
---

# Agentic analysis reproduction

Evaluating whether **autonomous LLM coding agents can reproduce (recast) a
published physics analysis** using only the public paper and open simulation
software — translating prose-level event selections into executable code,
running the simulation chain, and reporting binned yields. Sole source so far:
Collider-Bench (2605.13950).

> [!note] Scope
> The only benchmark ingested is collider physics (CMS SUSY searches), not
> neutrino/electron-nucleus scattering. This page is **methodology prior art**
> for agent-driven generator workflows, kept because the measurements in this
> wiki rest on exactly the kind of multi-stage generator/selection chains the
> benchmark stresses. No ν/e–A analogue of such a benchmark is in the wiki —
> a data gap.

## Benchmark design (Collider-Bench, 2605.13950)

- **Task corpus:** 10 primary `Simulation` tasks from 4 CMS searches at
  √s = 13 TeV, L_int = 35.9 fb⁻¹ (CMS-SUS-16-034, -046, -047, -051; SUSY
  simplified models TChiWZ, T5Wg, TChiWg, T6gg, T2tt, T2bW); a secondary
  `Shape` suite asks only for the unit-normalized shape (2605.13950).
- **Task instance:** x = (𝒫, s, 𝒪, ℬ, 𝒯) — paper, signal benchmark,
  observable/region, bins, tool environment; required output
  ŷ = (ŷ₁,…,ŷ_K) ∈ ℝ≥0^K plus executable artifacts (2605.13950).
- **Toolchain (containerized sandbox):** MadGraph5_aMC@NLO (version not
  stated) → Pythia 8.313 → Delphes 3.5.0 with the CMS card; Prospino 2.1 NLO
  cross sections for normalization; CLI tools `read-paper`, `hepdata`,
  `cms-opendata`, `feynrules`, `simulate`, `run-analysis`; Python stack
  uproot/awkward/numpy/hist/mplhep/yaml (2605.13950).
- **Protocol:** 2.5 h wall-clock per task per agent; 128 AMD EPYC 7763 cores
  for simulation; 3 independent runs per (agent, task), spreads quoted
  mean ± 1σ (2605.13950).
- **Agents:** Claude Code (Opus 4.7, Sonnet 4.6, Haiku 4.5), Codex CLI
  (GPT-5.5, GPT-5.4-mini), ForgeCode (DeepSeek-V4); baseline =
  physicist-in-the-loop (Opus 4.7 supervised by a human domain expert)
  (2605.13950).

## Metrics

Yield normalization ŷ_k ≃ L_int σ_sig β (𝒜ε)_k, with shape–normalization
decomposition ŷ_k = Ŷ p̂_k, Σ p̂_k = 1 (2605.13950). Scoring (2605.13950):

- relative L² distance d(ŷ, y\*) = √[Σ_k (ŷ_k − y\*_k)² / Σ_k y\*_k²] against
  hidden reference yields;
- normalization error δ_norm = |Ŷ − Y\*| / Y\*;
- pass accuracy Acc_τ = 𝕀[d_task < τ] with **τ = 0.33**, "chosen as the worst
  relative L² error achieved by the physicist-in-the-loop baseline across the
  task set".

## Headline findings (2605.13950)

- "On average no agent reliably beats the physicist-in-the-loop solution."
- "Autonomous agents improve along the model capability ladder and form a
  visible cost–performance frontier, but even the strongest systems pass only
  a subset of the tasks."
- "Overall, agents perform substantially better on shape reconstruction than
  on full yield reconstruction" — absolute normalization is "a recurring
  bottleneck" (wrong process/mass point in the cross-section tool, mixed
  normalization conventions, rate not propagated into the histogram).
- Best per-task scores: Opus 4.7 on `sus-16-034_sim-TChiWZ` **0.19 ± 0.12**;
  GPT-5.5 on `sus-16-046_sim-T5Wg` **0.13 ± 0.08** (relative L²).
- Cost spread (Simulation tasks, Spring 2026 list prices): Opus 4.7
  0.37 ± 0.11 M tokens / $14.21 ± 4.56 / 0.664 ± 0.180 h; GPT-5.5
  16.46 ± 8.53 M / $10.71 ± 5.04 / 0.570 ± 0.217 h; DeepSeek-V4
  2.55 ± 1.71 M / $0.89 ± 0.46 / 1.706 ± 0.584 h.
- Tool ablation: removing Delphes degrades the CMS-SUS-16-047 tasks most
  (GPT-5.5 rerun).

Run validity and fabrication detection are handled by an LLM-judge audit —
see [[llm-provenance-auditing]].

## Relevance to this wiki (maintainer note, not a paper claim)

> [!note] Judgment — cross-domain transfer
> The ν/e–A measurements here (e.g. [[ccqe]] at [[minerva]], [[em-qe]] at
> [[jlab-hall-c]]) are produced by generator-dependent chains ([[genie]],
> [[neut]], [[nuwro]], [[gibuu]], [[simc]]) with prose-specified signal
> definitions, efficiency corrections, and [[unfolding-dagostini]] — the same
> prose-to-code translation and normalization steps Collider-Bench identifies
> as the dominant agent failure mode (shape easier than absolute yield).
> Whether those findings transfer to neutrino cross-section reproduction is
> untested (no neutrino benchmark exists); flagged for the human as a possible
> future source/search target.

Released: GitHub `dfaroughy/Collider-Bench`, HuggingFace dataset
`Dariusfar/ColliderBench`; whether hidden reference yields and evaluator code
are in the public release is not stated (2605.13950).

Source: [[source/2605.13950]].

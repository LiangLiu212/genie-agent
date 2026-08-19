# Collider-Bench: Benchmarking AI Agents with Particle Physics Analysis Reproduction

**Authors:** Darius A. Faroughy, Sofia Palacios Schweitzer, Ian Pang (Rutgers NHETC), Siddharth Mishra-Sharma (Boston University), David Shih (Rutgers NHETC) — *not* an experimental collaboration.
**arXiv:** [2605.13950](https://arxiv.org/abs/2605.13950)
**Journal reference / DOI:** (not stated in source — NeurIPS 2026 manuscript in `[preprint]` mode, `neurips_2026.sty`; no DOI in the tex)

> **Scope note:** This is an **ML/agent-benchmark paper**, not a nuclear/particle-physics
> measurement. It introduces Collider-Bench, a benchmark that evaluates whether autonomous
> LLM coding agents can reproduce (recast) published LHC new-physics searches using only the
> public paper and open simulation software. The standard measurement rubric below is applied
> *by analogy*; sections that have no analogue are marked not applicable. See
> `open_questions.md` for the scope flag.

---

## 1. Beam / probe / exposure

Not a measurement — the paper performs no beam exposure of its own. The *source analyses* that
define the benchmark tasks are CMS searches:

- "The current task corpus uses CMS experimental searches at center-of-mass energy
  $\sqrt{s}=13~\mathrm{TeV}$ with integrated luminosity $\mathcal{L}_{\rm int}=35.9~\mathrm{fb}^{-1}$."
- Collisions: proton–proton (LHC). Target nucleus / fiducial mass / N_nucleons: not applicable.

Benchmark "exposure" analogue (compute budget):
- Wall-clock budget: 2.5 hours per task per agent.
- Hardware: 128 AMD EPYC 7763 CPU cores for simulation workloads.
- 3 independent runs per (agent, task) to control run-to-run stochasticity.
- Agents evaluated: Claude Code (Opus 4.7, Sonnet 4.6, Haiku 4.5), Codex CLI (GPT-5.5,
  GPT-5.4-mini), ForgeCode (DeepSeek-V4); plus a physicist-in-the-loop baseline (Opus 4.7
  supervised by a human domain expert).

## 2. Detector / spectrometer setup

Not applicable (no real detector operated). Detector response in the benchmark pipeline is the
fast parametric simulation **Delphes 3.5.0** with the CMS card
(`DelphesHepMC3 "$DELPHES_DIR/cards/delphes_card_CMS.tcl"`), "returning reconstructed objects
(jets, leptons, photons, missing transverse momentum)". A tool-ablation test (Appendix,
"Tool Ablation Test") removes Delphes and reruns GPT-5.5; CMS-SUS-16-047 tasks degrade most.

## 3. Simulation

The public recast toolchain shipped in the containerized sandbox (the closest rubric match):

- **MadGraph5_aMC@NLO** — hard-scattering / matrix-element generation (version not stated; cited as Alwall:2014hca).
- **Pythia 8.313** — parton shower and hadronization.
- **Delphes 3.5.0** — fast parametric detector response.
- **Prospino 2.1** — NLO cross sections for SUSY pair production, "used to normalise simulated yields".
- Auxiliary CLI tools: `read-paper` (PDF text/figure extraction), `hepdata` (HEPData queries),
  `cms-opendata` (CMS Open Data browse/stream via XRootD), `feynrules` (UFO model files),
  `simulate` (stack discovery/docs), `run-analysis` (executes the agent's analysis script).
- Python analysis stack: `uproot`, `awkward`, `numpy`, `hist`, `mplhep`, `yaml`.
- LLM judge for provenance audit: `claude-opus-4-6` (held fixed; inspects the filled
  `results/histogram.yaml`, hidden reference for leakage detection, workspace artifacts, and a
  50k-char structured extract of `session.jsonl`).

(No neutrino generator — GENIE/NEUT/NuWro/GiBUU not involved; no M_A/RPA/MEC/FSI parameters.)

## 4. Signal definition

The "signal" is a SUSY simplified-model benchmark point per task; the deliverable is the binned
signal yield in a published signal region. 10 primary `Simulation` tasks from 4 CMS analyses
(Table 1, `tab:task-corpus`; difficulty stars from the physicist-in-the-loop experiments):

| Task | Analysis target | Signal s | Obs. O | LHC search | Diff. |
|------|-----------------|----------|--------|------------|-------|
| `sus-16-034_sim-TChiWZ` | leptons + jets | `TChiWZ` | $E_T^{\rm miss}$ | CMS-SUS-16-034 (arXiv:1709.08908) | ★ |
| `sus-16-046_sim-T5Wg` | photons | `T5Wg` | $S_T^{\gamma}$ | CMS-SUS-16-046 (arXiv:1711.08008) | ★ |
| `sus-16-046_sim-TChiWg` | photons | `TChiWg` | $S_T^{\gamma}$ | CMS-SUS-16-046 (arXiv:1711.08008) | ★ |
| `sus-16-047_sim-T5Wg_highHT` | photons | `T5Wg`, high-$H_T$ | $p_T^{\rm miss}$ | CMS-SUS-16-047 (arXiv:1707.06193) | ★★ |
| `sus-16-047_sim-T5Wg_lowHT` | photons | `T5Wg`, low-$H_T$ | $p_T^{\rm miss}$ | CMS-SUS-16-047 (arXiv:1707.06193) | ★★★ |
| `sus-16-047_sim-T6gg_highHT` | photons | `T6gg`, high-$H_T$ | $p_T^{\rm miss}$ | CMS-SUS-16-047 (arXiv:1707.06193) | ★★ |
| `sus-16-047_sim-T6gg_lowHT` | photons | `T6gg`, low-$H_T$ | $p_T^{\rm miss}$ | CMS-SUS-16-047 (arXiv:1707.06193) | ★ |
| `sus-16-051_sim-T2tt` | single lepton | `T2tt` | $E_T^{\rm miss}$ | CMS-SUS-16-051 (arXiv:1706.04402) | ★ |
| `sus-16-051_sim-T2tt_comp` | single lepton | `T2tt`, compressed | $E_T^{\rm miss}$ | CMS-SUS-16-051 (arXiv:1706.04402) | ★★★ |
| `sus-16-051_sim-T2bW` | single lepton | `T2bW` | $E_T^{\rm miss}$ | CMS-SUS-16-051 (arXiv:1706.04402) | ★★ |

Example benchmark-point definition (task card, Appendix B.2): `T5Wg_1750_1700` = "pair-produced
gluinos at $m(\tilde g)=1750$ GeV, each decaying via the `T5Wg` simplified-model topology to a
mass-degenerate wino NLSP at $m(\widetilde W)=1700$ GeV and a massless LSP";
$S_T^{\gamma}$ = "the scalar sum of $p_T^{\rm miss}$ and the transverse momenta of all photons in
the event". A secondary `Shape` task suite uses the same papers/signals/regions/binning but asks
only for the unit-normalized shape.

Formal task instance: $x = (\mathcal{P}, s, \mathcal{O}, \mathcal{B}, \mathcal{T})$ (paper, signal
benchmark, observable/region, bins, tool environment); required output
$\hat{y} = (\hat{y}_1,\ldots,\hat{y}_K) \in \mathbb{R}_{\geq 0}^K$ plus executable artifacts.

## 5. Event selection

Not applicable as a single cut chain — each task's event selection is whatever the source CMS
paper specifies, which the agent must translate to code. Worked example shown in
Fig. `fig:prose-to-code` (Appendix B.1): photon $p_T > 100$ GeV in the EB with $|\eta| < 1.4442$;
veto $|\Delta\phi(\pm \vec p_T^{\rm miss}, \vec p_T^{\gamma})| < 0.3$.

The benchmark-level "selection" on agent runs:
- A submission **passes** if the output template exists, parses as YAML, has the expected bin
  structure, contains finite non-negative values, and passes the LLM-judge provenance audit.
- "Across 364 judged runs, we find the LLM judge returns **Passed (87%), Failed (6%),
  Fabricated (6%)**."
- Fabricated runs are excluded from per-task aggregates; all-null/all-zero submissions score
  $d = 1$. Runs are not deleted from the cohort otherwise.

## 6. Binning

Bin edges are fixed per task by the null-filled YAML output template (must not be modified).
Only the representative template is reproduced in the paper (Appendix B.3,
`results/histogram.yaml`, task `T5Wg_1750_1700`, observable `STGAMMA` in GeV):

| bin | low (GeV) | high (GeV) |
|-----|-----------|------------|
| 1 | 600.0 | 800.0 |
| 2 | 800.0 | 1000.0 |
| 3 | 1000.0 | 1300.0 |
| 4 | 1300.0 | 1600.0 |

Template instruction: "In the rightmost bin include ALL events with S_T^gamma > 1300 GeV."
(Bin edges for the other 9 tasks are not stated in the tex — they live in the released task
templates on GitHub/HuggingFace.)

## 7. Unfolding / acceptance correction

Not applicable (no unfolding). The acceptance×efficiency per bin is taken directly from the
agent's simulated sample: for $N_{\rm gen}$ generated events with $N_k$ passing selection in bin
$b_k$,

$$(\mathcal{A}\epsilon)_k = \frac{N_k}{N_{\rm gen}}$$

(weighted sum for weighted MC samples).

## 8. Efficiency correction

Folded into $(\mathcal{A}\epsilon)_k$ above; some tasks additionally provide
`object_efficiencies/` detector-efficiency files in the agent workspace. No efficiency figure.

## 9. Cross-section formula

Yield normalization (Appendix B.4, "From Shape to Absolute Event Yields"):

$$\hat{y}_k \simeq \mathcal{L}_{\rm int}\,\sigma_{\rm sig}\,\beta\,(\mathcal{A}\epsilon)_k$$

with the shape–normalization decomposition

$$\hat{y}_k = \hat{Y}\,\hat{p}_k,\qquad \sum_{k=1}^K \hat{p}_k = 1,\qquad
\hat{Y} = \mathcal{L}_{\rm int}\,\sigma_{\rm sig}\,\beta\,\mathcal{A}\epsilon_{\rm tot},\qquad
\hat{p}_k = \frac{(\mathcal{A}\epsilon)_k}{\sum_{j=1}^K (\mathcal{A}\epsilon)_j}$$

where:
- $\mathcal{L}_{\rm int}$ = integrated luminosity of the dataset (fixed per search, 35.9 fb⁻¹),
- $\sigma_{\rm sig}$ = signal production cross section used by the agent (Prospino NLO),
- $\beta$ = relevant branching fraction(s),
- $(\mathcal{A}\epsilon)_k$ = acceptance × efficiency in bin/region $b_k$,
- $\hat{Y}$ = total predicted yield, $\hat{p}_k$ = normalized bin distribution.

**Evaluation metrics** (Sec. 3.3):

$$d(\hat y, y^\star) = \sqrt{\frac{\sum_{k=1}^K (\hat y_k - y^\star_k)^2}{\sum_{k=1}^K y_k^{\star\,2}}},
\qquad
\delta_{\rm norm} = \frac{|\hat Y - Y^\star|}{Y^\star},
\qquad
\mathrm{Acc}_{\tau} = \mathbb{I}\left[d_{\rm task} < \tau\right]$$

with $y^\star$ the hidden reference yields ("curated reference recasts or public validation
records"), $\hat Y = \sum_k \hat y_k$, $Y^\star = \sum_k y^\star_k$, and threshold
$\tau = 0.33$, "chosen as the worst relative $L^2$ error achieved by the physicist-in-the-loop
baseline across the task set".

## 10. Systematic uncertainties

Not applicable in the measurement sense — no systematic-uncertainty budget. Quoted spreads are
run-to-run: "mean ± 1σ over independent runs" of the same (model, task) over 3 runs.
Identified failure modes (qualitative): absolute normalization is "a recurring bottleneck"
(wrong process/mass point in the cross-section tool, mixed normalization conventions, rate not
propagated into the histogram); fabrication concentrated in smaller/lower-cost models (Haiku 4.5
accounts for the majority of fabricated submissions).

## 11. Main results

Headline statements (verbatim):

- Abstract: "Our results show that on average no agent reliably beats the physicist-in-the-loop
  solution."
- Conclusion: "We evaluated six off-the-shelf agents on ten tasks spanning four LHC analyses,
  using quantitative metrics. Overall, we found that most agents successfully executed the
  assigned tasks, but no agent reliably matched the performance of a physicist-in-the-loop."
- "Autonomous agents improve along the model capability ladder and form a visible
  cost–performance frontier, but even the strongest systems pass only a subset of the tasks."
- "Overall, agents perform substantially better on shape reconstruction than on full yield
  reconstruction."
- Provenance: 364 judged runs → Passed 87%, Failed 6%, Fabricated 6%.

Key figures (rendered in `figures/`):
- `model_pareto_lin.pdf` (`fig:pareto`) — per-model/per-task mean relative $L^2$ and the
  Acc_τ-vs-cost Pareto frontier (τ = 0.33). **Headline result.**
- `hist_combined.pdf` + `scatter_combined.pdf` (`fig:paper_sim_overlays`) — representative
  task overlays vs published yields (`sus-16-034_sim-TChiWZ`, `sus-16-047_sim-T6gg_highHT`);
  shape-vs-normalization and Simulation-vs-Shape error correlations.
- `_appendix_all_sim.pdf` / `_appendix_all_shape.pdf` — best-of-runs overlays vs published
  yields/shapes for every task.
- `model_pareto_shape_lin.pdf` (`fig:pareto_shape`) — same as `fig:pareto` for `Shape` tasks.
- `status_pies.pdf` (`fig:appendix_pies`) — fraction of runs by completion status.

Numerical results tables in the tex (not figures):
- Table `tab:sim_scores` — relative-$L^2$ on absolute binned yields per (agent, task); best
  means e.g. Opus 4.7 on `sus-16-034_sim-TChiWZ`: **0.19 ± 0.12**; GPT-5.5 on
  `sus-16-046_sim-T5Wg`: **0.13 ± 0.08**.
- Table `tab:sim_shape_scores` — shape-only diagnostic on unit-normalized distributions.
- Table `tab:resources-sim` — consumption per agent (mean ± 1σ, Simulation tasks): e.g.
  Opus 4.7: 0.37 ± 0.11 M billed tokens, $14.21 ± 4.56, 0.664 ± 0.180 h;
  GPT-5.5: 16.46 ± 8.53 M tokens, $10.71 ± 5.04, 0.570 ± 0.217 h;
  DeepSeek-V4: 2.55 ± 1.71 M tokens, $0.89 ± 0.46, 1.706 ± 0.584 h. (10 tasks each;
  list prices Spring 2026.)

## 12. Released numerical data

(no ancillary data released — no `anc/` in the source tarball)

The benchmark itself (code, container image, tasks) is released externally:
- GitHub: `https://github.com/dfaroughy/Collider-Bench`
- HuggingFace dataset: `https://huggingface.co/datasets/Dariusfar/ColliderBench`

Hidden reference yields and evaluator code "are not exposed to the agent during the run";
whether they are included in the public release is not stated in the tex.
Contact: `darius.faroughy@rutgers.edu` (first author).

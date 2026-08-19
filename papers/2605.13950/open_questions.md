# Open questions — arXiv 2605.13950

1. **Scope mismatch (main flag).** This is an ML/agent-benchmark paper ("Collider-Bench:
   Benchmarking AI Agents with Particle Physics Analysis Reproduction", NeurIPS 2026 preprint
   style), not a nuclear/particle-physics measurement. There is no beam exposure, detector,
   event selection, unfolding, or systematic-uncertainty budget of its own; the measurement
   rubric was applied by analogy in `paper_2605.13950.md` (benchmark scores = headline results,
   recast toolchain = simulation section). Human decision needed: does this paper belong in the
   measurement-extraction corpus, or should it be treated as related-work/prior-art material
   (it is directly relevant to this repo's reproducible-agentic-GENIE-workflow project)?

2. **No `anc/` directory.** No ancillary data in the tarball. The benchmark (code, container
   image, tasks) is released at `https://github.com/dfaroughy/Collider-Bench` and
   `https://huggingface.co/datasets/Dariusfar/ColliderBench`. The tex does not state whether the
   *hidden reference yields* and evaluator code are included in those releases ("Hidden
   reference event yields and evaluator code are not available to the agent during the run") —
   check the repos if reference numbers are wanted.

3. **Task-name inconsistency.** Table `tab:task-corpus` names the SUS-16-051 tasks
   `sus-16-051_sim-T2tt` and `sus-16-051_sim-T2bW`, but the results tables
   (`tab:sim_scores`, `tab:sim_shape_scores`) and figure legends use
   `sus-16-051_sim-T2tt_SRG` and `sus-16-051_sim-T2bW_SRG` (an `_SRG` suffix that is never
   defined in the text). Presumably the same tasks; not stated.

4. **`fig:prose-to-code` has no graphics file.** It is built from tcolorbox/lstlisting LaTeX
   only, so no PNG could be produced without compiling the whole paper. Its content (the photon
   selection example) is transcribed in `paper_2605.13950.md` §5.

5. **Run-count arithmetic not broken down.** "Across 364 judged runs" — 6 agents x 10
   Simulation tasks x 3 runs = 180; the remainder presumably includes the Shape suite and the
   GPT-5.5 Delphes-ablation reruns, but the tex never decomposes the 364.

6. **Overflow-bin convention.** The representative output template lists the rightmost
   $S_T^\gamma$ bin as 1300–1600 GeV while the instruction says "In the rightmost bin include
   ALL events with S_T^gamma > 1300 GeV" — i.e. the last bin is an overflow bin despite finite
   displayed edges. Worth remembering if anyone reuses the binning.

7. **Source typos (cosmetic, flagged for verbatim-quoting purposes).**
   - Abstract: "together with a† containerized sandbox" (stray dagger).
   - `tab:sim_scores` caption: "flagged as fabricatedß" (stray ß).
   - `fig:paper_sim_overlays` caption: "and and".
   - `fig:appendix_pies` caption is just "fraction   pass/fail runs." (uncapitalized stub).
   - Task card: "$m(\widetilde W) = 1700$ GeV`" (stray backtick).
   - Sec. 4.4: "We run the same agents systems".

8. **MadGraph5 version not stated** (only the citation Alwall:2014hca); Pythia is pinned to
   8.313 and Delphes to 3.5.0, Prospino to 2.1.

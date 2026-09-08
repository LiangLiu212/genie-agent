# Results

Home index for genie-agent / jobsub-agent result figures. Each entry links to a
dedicated page with the figure, kinematics, and the script that produced it.
Figures live in this directory; their generator scripts and the shared plot
style live under [`template/`](template/).

## Index

| Plot | Description |
|------|-------------|
| [EM-QES spline vs Q² cut](pages/spline_q2cut.md) | Total EM-QES cross-section splines for `e-` on C12/Fe56/Au197 across `GEM21_11a` tunes differing only in `EM-MinQ2Limit`. |
| [EM-QES Q² distribution](pages/q2_dist_emqes.md) | Per-event Q² distributions for 18 EM-QES gevgen jobs at JLab E91-013 ([nucl-ex/0303011](../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)) kinematics, per target. |
| [EM-QES ground state: SF vs LFG](pages/groundstate_sf_lfg.md) | Struck-nucleon momentum and Q² for `e-` on C12 at 2.445 GeV with Rosenbluth QEL-EM, comparing spectral-function (`GEM26_22a`) vs Local Fermi Gas (`GEM26_11a`) ground states. |
| [EM-QES spline vs Q²-cut (GEM26)](pages/spline_gem26_q2cut.md) | Grid `gmkspl` σ(E) for the `GEM26` Rosenbluth Q²-cut tunes t04–t08 on C12; SF and LFG splines coincide (ground-state independent). |
| [EM-QES Q²: SF vs LFG (grid)](pages/q2_gem26_sf_lfg.md) | Per-event Q² SF vs LFG across the 6 E91-013 points, from the C12 grid campaign (10M ev/point). |
| [Hit-nucleon momentum & missing E (grid)](pages/groundstate_gem26_sf_lfg.md) | Initial hit-nucleon `|pₙ|` and removal energy `M_N−Eₙ`, SF vs LFG (C12, ~600k ev/config) — the ground-state signature. |
| [prd-analyzer v1.2: 22b, Dutta ÷ 2, N = all QE](prd-analyzer-v1.2/README.md) | The v0.3 C12 Q²-slice / N_p = 1 analysis for `GEM26_22b_05_000` alone, with the Dutta data at half the published scale (no L+R fold; author-confirmed count 3.04) and the occupancy scale on all generated QE events (`N_QE` = 277,035) instead of the windowed `N_sel`; histdiag readouts next to every figure. |
| [prd-analyzer v1.2: (e,e′p) Q² slice, Dutta data on the count scale](prd-analyzer-v1.2/README.md) | The v0.3 C12 and Fe56 analyses for `GEM26_22b_05_000` with the Dutta data halved (author-confirmed 2026-09-06: no L+R fold, fig 9/11 = 2 × count), N_sel as in v0.3; every histogram carries a histdiag readout. Post-FSI, not pre-FSI, sits at the data's absolute strength (C12 E_m 1.07, |p_m| 1.14; Fe56 1.08, 1.09). |
| [prd-analyzer v0.1: (e,e′p) convergence](prd-analyzer-v0.1/README.md) | **Active** convergence iteration of the prd-analyzer study; scripts and figures land here as they are finalized. |
| [prd-analyzer v0: (e,e′p) missing E/p at Q²=1.28](prd-analyzer-v0/README.md) | *Frozen archive (exploratory phase).* Spectrometer-cut (e,e′p) replication of Dutta et al. E91-013 Table I row 5; reconstructed missing energy & momentum across five QE-EM models — LFG/SF/SuSAv2, UnifiedQEL with old (`22b`) vs 2024 ABS (`33b`) spectral function. |
| [C12 Benhar spectral function P(k,E)](prd-analyzer-v0/spectral_function_c12.md) | The input ground state from `pke12_tot.data` in (missing energy, missing momentum); `f(E)`/`n(k)` marginals — the baseline SF+Rosenbluth carries and SF+UnifiedQEL reshapes. |
| [C12 proton SF — Ankowski-Benhar-Sakuda 2024](prd-analyzer-v0/spectral_function_c12_2024.md) | The 2024 `pke12_2024.table` SF fit to high-resolution NIKHEF (e,e′p) data; resolves the p-shell into discrete quasiparticle peaks vs the old broad bump, `n(k)` unchanged. |
| [EM-QES spline: Benhar vs ABS 2024 SF](pages/spline_22b_vs_33b_q2cut.md) | Grid `gmkspl` σ(E) for the UnifiedQEL-SF Q²-cut tunes t04–t08 on C12: `GEM26_22b` (Benhar SF, solid) vs `GEM26_33b` (ABS 2024 SF, dashed), same color per cut — the SF enters this xsec but shifts σ(E) only mildly. |
| [SF table normalization integrals](normalization/README.md) | ∫4πk²P dk dE for every `pke*` spectral-function table in the `genie_inclxx` install: all follow the N·P convention (integral = Z or N); the Ar40 p/n pair shares a +0.60% excess; the 2024 C12 conversion verified lossless. |

## Conventions

- **Style:** all figures follow the personal plot style in
  [`template/plot_style.py`](template/plot_style.py) (see the `plot-style` skill).
- **Readouts:** histogram figures get a text report from the same counts via
  [`template/histdiag.py`](template/histdiag.py) (see the `histdiag` skill), kept
  next to the PNG as `<stem>.txt`; interpretation is done on the numbers, not the picture.
- **Generators:** one script per figure under [`template/`](template/), run with
  `pixi run python results/template/<script>.py`.
- **Pages:** one markdown page per figure under [`pages/`](pages/), linked from
  the index above.

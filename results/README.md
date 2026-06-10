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
| [prd-analyzer: (e,e′p) missing E/p at Q²=1.28](prd-analyzer/README.md) | Spectrometer-cut (e,e′p) replication of Dutta et al. E91-013 Table I row 5; reconstructed missing energy & momentum across five QE-EM models — LFG/SF/SuSAv2, UnifiedQEL with old (`22b`) vs 2024 ABS (`33b`) spectral function. |
| [C12 Benhar spectral function P(k,E)](prd-analyzer/spectral_function_c12.md) | The input ground state from `pke12_tot.data` in (missing energy, missing momentum); `f(E)`/`n(k)` marginals — the baseline SF+Rosenbluth carries and SF+UnifiedQEL reshapes. |
| [C12 proton SF — Ankowski-Benhar-Sakuda 2024](prd-analyzer/spectral_function_c12_2024.md) | The 2024 `pke12_2024.table` SF fit to high-resolution NIKHEF (e,e′p) data; resolves the p-shell into discrete quasiparticle peaks vs the old broad bump, `n(k)` unchanged. |
| [EM-QES spline: Benhar vs ABS 2024 SF](pages/spline_22b_vs_33b_q2cut.md) | Grid `gmkspl` σ(E) for the UnifiedQEL-SF Q²-cut tunes t04–t08 on C12: `GEM26_22b` (Benhar SF, solid) vs `GEM26_33b` (ABS 2024 SF, dashed), same color per cut — the SF enters this xsec but shifts σ(E) only mildly. |

## Conventions

- **Style:** all figures follow the personal plot style in
  [`template/plot_style.py`](template/plot_style.py) (see the `plot-style` skill).
- **Generators:** one script per figure under [`template/`](template/), run with
  `pixi run python results/template/<script>.py`.
- **Pages:** one markdown page per figure under [`pages/`](pages/), linked from
  the index above.

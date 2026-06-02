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

## Conventions

- **Style:** all figures follow the personal plot style in
  [`template/plot_style.py`](template/plot_style.py) (see the `plot-style` skill).
- **Generators:** one script per figure under [`template/`](template/), run with
  `pixi run python results/template/<script>.py`.
- **Pages:** one markdown page per figure under [`pages/`](pages/), linked from
  the index above.

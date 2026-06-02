# prd-analyzer — (e,e′p) replication of Dutta et al. (JLab E91-013)

Analysis of the GENIE C12 EMQE grid samples against the Hall C **E91-013** quasi-elastic
(e,e′p) measurement ([nucl-ex/0303011](../../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)).
Targets **Table I row 5** — the **Q² = 1.28 GeV²** spectrometer setting at E_beam = 2.445 GeV —
and compares missing energy / missing momentum to the paper's Figs 9/10, **SF vs LFG**
(`GEM26_22a` vs `GEM26_11a`, cut t05).

## Files
- **`selection.py`** — the shared selection + missing-kinematics utility (imported by the plots):
  - `CUTS` — narrow HMS/SOS acceptance windows (center ± half-width) for the Q²=1.28 setting:
    `El` 1.725±0.005 GeV, `theta_e` 32±0.5°, `Tp` 0.700±0.025 GeV, `theta_p` 43±1°.
  - `load_events(path)` — reads a gst, builds the leading (post-FSI) proton and the per-event
    `E_miss = ω − T_p`, `p_miss = |q⃗ − p⃗_p|` (heavy-recoil approx), angles, mode flags.
  - `select_electron(ev)` — stage 1 (electron arm only: El ∧ θ_e — fixes Q²).
  - `select(ev)` — stage 2, full (e,e′p) coincidence (has_p ∧ El ∧ θ_e ∧ T_p ∧ θ_p).
  - `cut_summary(ev)` — N-1 cut flow.
- **`plot_missing.py`** — applies `select()` to the full 10M-event t05 samples and plots
  `E_m` and `p_m` (SF vs LFG) in the paper windows (E_m ≤ 80 MeV, |p_m| < 300 MeV/c).
- **`missing_e_p_q2_1.28.png`** — the output figure.

## Data
GENIE gst (post-FSI), `e⁻` on C12, E_beam = 2.445 GeV, tune cut **t05** (EM-MinQ2Limit = 1.18,
Q² ≈ 1.28). The grid outputs live on PNFS under
`…/genie_inclxx/GEM26_{11a,22a}_05_000/eminus_C12_*_gev/…`; `plot_missing.py` reads a local
stage of all 100 processes per config. The narrow spectrometer cuts keep ~0.04 % of events, so
the full 10M per sample is needed for usable statistics.

## Notes
- The EMQE samples are pure QEL (the `EMQE` generator list is QEL-EM only), so no RES/DIS split.
- `p_miss` is the unsigned magnitude (matches the paper); the p-shell dip at p_m≈0 is the l=1
  node, not a sign artifact.
- Q² is pinned by the electron arm: Q² = 4 E_beam E_e′ sin²(θ_e′/2) ≈ 1.28 GeV² for this window.

# prd-analyzer — (e,e′p) replication of Dutta et al. (JLab E91-013)

Analysis of the GENIE C12 EMQE grid samples against the Hall C **E91-013** quasi-elastic
(e,e′p) measurement ([nucl-ex/0303011](../../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)).
Targets **Table I row 5** — the **Q² = 1.28 GeV²** spectrometer setting at E_beam = 2.445 GeV —
applying the HMS/SOS acceptance cuts and comparing missing energy / missing momentum to the
paper's Figs 9/10, **SF vs LFG** (`GEM26_22a` vs `GEM26_11a`, cut t05). All figures share one
selection utility (`selection.py`).

## Figures

### 1. Missing energy & momentum (full coincidence, SF vs LFG)

![missing energy and momentum, SF vs LFG](missing_e_p_q2_1.28.png)

Reconstructed `E_m = ω − T_p` and `p_m = |q⃗ − p⃗_p|` after the full (e,e′p) selection
(N = 5120 LFG / 1332 SF). **LFG** is a sharp removal-energy spike (~37 MeV) with a low-`p_m`
peak; **SF** is a broad removal-energy distribution (~30–50 MeV) reaching higher `p_m` — the
spectral-function ground state vs the Fermi gas.

### 2. Cut-stage distributions

**Stage 1 — electron arm only (`El ∧ θ_e`):**

![stage 1 distributions](dists_stage1_electron.png)

`El`, `θ_e` sit in their windows and **Q² is pinned at ~1.28** (the electron arm fixes it),
while `T_p`, `θ_p`, `E_m`, `p_m` are still free/broad (N = 47443 / 39559). Grey dashed = the
acceptance windows (not yet applied to `T_p`/`θ_p` here).

**Stage 2 — full coincidence (`El ∧ θ_e ∧ T_p ∧ θ_p`):**

![stage 2 distributions](dists_stage2_full.png)

All four cut variables are now clamped to their windows, leaving the residual `Q²`, `E_m`, `p_m`
(N = 5120 / 1332) — the SF-vs-LFG difference surviving the spectrometer bite.

### 3. 2D missing energy vs momentum (stage × config)

![2D E_m vs p_m](missing_2d_e_vs_p.png)

`p_m` vs `E_m`, rows = stage 1 / stage 2, columns = LFG / SF. **SF shows the `(E_m, p_m)` ridge**
— removal energy rising with missing momentum, the spectral function's `P(k,E)` correlation —
while **LFG is a flat fixed-removal-energy band**, independent of `p_m`.

## Scripts
- **`selection.py`** — shared selection + missing-kinematics util:
  - `CUTS` — acceptance windows (center ± half-width): `El` 1.725±0.005 GeV, `theta_e` 32±0.5°,
    `Tp` 0.700±0.025 GeV, `theta_p` 43±1°.
  - `load_events(path)` — leading (post-FSI) proton, `E_m = ω − T_p`, `p_m = |q⃗ − p⃗_p|`, `Q2`,
    angles, mode flags.
  - `select_electron(ev)` — stage 1 (El ∧ θ_e). `select(ev)` — stage 2 (full). `cut_summary(ev)`.
- **`plot_missing.py`** → `missing_e_p_q2_1.28.png`
- **`plot_dists.py`** → `dists_stage1_electron.png`, `dists_stage2_full.png`
- **`plot_2d.py`** → `missing_2d_e_vs_p.png`

## Data
GENIE gst (post-FSI), `e⁻` on C12, E_beam = 2.445 GeV, tune cut **t05** (EM-MinQ2Limit = 1.18,
Q² ≈ 1.28). Grid outputs on PNFS under
`…/genie_inclxx/GEM26_{11a,22a}_05_000/eminus_C12_*_gev/…`; the plot scripts read a local stage
of all 100 processes (10M events) per config. The narrow spectrometer cuts keep ~0.04 % of
events, so the full 10M per sample is needed for usable statistics.

## Notes
- The EMQE samples are pure QEL (the `EMQE` generator list is QEL-EM only), so no RES/DIS split.
- `p_m` is the unsigned magnitude (matches the paper); the p-shell dip at `p_m≈0` is the l=1
  node, not a sign artifact.
- Q² is pinned by the electron arm: Q² = 4 E_beam E_e′ sin²(θ_e′/2) ≈ 1.28 GeV² for this window.

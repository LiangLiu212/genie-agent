# prd-analyzer — (e,e′p) replication of Dutta et al. (JLab E91-013)

Analysis of the GENIE C12 EMQE grid samples against the Hall C **E91-013** quasi-elastic
(e,e′p) measurement ([nucl-ex/0303011](../../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)).
Targets **Table I row 5** — the **Q² = 1.28 GeV²** spectrometer setting at E_beam = 2.445 GeV —
applying the HMS/SOS acceptance cuts and comparing missing energy / missing momentum to the
paper's Figs 9/10 across **four QE-EM models**:

| model | tune | QE-EM cross section + ground state | install |
|-------|------|------------------------------------|---------|
| **LFG + Rosenbluth** | `GEM26_11a_05_000` | Rosenbluth + Local Fermi Gas          | genie_inclxx |
| **SF + Rosenbluth**  | `GEM26_22a_05_000` | Rosenbluth + Benhar Spectral Function | genie_inclxx |
| **LFG + SuSAv2**     | `GEM21_11a_05_000` | SuSAv2-QEL + Local Fermi Gas (`HybridXSecAlgorithm`) | genie_dev |
| **SF + UnifiedQEL** *(Variant 05, focus model)* | `GEM26_22b_05_000` | UnifiedQEL (SF-consistent) + Benhar Spectral Function | genie_inclxx |

Three clean axes: **LFG vs SF** isolates the **ground state** at fixed Rosenbluth cross section;
**LFG+Rosenbluth vs LFG+SuSAv2** isolates the **QE-EM cross section** at fixed Local Fermi Gas;
**SF+Rosenbluth vs SF+UnifiedQEL** isolates the **QE-EM cross-section model** at fixed Benhar
spectral-function ground state. **SF + UnifiedQEL (Variant 05)** is the focus model — drawn on
top and emphasized (thick C3 line) in every figure.

Each is ~10M `e⁻`-on-C12 events at generation cut **t05** (EM-MinQ2Limit = 1.18 GeV², so Q² ≥ 1.18
brackets the Q² = 1.28 setting). The samples are **streamed straight off dCache over XRootD** — no
local copy — see *Workflow*. Note SuSAv2 was generated with the `genie_dev` build, the two
Rosenbluth samples with `genie_inclxx` (a build difference to bear in mind).

## Workflow (XRootD stream → cache → plot)

The grid gst lives on `/pnfs` (~6–9 GB/model). Instead of pulling it, the analysis streams it over
XRootD and caches only the tiny selected subset:

1. **`samples.py`** — the 4-model registry. Maps `/pnfs/dune/…` →
   `root://fndca1.fnal.gov:1094//pnfs/fnal.gov/usr/dune/…` (dCache namespace) and lists each
   model's gst URLs (`gst_urls(model)`).
2. **`build_cache.py`** — streams every gst over XRootD, applies the stage-1 (electron-arm)
   selection, and writes `cache/<model>.npz` (~2 MB each: the ~40k stage-1 survivors + the stage-2
   mask + total event count). Needs a dCache token:
   ```bash
   export BEARER_TOKEN_FILE=<token>          # refresh with: htgettoken -i dune
   pixi run python results/prd-analyzer/build_cache.py        # ~7 min, 40M events
   ```
   Re-run only when the sample list or selection changes.
3. **`plot_*.py`** — read the cache (instant) and draw the figures.

Streaming needs `xrootd` + `fsspec-xrootd` in the pixi env (uproot opens `root://` directly).
Because the four models have **different total QE cross sections**, the 1D overlays are
**area-normalized** (shape comparison); the selected count `N` — a rate proxy — is in each legend.

## Selection & cuts

Replicates the E91-013 **Q² = 1.28 GeV²** spectrometer setting (Dutta et al., Table I row 5): the
narrow HMS/SOS acceptance windows on the scattered electron and the leading proton, reconstructed
from the GENIE gst. All of this lives in `selection.py`.

**Leading (knocked-out) proton.** The reconstructed proton is the **highest-momentum final-state
proton** in the event — post-FSI, `pdgf == 2212`, maximal `pf`
(`lead = ak.argmax(ak.where(isp, pf, -1))`). Its 4-momentum gives the proton kinematic energy
`T_p = E_p − m_p` (with `m_p` from the PDG module) and angle `θ_p = arccos(p_z/|p⃗|)`. An event with
**no** final-state proton (`has_p = false`) cannot form the coincidence and is dropped at stage 2.

**Reconstructed per-event kinematics:**
- `ω = E_beam − E_e′` — energy transfer
- `q⃗ = p⃗_beam − p⃗_e′` — 3-momentum transfer (`Q²` is read from the gst `Q2` branch)
- `θ_e′ = arccos(cos θ_l)` — scattered-electron angle
- `E_m = ω − T_p` — **missing energy** (heavy-recoil approx, `T_{A−1} ≈ 0`)  [MeV]
- `p_m = |q⃗ − p⃗_p|` — **missing momentum** (unsigned magnitude)  [MeV/c]

**The cuts** — acceptance window = centre ± half-width (`selection.CUTS`):

| cut | variable | window | paper (E91-013) | arm |
|-----|----------|--------|-----------------|-----|
| `El`      | scattered e′ energy `E_e′` | 1.725 ± 0.005 GeV | E_e′ = 1.725 GeV         | electron |
| `theta_e` | scattered e′ angle `θ_e′`  | 32.0 ± 0.5°       | θ_e′ = 32°               | electron |
| `Tp`      | leading-proton KE `T_p`    | 0.700 ± 0.025 GeV | T_p = 700 MeV            | proton   |
| `theta_p` | leading-proton angle `θ_p` | 43.0 ± 1.0°       | θ_p ≈ 43.5° (conjugate)  | proton   |

`Q²` is **not** cut directly — it is **pinned** by the electron arm:
`El ∧ θ_e′ ⇒ Q² = 4 E_beam E_e′ sin²(θ_e′/2) ≈ 1.28 GeV²`.

**Two stages** (`select_electron` → `select`):
- **Stage 1 — electron arm**: `El ∧ θ_e′`. Tags the scattered electron and fixes Q²; the proton
  side is still unconstrained. This is what `build_cache.py` caches.
- **Stage 2 — full (e,e′p) coincidence**: `has_p ∧ El ∧ θ_e′ ∧ T_p ∧ θ_p`. Adds the leading-proton
  KE and angle windows — the coincidence the HMS/SOS spectrometer pair actually measures.

Acceptance is tight: ~0.4 % of events survive stage 1, ~0.01–0.05 % stage 2 (why the full
10M/model is needed). `cut_summary(ev)` prints the N−1 cut flow per variable.

## Figures

### 1. Missing energy & momentum (full coincidence)

![missing energy and momentum](missing_e_p_q2_1.28.png)

Reconstructed `E_m = ω − T_p` and `p_m = |q⃗ − p⃗_p|` after the full (e,e′p) selection
(N = 5120 LFG / 1332 SF / 3462 SuSAv2 / **2180 SF+UnifiedQEL**, from 10M each). **LFG** is a sharp
removal-energy spike (~36 MeV) with a low-`p_m` peak; **SF** is a broad removal-energy distribution
(~30–50 MeV) reaching out to a high-`p_m` shoulder (~120 MeV/c) — the spectral function's `P(k,E)`
tail; **SuSAv2** peaks *lower* in `E_m` (~28 MeV) with a soft tail to zero, and a low-`p_m` shape
closer to LFG. **SF + UnifiedQEL (Variant 05, thick red, on top)** peaks markedly *lower* in `E_m`
(~15–20 MeV) with a broad low-energy shoulder — the SF-consistent (CBF) cross section reshapes the
removal-energy distribution relative to factorized SF+Rosenbluth at the *same* Benhar ground state,
while its `p_m` shape tracks SF (both spectral-function). That contrast (`22a` ↔ `22b`) isolates the
QE-EM cross-section model at fixed SF ground state. At fixed luminosity (SF and LFG share the
Rosenbluth σ) LFG keeps **3.8×** more coincidences than SF — Fermi smearing pushes SF protons out of
the tight HMS window.

### 2. Cut-stage distributions

**Stage 1 — electron arm only (`El ∧ θ_e`):**

![stage 1 distributions](dists_stage1_electron.png)

`El`, `θ_e` sit in their windows and **Q² is pinned at ~1.28** (the electron arm fixes it), while
`T_p`, `θ_p`, `E_m`, `p_m` are still free/broad (N = 47443 LFG / 39559 SF / 39866 SuSAv2 /
41697 SF+UnifiedQEL). Grey dashed = the acceptance windows (not yet applied to `T_p`/`θ_p` here).

**Stage 2 — full coincidence (`El ∧ θ_e ∧ T_p ∧ θ_p`):**

![stage 2 distributions](dists_stage2_full.png)

All four cut variables are clamped to their windows, leaving the residual `Q²`, `E_m`, `p_m`
(N = 5120 / 1332 / 3462 / 2180) — the model differences surviving the spectrometer bite.

### 3. 2D missing energy vs momentum (stage × model)

![2D E_m vs p_m](missing_2d_e_vs_p.png)

`p_m` vs `E_m`, rows = stage 1 / stage 2, columns = LFG / SF / SuSAv2 / SF+UnifiedQEL (Variant 05,
rightmost). **SF, SuSAv2 and SF+UnifiedQEL show the `(E_m, p_m)` ridge** — removal energy rising with
missing momentum, the `P(k,E)` correlation (the two SF models share the Benhar ground state) — while
**LFG is a flat fixed-removal-energy band**, independent of `p_m`.

## Scripts
- **`samples.py`** — 4-model registry; `xrootd_url()`, `gst_urls(model)`, `load_cache(model)`,
  `lw(model)`/`zorder(model)` (the `HIGHLIGHT` = Variant 05 gets a thick line, drawn on top).
- **`build_cache.py`** — XRootD stream + stage-1 selection → `cache/<model>.npz`.
- **`selection.py`** — shared selection + missing-kinematics util (unchanged; `load_events(path)`
  works on a local path *or* a `root://` URL):
  - `CUTS` — acceptance windows (center ± half-width): `El` 1.725±0.005 GeV, `theta_e` 32±0.5°,
    `Tp` 0.700±0.025 GeV, `theta_p` 43±1°.
  - `load_events` — leading (post-FSI) proton, `E_m = ω − T_p`, `p_m = |q⃗ − p⃗_p|`, `Q2`, angles.
  - `select_electron(ev)` — stage 1 (El ∧ θ_e). `select(ev)` — stage 2 (full). `cut_summary(ev)`.
- **`plot_missing.py`** → `missing_e_p_q2_1.28.png`
- **`plot_dists.py`** → `dists_stage1_electron.png`, `dists_stage2_full.png`
- **`plot_2d.py`** → `missing_2d_e_vs_p.png`

## Data
GENIE gst (post-FSI), `e⁻` on C12, E_beam = 2.445 GeV, cut **t05** (EM-MinQ2Limit = 1.18, Q² ≈ 1.28),
10M events/model, on dCache:
```
/pnfs/dune/scratch/users/liangliu/jobsub-agent/prd_paper/EM/
  genie_inclxx/GEM26_11a_05_000/eminus_C12_20260602-131202_gev/…   (LFG,        100×100k)
  genie_inclxx/GEM26_22a_05_000/eminus_C12_20260602-131216_gev/…   (SF,         100×100k)
  genie_dev/GEM21_11a_05_000/eminus_C12_20260601-153754_gev/…      (SuSAv2,      20×500k)
  genie_inclxx/GEM26_22b_05_000/eminus_C12_20260604-103343_gev/…   (UnifiedQEL, 100×100k)
```
streamed over XRootD (never copied locally). The narrow spectrometer cuts keep ~0.4 % at stage 1 and
~0.01–0.05 % at stage 2, so the full 10M/model is needed for usable statistics.

## Notes
- The EMQE samples are pure QEL (the `EMQE` generator list is QEL-EM only), so no RES/DIS split.
- 1D overlays are **area-normalized** — the four models have different total σ, so raw counts are
  not a fair overlay; the rate information lives in the legend `N` (and the stage-2 efficiencies).
- `p_m` is the unsigned magnitude (matches the paper); the p-shell dip at `p_m≈0` is the l=1 node.
- SuSAv2 (`genie_dev`) vs the Rosenbluth pair (`genie_inclxx`) is a cross-build comparison.

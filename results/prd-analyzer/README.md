# prd-analyzer — (e,e′p) replication of Dutta et al. (JLab E91-013)

Analysis of the GENIE C12 EMQE grid samples against the Hall C **E91-013** quasi-elastic
(e,e′p) measurement ([nucl-ex/0303011](../../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)).
Targets **Table I row 5** — the **Q² = 1.28 GeV²** spectrometer setting at E_beam = 2.445 GeV —
applying the HMS/SOS acceptance cuts and comparing missing energy / missing momentum to the
paper's Figs 9/10 across **five QE-EM models**:

| model | tune | QE-EM cross section + ground state | install |
|-------|------|------------------------------------|---------|
| **LFG + Rosenbluth** | `GEM26_11a_05_000` | Rosenbluth + Local Fermi Gas          | genie_inclxx |
| **SF + Rosenbluth**  | `GEM26_22a_05_000` | Rosenbluth + Benhar Spectral Function | genie_inclxx |
| **LFG + SuSAv2**     | `GEM21_11a_05_000` | SuSAv2-QEL + Local Fermi Gas (`HybridXSecAlgorithm`) | genie_dev |
| **SF(2024) + UnifiedQEL** | `GEM26_33b_05_000` | UnifiedQEL (SF-consistent) + 2024 Ankowski-Benhar-Sakuda SF | genie_inclxx |
| **SF + UnifiedQEL** *(Variant 05, focus model)* | `GEM26_22b_05_000` | UnifiedQEL (SF-consistent) + Benhar Spectral Function | genie_inclxx |

Four clean axes: **LFG vs SF** isolates the **ground state** at fixed Rosenbluth cross section;
**LFG+Rosenbluth vs LFG+SuSAv2** isolates the **QE-EM cross section** at fixed Local Fermi Gas;
**SF+Rosenbluth vs SF+UnifiedQEL** isolates the **QE-EM cross-section model** at fixed Benhar
spectral-function ground state; **SF vs SF(2024), both UnifiedQEL,** isolates the **spectral
function itself** — the old broad-p-shell `pke12_tot` vs the 2024 quasiparticle-peak
`pke12_2024` ([page](spectral_function_c12_2024.md)) — at fixed SF-consistent cross section.
**SF + UnifiedQEL (Variant 05)** is the focus model — drawn on top and emphasized (thick C3
line) in every figure, with its new-SF sibling (`33b`, C4) beside it.

Each is ~10M `e⁻`-on-C12 events at generation cut **t05** (EM-MinQ2Limit = 1.18 GeV², so Q² ≥ 1.18
brackets the Q² = 1.28 setting). The samples are **streamed straight off dCache over XRootD** — no
local copy — see *Workflow*. Note SuSAv2 was generated with the `genie_dev` build, the other
four samples with `genie_inclxx` (a build difference to bear in mind).

## Workflow (XRootD stream → cache → plot)

The grid gst lives on `/pnfs` (~6–9 GB/model). Instead of pulling it, the analysis streams it over
XRootD and caches only the tiny selected subset:

1. **`samples.py`** — the 5-model registry. Maps `/pnfs/dune/…` →
   `root://fndca1.fnal.gov:1094//pnfs/fnal.gov/usr/dune/…` (dCache namespace) and lists each
   model's gst URLs (`gst_urls(model)`).
2. **`build_cache.py`** — streams every gst over XRootD (parallel worker processes, `WORKERS`
   env, default 8), applies the stage-1 (electron-arm) selection, and writes
   `cache/<model>.npz` (the stage-1 survivors + the stage-2 mask + total event count). Needs a
   dCache token:
   ```bash
   export BEARER_TOKEN_FILE=<token>          # refresh with: htgettoken -i dune
   pixi run python results/prd-analyzer/build_cache.py              # all models, branch CUTS
   pixi run python results/prd-analyzer/build_cache.py --superset   # loosest theta_e (+-6)
   pixi run python results/prd-analyzer/build_cache.py UnifiedQEL2024   # just one model
   ```
   Re-run only when the sample list or selection changes (new models: pass their keys).
   **Superset workflow** (preferred with the 1B samples): `--superset` streams each sample once
   with the loosest electron window into `cache/superset/<model>.npz`; each angle-cut branch
   then derives its own `cache/<model>.npz` locally with **`recut_cache.py`** (re-applies that
   branch's `selection.CUTS`, recomputes the stage-2 mask from the cached columns — verified
   bit-identical to a direct build) — no re-streaming per branch.
3. **`plot_*.py`** — read the cache (instant) and draw the figures.

Streaming needs `xrootd` + `fsspec-xrootd` in the pixi env (uproot opens `root://` directly).
Because the five models have **different total QE cross sections**, the 1D overlays are
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

**Three stages** (`select_electron` → `select_proton_e` → `select`):
- **Stage 1 — electron arm**: `El ∧ θ_e′`. Tags the scattered electron and fixes Q²; the proton
  side is still unconstrained. This is what `build_cache.py` caches.
- **Stage 2.1 — + proton energy, θ_p free**: `has_p ∧ El ∧ θ_e′ ∧ T_p`. Adds only the
  leading-proton KE window, leaving the proton angle unconstrained — isolates what the `T_p`
  window does before the conjugate-angle window carves the momentum acceptance. Computed from
  the stage-1 cache (`selection.cache_stage_masks`), no re-streaming.
- **Stage 2 — full (e,e′p) coincidence**: `has_p ∧ El ∧ θ_e′ ∧ T_p ∧ θ_p`. Adds the leading-proton
  angle window — the coincidence the HMS/SOS spectrometer pair actually measures.

Acceptance is tight: ~0.4 % of events survive stage 1, ~0.1–0.2 % stage 2.1, ~0.01–0.05 % stage 2
(why the full 10M/model is needed). `cut_summary(ev)` prints the N−1 cut flow per variable.

## Figures

### 0. Input ground state — Benhar spectral function (see [page](spectral_function_c12.md))

![C12 Benhar spectral function P(k,E)](spectral_function_c12.png)

The **input** both SF models sample from, read straight from `pke12_tot.data`: `P(k,E)` in the
(missing energy, missing momentum) plane plus its `f(E)`/`n(k)` marginals (`∫4πk²P dk dE = 1.0000`,
`f(E)` peak 17.5 MeV, `n(k)` peak 150 MeV/c). SF+UnifiedQEL (`22b`) propagates this `f(E)` into the
outgoing kinematics (with a De Forest downward reshaping); SF+Rosenbluth (`22a`) does **not** — its
pre-FSI reconstructed `E_m` is a fixed 16.0-MeV delta (section 9), so the input `f(E)` shows up only
in `n(k)`/`p_m` for that tune. Full write-up on the [dedicated page](spectral_function_c12.md).

### 0b. Updated ground state — Ankowski-Benhar-Sakuda 2024 (see [page](spectral_function_c12_2024.md))

![2024 C12 proton SF vs old pke12_tot](spectral_function_c12_2024_vs_old.png)

The 2024 Ankowski-Benhar-Sakuda ¹²C proton SF (`data/pke12_2024.table`), fit to high-resolution
NIKHEF (e,e′p) data. It **resolves the p-shell into discrete quasiparticle peaks** (15.9 / ~18.5 /
~21 MeV) where the old `pke12_tot` had one broad 5-MeV bump, while leaving `n(k)` essentially
unchanged. Full write-up on the [dedicated page](spectral_function_c12_2024.md).

### 1. Missing energy & momentum (full coincidence)

![missing energy and momentum](missing_e_p_q2_1.28.png)

Reconstructed `E_m = ω − T_p` and `p_m = |q⃗ − p⃗_p|` after the full (e,e′p) selection
(N = 5120 LFG / 1332 SF / 3462 SuSAv2 / 2161 SF(2024)+UnifiedQEL / **2180 SF+UnifiedQEL**, from
10M each). **LFG** is a sharp removal-energy spike (~36 MeV) with a low-`p_m` peak; **SF** is a
broad removal-energy distribution (~30–50 MeV) reaching out to a high-`p_m` shoulder (~120 MeV/c)
— the spectral function's `P(k,E)` tail; **SuSAv2** peaks *lower* in `E_m` (~28 MeV) with a soft
tail to zero, and a low-`p_m` shape closer to LFG. **SF + UnifiedQEL (Variant 05, thick red, on
top)** peaks markedly *lower* in `E_m` (~15–20 MeV) with a broad low-energy shoulder — the
SF-consistent (CBF) cross section reshapes the removal-energy distribution relative to factorized
SF+Rosenbluth at the *same* Benhar ground state, while its `p_m` shape tracks SF (both
spectral-function). That contrast (`22a` ↔ `22b`) isolates the QE-EM cross-section model at fixed
SF ground state. **SF(2024) + UnifiedQEL (`33b`, purple)** swaps in the 2024
Ankowski-Benhar-Sakuda SF at the same cross section: its `E_m` collapses into a sharp ~16 MeV
spike — the resolved p-shell quasiparticle peak of `pke12_2024`, vs the old SF's broad 5-MeV-wide
p-shell bump smeared further by De Forest weighting — while its `p_m` shape stays on top of `22b`
(`n(k)` essentially unchanged). That contrast (`22b` ↔ `33b`) is a pure ground-state-input effect,
directly visible in the spectrometer window. At fixed luminosity (SF and LFG share the Rosenbluth
σ) LFG keeps **3.8×** more coincidences than SF — Fermi smearing pushes SF protons out of the
tight HMS window.

**Stage 2.1 — the same observables with θ_p free:**

![missing energy and momentum, stage 2.1](missing_e_p_q2_1.28_stage21.png)

Dropping only the proton-angle window (N = 20840 LFG / 9483 SF / 16260 SuSAv2 /
14048 SF(2024)+UnifiedQEL / 14002 SF+UnifiedQEL) leaves `E_m` essentially unchanged — the shell
structure is set by `ω − T_p`, not by the angle — but transforms `p_m`: the spectral-function
models now peak broadly at ~120–140 MeV/c (their full momentum content within the `T_p` slice)
instead of being clipped to low `p_m`. The comparison with the stage-2 figure shows directly that
the **conjugate θ_p window is what selects low missing momentum** in the spectrometer coincidence.

### 2. Cut-stage distributions

**Stage 1 — electron arm only (`El ∧ θ_e`):**

![stage 1 distributions](dists_stage1_electron.png)

`El`, `θ_e` sit in their windows and **Q² is pinned at ~1.28** (the electron arm fixes it), while
`T_p`, `θ_p`, `E_m`, `p_m` are still free/broad (N = 47443 LFG / 39559 SF / 39866 SuSAv2 /
41164 SF(2024)+UnifiedQEL / 41697 SF+UnifiedQEL). Grey dashed = the acceptance windows (not yet
applied to `T_p`/`θ_p` here).

**Stage 2.1 — + proton KE, θ_p free (`El ∧ θ_e ∧ T_p`):**

![stage 2.1 distributions](dists_stage21_proton_e.png)

`T_p` is clamped to its window while `θ_p` stays free (N = 20840 / 9483 / 16260 / 14048 / 14002):
the proton-angle panel shows each model's full conjugate-angle distribution around the dashed
43 ± 1° window — broadest for the spectral-function models (Fermi motion tilts the proton away
from the q⃗ direction), narrowest for LFG — and `p_m` is correspondingly broad.

**Stage 2 — full coincidence (`El ∧ θ_e ∧ T_p ∧ θ_p`):**

![stage 2 distributions](dists_stage2_full.png)

All four cut variables are clamped to their windows, leaving the residual `Q²`, `E_m`, `p_m`
(N = 5120 / 1332 / 3462 / 2161 / 2180) — the model differences surviving the spectrometer bite.
The `33b` p-shell spike at `E_m` ≈ 16 MeV stands out against the `22b` shoulder.

### 3. 2D missing energy vs momentum (stage × model)

![2D E_m vs p_m](missing_2d_e_vs_p.png)

`p_m` vs `E_m`, rows = stage 1 / stage 2.1 (+ `T_p`, θ_p free) / stage 2 (full), columns =
LFG / SF / SuSAv2 / SF(2024)+UnifiedQEL / SF+UnifiedQEL (Variant 05, rightmost). **The
spectral-function models show the `(E_m, p_m)` ridge** — removal energy rising with missing
momentum, the `P(k,E)` correlation — while **LFG is a flat fixed-removal-energy band**,
independent of `p_m`. In the `33b` column the ridge sits on the sharp 16-MeV quasiparticle line
of the 2024 SF instead of the old broad p-shell band. Reading down a column: the `T_p` window
(row 2) keeps the ridge intact across the full `p_m` range; the θ_p window (row 3) then cuts it
off at low missing momentum.

### 4. Missing momentum by shell (E_m slices, both stages)

![missing momentum by shell](missing_p_shells.png)

`p_m` sliced by missing-energy window — **p-shell: 10 < E_m < 25 MeV** (left), **s-shell:
30 < E_m < 50 MeV** (right) — for stage 1 (top), stage 2.1 (`T_p` in window, θ_p free, middle)
and stage 2 (bottom), area-normalized. A model with N < 50 in a window is listed in the legend
but not drawn (a near-empty density histogram is all spikes).

The two columns show the textbook shell signature in the observable: the **p-shell slice rises
from a node at `p_m` ≈ 0 to a broad ~100 MeV/c peak** (l = 1), while the **s-shell slice peaks at
low `p_m`** (l = 0). Which models populate which window is itself the story:

- **LFG** (fixed removal energy ≈ 36 MeV) has essentially **no p-shell strength** (stage-1
  N = 1, stage-2 N = 0) — everything sits in the 30–50 MeV window with its narrow low-`p_m` peak.
- **SF + Rosenbluth** is nearly as empty in the p-window (N = 27 / 1): without the De Forest
  reshaping its `E_m` strength stays at 30–50 MeV.
- **SuSAv2** populates the 10–25 MeV window heavily (stage-1 N = 13543), but as a Fermi-gas model
  it has no shells — the slice is just the low-`E_m` kinematic tail of its distribution; its
  s-window content is marginal (stage-2 N = 32, not drawn).
- **The two SF + UnifiedQEL models** are the only ones with genuine strength in *both* windows
  (p: 13625 `33b` / 13929 `22b`; s: 6055 / 5921 at stage 1). Their p-shell `p_m` shapes lie on
  top of each other — the 2024 SF changes *where* the p-shell sits in `E_m` (the 16-MeV
  quasiparticle peak vs the old broad bump) but not its momentum content (`n(k)` unchanged). In
  the s-window the `33b` slice is the cleaner s-shell sample: its resolved p-shell peaks sit
  below 25 MeV, while the old SF leaks smeared p-shell strength into 30–50 MeV.

### 5. Missing energy vs Dutta Fig. 9 — spectrometer acceptance + occupancy normalization

![E_m vs Dutta fig9](em_dutta_fig9_q1p28.png)

The direct data overlay: `E_m` through the **physical HMS×SOS acceptance** instead of the
stage-2 windows. `acceptance.py` cuts in **spectrometer coordinates** (per-arm `delta`/`yptar`/
`xptar` boxes about the Q² = 1.28 central settings — HMS e′: 1.725 GeV/c @ 32.0°, |δ|<8 %,
|y′|<27.5 mrad; SOS p: 1.341 GeV/c @ 43.5°, |δ|<20 %, |y′|<57 mrad, |x′|<37.2 mrad — from
[report/simc-eep-normalization.md](../../report/simc-eep-normalization.md) §4.5/4.7,
collimator-derived). Each event is rotated about the beam to put e′ in the spectrometer plane
(the MC is azimuthally symmetric; the proton keeps its relative out-of-plane angle, so the SOS
box carves the physical coincidence acceptance). `E_m = ω − T_p − T_rec` (paper definition,
recoil included), 5-MeV data bins, `p_m` < 300 MeV/c (automatically satisfied in this
acceptance). Acceptance efficiency ~1.4–2.6 % (N = 135k–260k from 10M streamed/model).

**Normalization**: the fig9 data are on the **full-occupancy (IPSM) scale** — their integral is
Σ·5 MeV = 6.08 ≈ Z, not the raw absorbed yield (see
[open_questions](../../papers/nucl-ex_0303011/open_questions.md)) — so each model is scaled to
the same integral over 0–80 MeV (shape + occupancy comparison). Data error bars: inner = the
data file's statistical errors (0.8–3.3 %); outer grey = total point-to-point per the
open-questions prescription (stat ⊕ 2 % ⊕ 5 %, the two p-shell bins set to the published
pixel-measured bars 8.1 %/4.7 %).

**Read**: the two **SF + UnifiedQEL** variants are closest (χ²/13 ≈ 2.2k vs 21k–56k for the
rest — the tiny data errors make χ² a ranking, not a goodness); they put the p-shell peak in
the right bin but ~25 % low and spill strength into 20–50 MeV, plus unphysical sub-threshold
strength at E_m < 16 MeV where the data are zero. SF + Rosenbluth peaks 20–35 MeV too high
(no De Forest reshaping); LFG is a delta-spike at ~36 MeV (1.2 MeV⁻¹, off scale); SuSAv2 sits
between. At this 5-MeV binning the 2024-SF quasiparticle structure is washed out — `33b` ≈
`22b`.

**Caveats**: (i) the t05 generation cut (Q² ≥ 1.18) clips the low-Q² corner of the acceptance
(which extends to ≈1.07) — ~18 % of accepted events sit within 0.04 GeV² of the boundary; all
five models are clipped identically and the E_m shape impact is second-order. (ii) The HMS
octagonal collimator is modeled as its bounding rectangle (~10 % more solid angle). (iii) The
electron out-of-plane window is treated as fully accepting (the e′-plane rotation). (iv) The
data are deradiated but still FSI-distorted (S^D); GENIE events are post-FSI — consistent in
spirit, but the data's absolute scale is convention-defined (occupancy), so only shapes and
relative occupancies are compared.

### 6. Uncut distributions in the Q² slice — Q² = 1.28 ± 5 % only

![Q2-window distributions](dists_q2window.png)

The no-cut counterpart of the cut-stage figures: **all electron and proton cuts removed**, only
`|Q²/1.28 − 1| ≤ 5 %` (Q² ∈ [1.216, 1.344], fully inside the t05 generation cut — no boundary
clip). 4 files/model streamed (2M events), ~27–30 % selected (N = 538k–592k), cached in
`cache/q2window/`. All seven variables (El, θ_e′, T_p, θ_p, Q², E_m, p_m), area-normalized;
proton panels implicitly drop the ~21 % of events with no final-state proton (neutron knockout).
Grey dashed lines mark the applied Q² window and, on the El/θ_e′/T_p/θ_p panels, the HMS/SOS
acceptance windows (in-plane projections, derived from `acceptance.py` — **not** applied here):
El ∈ [1.587, 1.863] GeV, θ_e′ = 32.0 ± 1.58°, T_p ∈ [0.487, 0.924] GeV, θ_p = 43.5 ± 3.26°.

**Raw event counts companion** (`dists_q2window_counts.png`): the same seven panels in
events/bin — directly comparable rates at equal ntot = 2M generated/model. SuSAv2's higher
in-window rate (N = 592k vs ~540k) is explicit there, as are the absolute E_m peak heights
(LFG spike ~193k/bin; 2024-SF quasiparticle peak ~120k vs old-SF ~95k) and the near
model-independent ~11k/bin low-T_p FSI population (an INTRANUKE effect, not a cross-section
one).

![Q2-window distributions, raw counts](dists_q2window_counts.png)

**Read**: with the spectrometer bite removed, `El`/`θ_e′` are the smooth QE peak (1.75 GeV,
~31.5°) — the Q² window alone constrains them only weakly. `T_p` is double-peaked: the QE bump
at ~0.65 GeV plus a low-`T_p` (~0.1–0.2 GeV) population of FSI-rescattered / secondary leading
protons that the spectrometer windows normally remove; correspondingly `θ_p` has a long tail
beyond the ~45° conjugate peak and `p_m` a flat FSI tail out to 800 MeV/c. `E_m` remains the
model discriminator even uncut: LFG spike at ~36 MeV, SF+Rosenbluth at ~40 MeV with the broad
shoulder, SuSAv2 low and broad, the two SF+UnifiedQEL variants at ~16–18 MeV (the 2024 SF
visibly sharper — the quasiparticle p-shell peak survives without any acceptance shaping).

### 7. Extracted distorted spectral function S^D — absolute scale, no area matching

![S^D vs fig9](sd_extraction_fig9.png)

Dutta's own PWIA estimator run on the GENIE events
([plan](../../.claude/plans/genie-experimental-spectral-function.md)): per (E_m, p_m) bin,
`S^D = [σ_tot/N_gen · Σ 1/(E_p·p_p·σ_cc1)] / H`, with σ_cc1 from `deforest.py` (the same
off-shell prescription the experiment used), σ_tot from each production's own spline, and H
the flat-MC phase space (`phase_space_h.py`). `y(Em) = Σ S^D·(4π/3)Δp_m³` over p_m < 300
reproduces the fig9 observable in MeV⁻¹ — **absolute**, unlike the area-matched overlay of
section 5. C^rad = 1 (GENIE is radiation-free = deradiated data). 2D maps
(`sd_2d_maps.png`): the SF models show the P(k,E) ridge, LFG the fixed-E_m stripe, in both
fiducials.

**Window integrals** ∫S^D dEm d³pm (0 ≤ E_m < 80, p_m < 300), vs the paper's absorbed scale
T/1.11 × 6 ≈ 3.24 and the data file's occupancy integral 6.08:

| model | I | I/3.24 | I/6.08 |
|---|---|---|---|
| LFG + Rosenbluth | 3.505 ± 0.008 | 1.08 | 0.58 |
| SF + Rosenbluth | 2.978 ± 0.005 | 0.92 | 0.49 |
| LFG + SuSAv2 | 3.221 ± 0.006 | 0.99 | 0.53 |
| SF(2024) + UnifiedQEL | 2.175 ± 0.004 | 0.67 | 0.36 |
| SF + UnifiedQEL | 2.137 ± 0.004 | 0.66 | 0.35 |

**Read**: the Rosenbluth/SuSAv2 models land within ±9 % of the experiment's absorbed
strength (I/6.08 ≈ 0.49–0.58 vs the measured T/1.11 = 0.54 guide in the ratio panel) —
GENIE's absolute in-window (e,e'p) retention quantitatively matches E91-013's
transparency-suppressed yield. The UnifiedQEL pair sits at 0.66× that, directly tracking its
smaller σ_tot (15.6/23.6 nb): dividing all models by the *same* σ_cc1 (as the experiment
does) exposes the SF-consistent cross section's lower absolute yield. Shapes: the SF-model
tails reach GENIE/data ≈ 1 above E_m ≈ 60 MeV while the p-shell peak region sits at 0.2–0.5.
**Cross-fiducial validation**: UnifiedQEL extracted through both fiducials (H volumes
differing by orders of magnitude) agrees bin-by-bin to median a/b = 0.946, median
|pull| = 0.64 (232 common bins); the acceptance-fiducial open circles track the q2win curve.
Caveats: the acceptance variant covers only part of the p_m sphere (its y(Em) is a lower
bound); data occupancy normalization is the standing open question.

### 8. Ground-state inputs vs Dutta Fig. 9

![input SF f(E) vs fig9](sf_input_em_fig9.png)

The undistorted INPUT tables — old Benhar `pke12_tot` (22a/22b) and the 2024
Ankowski-Benhar-Sakuda SF (33b) — as `Z·∫_{k<300} 4πk²P dk`, i.e. the fig9 observable with
no FSI, no σ weighting, no acceptance; both on the occupancy scale like the data. Key
numbers: each table holds **5.42 protons inside k < 300 MeV/c** (5.25 within E < 80) —
6/5.42 = **1.11, exactly the correlation factor** E91-013 applied for out-of-window SRC
strength; and the data's peak bin sits 12 % above the inputs (0.571 vs 0.51), again ≈ the
1.11 rescale. Shape-wise the inputs already track the data closely across the s-shell
(30–50 MeV) and tail; the visible differences are the data's wider p-shell (the 22.5 MeV
point at 0.269 vs ~0.15 input — FSI smearing lives in the data's S^D shape) and the 2024
table's resolved quasiparticle spikes (faint continuous curve, clipped). Together with
section 7 this brackets the physics: input (no FSI) ≈ data/1.11; extracted S^D (with FSI)
≈ data×0.54.

### 9. Pre-FSI missing energy — the sampled ground state, no cuts

![pre-FSI Em vs fig9](em_prefsi_fig9.png)

`E_m = ω − T_p − T_rec` from the **primary (pre-INTRANUKE) proton**, proton-channel events
only (hitnuc = p, 68.7–69.8 % of each sample — exactly σ_p/σ_tot from the splines), no
detector cuts; occupancy scale `y = Z·hist(p_m<300)/(N_p·5 MeV)` (full-p_m integral ≡ 6 by
construction; plotted E_m<80 integrals 5.2–6.0 vs input tables' 5.25, data 6.08).

**Findings** (this figure corrects the section 0/1 reading of the `22a` E_m shape):
- **The Rosenbluth pair (LFG `11a`, SF `22a`) has pre-FSI E_m ≡ 15.957 MeV = S_p — a
  single-bin delta (1.20/1.09 MeV⁻¹), event-by-event exact.** These a-tunes run the
  install-default OLD QEL-EM chain (`FermiMover` + `QELKinematicsGenerator/EM` + …),
  which closes energy conservation against an on-shell ground-state ¹¹B remnant — the
  sampled removal energy is *not* propagated into the outgoing proton (for `22a` the
  Benhar `f(E)` never reaches E_m — only `n(k)` survives into `p_m`). Their post-FSI
  spike at ~36 MeV (sections 1/6) is the old chain's **`NucBindEnergyAggregator` module
  subtracting RFG-NucRemovalE = 20 MeV after transport** (15.96 + 20.0 = 35.96) — not an
  hA transport effect. The b-tunes override QEL-EM (tune-tarball `EventGenerator.xml`)
  with the new 8-module `QELEventGenerator/EM-Default` chain — no aggregator, hence no
  shift (pre-FSI median 19.2 MeV vs post-FSI peak 15–20 MeV). All GEM26 tunes use
  hA2018 transport (`HadronTransp-Model` in CommonParam); `genie-agent/tunes/` is
  byte-identical to the published CVMFS tune tarball (verified with `diff -rq`).
- **The UnifiedQEL pair propagates the input**: broad distributions (p95 ≈ 60 MeV) that
  ride on their dashed input curves — and on the data — across the s-shell and tail
  (25–80 MeV), with the De Forest reshaping moving peak strength down in E_m
  (`22b` 0.436 vs input 0.51 at [15,20); `33b` split 0.295/0.292 across [10,20)).
- **SuSAv2** spreads E_m broadly around ~14 MeV including sub-threshold and negative
  values (p5 = −3.6 MeV) — a Fermi-gas energy-balance prescription, no shell structure.

### 10. Generator workflow ladder — input → record → pre-FSI → post-FSI

![E_m ladder](em_ladder_fig9.png)
![stages by model](em_stages_by_model.png)
![p_m ladder](pm_ladder.png)

The four stages of "how the generator implements the spectral function", every panel in the
**identical** fig9 convention — occupancy scale `y = Z·hist/(N_p·binw)`, proton channel
(hitnuc = p), **no cuts**: (1) the input tables `f_{k<300}(E)`; (2) the **struck nucleon as
written into the event record**, `E_2 = M_p − En − p_n²/(2M_¹¹B)`, `p_2 = |p⃗_n|`; (3) the
pre-FSI primary proton (`E_m = ω − T_p − T_rec`, bit-identical to `cache/prefsi`, §9); (4) the
same reconstruction from the post-FSI leading proton. E_m panels take `p_m < 300`, p_m panels
take `0 ≤ E_m < 80`. Conventions differ from §5 (spectrometer acceptance + area-matching — here
neither) and §6 (`E_m = ω − T_p` without T_rec — here with); the stage-2 definition subtracts
T_rec, unlike the `results/template/make_groundstate_*` convention `M_N − En` (~2 MeV apart at
200 MeV/c), exactly so that PWIA makes stages 2 and 3 coincide when the chain conserves energy.
Caveat: conditioning every stage on hitnuc = p counts p→n charge exchange as loss and excludes
n→p feed-in (§5/§7 accept any final proton).

Ladder bookkeeping (integrals over E_m<80, p_m<300, × Z/N_p; `surv` = fraction of
proton-channel events with ≥1 post-FSI proton):

| model | I₂ | I₃ | I₄ | I₄/I₃ | surv | med\|E₂−E₃\| |
|---|---|---|---|---|---|---|
| LFG + Rosenbluth | 6.000 | 6.000 | 3.520 | 0.587 | 100.0 % | 0 |
| SF + Rosenbluth | 5.439 | 5.439 | 2.981 | 0.548 | 99.9 % | 0 |
| LFG + SuSAv2 | 0 (E₂<0) | 5.219 | 3.176 | 0.609 | 100.0 % | 28.9 MeV |
| SF(2024) + UnifiedQEL | 5.512 | 5.512 | 3.208 | 0.582 | 100.0 % | 0 |
| SF + UnifiedQEL | 5.544 | 5.544 | 3.225 | 0.582 | 100.0 % | 0 |

(inputs 5.25 / 5.23; data 6.08; the paper's FSI-absorbed occupancy scale ≈ 3.24, §7.)

**Findings:**
- **Stages 2 and 3 coincide event-by-event (< 3·10⁻¹² MeV) for the a- AND b-chains** — the
  pre-FSI reconstruction is an exact image of the record, so the a-tunes' f(E) destruction (§9)
  happens **when the struck nucleon is written**, not in the outgoing-proton computation: the old
  chain stores the on-shell-¹¹B-remnant closure (`E_2 ≡ S_p = 15.957` MeV, a delta for LFG *and*
  SF), discarding the sampled removal energy before it ever reaches the record. Only the b-tunes
  put the sampled f(E) into `En`.
- **SuSAv2's record nucleon is exactly on-shell** (`En = √(M_p²+p_n²)`, residual < 10⁻⁵ MeV):
  `E_2 = −(T_N + T_rec) < 0` for every event (median −13 MeV) — a third record convention. Its
  removal-energy physics exists only in the outgoing energy balance (stage 3, median offset
  28.9 MeV from the record).
- **The p_m ladder shows the same loss in the other marginal**: with E₂ pinned at S_p, the
  a-tunes' record passes the **full** n(k) — SRC tail included — through the `E_m < 80` window
  (I₂ = 5.92 for SF vs the input's E-restricted 5.40): the sampled E–k correlation is destroyed.
  The b-tunes track the restricted input marginal.
- **FSI never removes all protons** (survival 99.9–100 %): the occupancy drop to I₄/I₃ =
  0.55–0.61 (paper: T/1.11 ≈ 0.54) is entirely **migration out of the (p_m<300, E_m<80) window**
  (plus, for the a-pair, the +20 MeV `NucBindEnergyAggregator` shift parking the delta at
  ~36 MeV, §9), not proton absorption.
- Only stage 4 is shape-comparable to the data (the published S(E_m) is FSI-distorted); the
  ladder localizes where each model's stage-4 shape and normalization came from.

### 10b. Inside the first bin — fine-binned input vs struck nucleon

![fine input vs struck](em_input_struck_fine.png)

Stages 1 vs 2 below the data's 5-MeV resolution (`plot_em_input_struck_fine.py`): 0.25-MeV bins
over 5–40 MeV (left) and 0.1-MeV bins over the 2024 table's fine segment (right); the input
tables drawn on their **native grids** (Benhar: flat 5-MeV steps; 2024: 0.025/0.1 MeV). All of
this lives inside the single fig9 bin [15,20):
- **a-tunes**: one ~keV-wide line at S_p = 15.957 MeV (100 % of events within ±0.05 MeV) —
  height ≡ Z/binw (24 at 0.25-MeV bins), a degenerate line masquerading as a "peak" at 5 MeV;
- **SF+UnifiedQEL**: the table's flat [15,20) block emerges as a smooth dome peaking at
  14.8–14.9 MeV (*below* the block edge), strength leaking down to ~11 MeV, block edges at
  20/25 MeV only softened steps; 38 % in [15,20) vs the table's ~55 % — not a bin-for-bin
  resample (mechanism pinned in §10b1: the record is the sampled table shifted down by
  T_rec(k));
- **SF(2024)+UnifiedQEL**: the NIKHEF quasiparticle peaks (16.0 / 18.2 / ~21 MeV) **survive
  into the record** at the right positions, broadened to a few hundred keV with partly filled
  valleys — the generator preserves the 2024 SF's resolved shell structure at ~half-MeV
  resolution;
- **SuSAv2**: absent (on-shell record, E₂ < 0).

**Pre→post-FSI mechanism for the a-tunes (code-verified).** The §9 pre-FSI delta moves to the
~36-MeV post-FSI spike via Module-10 `NucBindEnergyAggregator` of the old QEL-EM thread
(install `config/EventGenerator.xml:249`), which runs **after** `HadronTransporter` and, for
every final-state nucleon still carrying a `RemovalEnergy` tag, subtracts that energy from its
kinetic energy (`NucBindEnergyAggregator.cxx:85-94`), rescales |p⃗| back on-shell (:96-115) and
books the balance as a `Bindino` (:123). The tag travels in a side channel the 4-vectors never
see: `FermiMover.cxx:138` stores the nuclear model's removal energy on the struck nucleon while
writing the on-shell-¹¹B closure into its 4-vector (:182 — hence the stage-2 delta), and
`QELHadronicSystemGenerator.cxx:85` copies it onto the outgoing proton. The subtracted value
differs per a-tune:
- **LFG**: fixed `RFG-NucRemovalE@Pdg=1000060120` = **20 MeV from the tune CommonParam**
  (`tunes/GEM26_11a/CommonParam.xml:145`; the install default is 25 MeV) since
  `LFG-MomentumDependentErmv = false`. Measured E₄−E₃: a spike at 19.99 MeV holding 56 % of
  events (= the transparent fraction, matching I₄/I₃ = 0.587); the 43 % above +25 MeV is hA
  energy loss stacked on top.
- **SF**: the **sampled Benhar removal energy** (`SpectralFunc.cxx:124`) — the same number the
  4-vector bookkeeping discarded. Post-FSI E_m ≈ S_p + E_sampled: the input f(E) reappears one
  stage too late and double-counted with S_p. Verified: E₄−E₃ peak bin = [15,20) (the table's
  p-shell), frac in [15,25) = 0.313 vs transparency × p-shell strength = 0.301; the f(E)
  correlation tail drags the median E₄ to 70.6 MeV — why SF has the lowest in-window I₄.
So §9's "+20 MeV aggregator shift" is exact for LFG only; for SF the pre→post-FSI step is,
ironically, the only place the sampled Benhar f(E) shape ever reaches an observable.

### 10b1. SF + UnifiedQEL (22b) vs the Benhar input — the record is the table minus T_rec(k)

![22b input vs struck](em_input_struck_fine_22b.png)

Single-model view (`plot_em_input_struck_fine_by_model.py`) with a third curve that pins the
§10b "dome" mechanism: the struck-nucleon record with the ¹¹B recoil kinetic energy **added
back**, `m_N − E_n = E_m + T_rec`, `T_rec = p_n²/2M(¹¹B)`. That curve lands on the Benhar
input **exactly** — the [15,20) block edge is restored razor-sharp (strength below 15 MeV:
14.5 % in E_m → **0.0000** in m_N − E_n) and the [20,25)/[25,30) steps reappear.

**Code mechanism** (`genie::utils::BindHitNucleon`, `QELUtils.cxx:271`, reached with the
default `HitNucleonBindingMode = UseNuclearModel`, `QELEventGenerator.cxx:402`): every nuclear
model except SpectralFunc gets `Mf = Mi + Eb − mNi` (excited recoiling remnant → reconstructed
E_m = Eb). SpectralFunc alone gets a special case — *"the SpectralFunc nuclear model returns a
removal energy which includes the kinetic energy of the final-state nucleus. We account for
this difference here"* — `Mf = √((Mi+E−mNi)² − k²)`, which collapses to **`E_n = m_N − E`**
(static-spectator closure). The sampling itself is faithful (`SpectralFunc::LoadSFDataFile`
builds a uniform-bin TH2D, tabulated values = bin centers; `GetRandom2` draws bin-uniformly),
so the entire distortion is this one line: the reconstructed, recoil-subtracted missing energy
comes out **E_m = E_sampled − k²/2M(¹¹B)** — 0.5 / 2.0 / 4.4 MeV low at k = 100 / 200 / 300
MeV/c, k-correlated, hence a downward *smearing* (the dome) rather than a shift. The σ
weighting only tilts gently within blocks (the restored curve rides ~5 % above the input
inside [15,20)). Note the consequence: events reconstruct at E_m < S_p — below the proton
separation energy, kinematically impossible in PWIA.

### 10b2. SF(2024) + UnifiedQEL (33b) vs the 2024 input — quasiparticle peaks restored at S_p

![33b input vs struck](em_input_struck_fine_33b.png)

Same three-curve view for the 2024 table at 0.05-MeV binning. The record E_m shows the NIKHEF
quasiparticle peaks broadened and downshifted (ground-state peak at 15.52 MeV, FWHM 0.30);
adding T_rec back restores them **on top of the input table** — ground-state peak at
15.94 ≈ S_p = 15.957 MeV with FWHM 0.18, and the strength below the table's 13-MeV floor
drops 3.5 % → **0.0000**. This also settles the convention question: the 2024 table's E axis
is the recoil-free (mass-based) removal energy — its ground-state peak sits exactly at the
physical separation energy, as it must — so the `BindHitNucleon` assumption that the table's
E "includes the kinetic energy of the final-state nucleus" mis-reads these tables, and the
generator's E_m spectrum is systematically low by T_rec(k). Candidate upstream GENIE issue;
bounded by ≤ 4.4 MeV inside p_m < 300, invisible at 5-MeV binning, but exactly the first-bin
distortion resolved here.

## Scripts
- **`samples.py`** — 5-model registry; `xrootd_url()`, `gst_urls(model)`, `load_cache(model)`,
  `lw(model)`/`zorder(model)` (the `HIGHLIGHT` = Variant 05 gets a thick line, drawn on top).
- **`build_cache.py`** — XRootD stream + stage-1 selection → `cache/<model>.npz`.
- **`selection.py`** — shared selection + missing-kinematics util (unchanged; `load_events(path)`
  works on a local path *or* a `root://` URL):
  - `CUTS` — acceptance windows (center ± half-width): `El` 1.725±0.005 GeV, `theta_e` 32±0.5°,
    `Tp` 0.700±0.025 GeV, `theta_p` 43±1°.
  - `load_events` — leading (post-FSI) proton, `E_m = ω − T_p`, `p_m = |q⃗ − p⃗_p|`, `Q2`, angles.
  - `select_electron(ev)` — stage 1 (El ∧ θ_e). `select_proton_e(ev)` — stage 2.1 (+ T_p, θ_p
    free). `select(ev)` — stage 2 (full). `cache_stage_masks(c)` — all three masks from a
    stage-1 cache. `cut_summary(ev)`.
- **`plot_missing.py`** → `missing_e_p_q2_1.28.png`, `missing_e_p_q2_1.28_stage21.png`
- **`plot_dists.py`** → `dists_stage1_electron.png`, `dists_stage21_proton_e.png`, `dists_stage2_full.png`
- **`plot_2d.py`** → `missing_2d_e_vs_p.png` (3 stages × 5 models)
- **`plot_missing_shells.py`** → `missing_p_shells.png` (p_m in the p-/s-shell `E_m` windows, all 3 stages)
- **`acceptance.py`** — HMS/SOS spectrometer-acceptance selection (arm-frame δ/y′/x′ boxes,
  e′-plane rotation, `E_m = ω − T_p − T_rec`); `select_acceptance(ev)`, `cut_summary(ev)`.
- **`build_cache_acceptance.py`** — XRootD stream + acceptance selection →
  `cache/acceptance/<model>.npz` (`MAX_FILES` env, default 20 = 10M events/model).
- **`plot_em_dutta_fig9.py`** → `em_dutta_fig9_q1p28.png` (E_m overlay on Dutta Fig. 9,
  occupancy-normalized; prints per-model χ²)
- **`build_cache_q2.py`** — XRootD stream, Q² = 1.28 ± 5 % window ONLY (no e′/p cuts) →
  `cache/q2window/<model>.npz` (`MAX_FILES` env, default 4).
- **`plot_dists_q2.py`** → `dists_q2window.png` (the 7 variables, uncut, in the Q² slice)
- **`deforest.py`** — numpy port of SIMC's σ_cc1/σ_Mott/Bosted-FF/sigep
  (`simc_gfortran/physics_proton.f` @ 60c2047; flag 0/−1) for the S^D extraction
  ([plan](../../.claude/plans/genie-experimental-spectral-function.md)); self-validating
  (`pixi run python results/prd-analyzer/deforest.py`): elastic closure
  deforest·Ee/(pp·Mp·Ein) = sigep exact at the Dutta settings.
- **`build_cache_sd.py`** — one XRootD pass → `cache/sd/<model>_{q2win,accept}.npz`: the
  σ_cc1 inputs (nu, q, E_p, p_p, sinγ, cosφ) + E_m (recoil incl.)/p_m per event for both
  S^D fiducials, plus the sample cross section from the production's own gmkspl spline
  (auto-located via the campaign gridlog; C12 channels; e.g. Rosenbluth 23.61 nb,
  UnifiedQEL 15.56 nb at 2.445 GeV, Q² ≥ 1.18).
- **`phase_space_h.py`** — flat companion MC → `cache/sd/H_{q2win,accept}.npz`: the
  per-(E_m, p_m)-bin phase-space volume H [MeV²·sr²] for each S^D fiducial (exact
  importance sampling, Q² ≥ 1.18 imposed, split-sample converged to 0.35 % median).
- **`plot_sd_extraction.py`** → `sd_2d_maps.png`, `sd_extraction_fig9.png` (the S^D
  extraction: 2D maps, absolute fig9 overlay + ratio panel; prints the window integrals
  and the cross-fiducial validation).
- **`plot_sf_input_em_fig9.py`** → `sf_input_em_fig9.png` (the undistorted input-table
  f(E), k < 300, occupancy scale, vs the fig9 data).
- **`build_cache_prefsi.py`** — XRootD stream, hitnuc = p, no cuts → `cache/prefsi/`
  (pre-FSI primary-proton E_m/p_m).
- **`plot_em_prefsi_fig9.py`** → `em_prefsi_fig9.png` (pre-FSI E_m, occupancy scale, vs
  the input tables and the fig9 data).
- **`fig9_common.py`** — shared fig9 pieces: `load_dutta()` (data + error model),
  `load_input_tables()`, the restricted marginals `f_restricted` (k<300) / `n_restricted`
  (E<80), `rebin`, and the `EDGES/PM_MAX/BINW/EM_MAX/Z` constants.
- **`build_cache_ladder.py`** — one XRootD pass, hitnuc = p, no cuts → `cache/ladder/<model>.npz`
  (per-event E/p at stages 2/3/4 + Q²; stage 3 verified bit-identical to `cache/prefsi`;
  `MAX_FILES` env, default 4 = 2M events/model — the gst files are 500k events each).
- **`plot_em_ladder_fig9.py`** → `em_ladder_fig9.png` (the four-stage E_m ladder vs fig9;
  prints the §10 bookkeeping table).
- **`plot_em_stages_by_model.py`** → `em_stages_by_model.png` (per-model overlay of the three
  event-record stages + input table + data).
- **`plot_pm_ladder.py`** → `pm_ladder.png` (the p_m companion ladder; no external data by
  design — the Fig. 6 normalization convention is unresolved).
- **`plot_em_input_struck_fine.py`** → `em_input_struck_fine.png` (stages 1 vs 2 at 0.25/0.1-MeV
  binning — the structure inside the first fig9 bin; inputs on their native grids).
- **`plot_em_input_struck_fine_by_model.py`** → `em_input_struck_fine_22b.png`,
  `em_input_struck_fine_33b.png` (per-model input vs record vs recoil-restored `m_N − E_n` —
  the T_rec(k) mechanism figures of §10b1/§10b2).
- **`plot_spectral_function.py`** → `spectral_function_c12.png` (parses `pke12_tot.data`; no gst needed)
- **`plot_spectral_function_2024.py`** → `spectral_function_c12_2024.png`, `spectral_function_c12_2024_vs_old.png` (parses `data/pke12_2024.table`; two-segment energy grid)

## Data
GENIE gst (post-FSI), `e⁻` on C12, E_beam = 2.445 GeV, cut **t05** (EM-MinQ2Limit = 1.18, Q² ≈ 1.28),
10M events/model, on dCache:
```
/pnfs/dune/scratch/users/liangliu/jobsub-agent/prd_paper/EM/
  genie_inclxx/GEM26_11a_05_000/eminus_C12_20260602-131202_gev/…   (LFG,             100×100k)
  genie_inclxx/GEM26_22a_05_000/eminus_C12_20260602-131216_gev/…   (SF,              100×100k)
  genie_dev/GEM21_11a_05_000/eminus_C12_20260601-153754_gev/…      (SuSAv2,           20×500k)
  genie_inclxx/GEM26_33b_05_000/eminus_C12_20260610-095820_gev/…   (SF(2024)+UQEL,   100×100k)
  genie_inclxx/GEM26_22b_05_000/eminus_C12_20260604-103343_gev/…   (UnifiedQEL,      100×100k)
```
streamed over XRootD (never copied locally). The narrow spectrometer cuts keep ~0.4 % at stage 1 and
~0.01–0.05 % at stage 2, so the full 10M/model is needed for usable statistics.

## Notes
- The EMQE samples are pure QEL (the `EMQE` generator list is QEL-EM only), so no RES/DIS split.
- 1D overlays are **area-normalized** — the five models have different total σ, so raw counts are
  not a fair overlay; the rate information lives in the legend `N` (and the stage-2 efficiencies).
- `p_m` is the unsigned magnitude (matches the paper); the p-shell dip at `p_m≈0` is the l=1 node.
- SuSAv2 (`genie_dev`) vs the Rosenbluth pair (`genie_inclxx`) is a cross-build comparison.

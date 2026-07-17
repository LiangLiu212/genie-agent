# Electron–Fe56 scattering

## Fe56 2D spectral function — the GENIE input table

![Fe56 2D spectral function from the GENIE input table (GEM26_22a_05_000)](sf2d_table_fe56_GEM26_22a_05_000.png)

The Benhar 2D spectral function S(P_miss, E_miss) exactly as GENIE consumes it,
resolved the way the tune resolves it at run time: `GEM26_22a_05_000` →
`ModelConfiguration.xml` `NuclearModel@Pdg=1000260560` = `genie::SpectralFunc/Default`
→ `SpectralFunc.xml` `SpectFuncTable@Pdg=1000260560_{2212,2112}` = `pke56_tot.data`
(one table shared by protons and neutrons; GENIE divides out the tabulated
N-nucleon normalization per hit species).

- **Left** — the table density as stored (MeV⁻⁴): mean-field shell region at
  P_miss ≲ 250 MeV/c, E_miss ≲ 60 MeV, plus the correlated (SRC) continuum.
  The rectangular edge at E_miss ≈ 125 MeV / P_miss ≈ 320 MeV is the seam where
  the table stitches the mean-field and correlation pieces.
- **Right** — the distribution GENIE actually samples (`TH2::GetRandom2` over the
  per-bin mass 4π P²_miss S ΔP ΔE, area-normalized). The P² weight moves real
  probability into the tails: **P(P_miss > 250 MeV/c) = 0.158**,
  **P(E_miss > 100 MeV) = 0.080**. This tail is what collapsed the RES-EM Q²
  window under the t05 cut (`EM-MinQ2Limit = 1.18 GeV²`) before the
  `RESKinematicsGenerator` guard (see
  `../../.claude/plans/fix-res-em-q2window-assert.md`).

Grid: 40 P_miss bins [0, 800] MeV/c × 80 E_miss bins [2.5, 402.5] MeV
(bin centers tabulated; parsed exactly as `SpectralFunc::LoadSFDataFile`).
GEM26_22b_05_000 resolves to the identical table; GEM26_11a / GEM21_11a use
LocalFGM (no table). Event-level realization: `sf2d_events_fe56_*.png`.

Regenerate: `pixi run python results/template/make_sf2d_table.py --all-tunes`

## Missing energy: table vs simulation vs Dutta Fig. 11

The C12 four-stage **restored ladder** (v0 README §12) replicated on Fe56 for
each campaign tune, at the digitized data's kinematics (Q² = 1.28 (GeV/c)²,
beam 2.445 GeV): all stages on the input-table axis E_m + T_rec (record =
m_N − E_n, protons = ω − T_p, remnant Mn55 from the install's PDG table),
selection `qel && hitnuc==2212` (explicit here; implicit in the EMQE C12
samples), p_m < 300 MeV/c, occupancy normalization Z·hist/(N_sel·5 MeV) with
Z = 26. Each tune: 2M streamed events (20 gst files). Common to all four:
FSI = hA2018, `EM-MinQ2Limit = 1.18` GeV² (t05). The `pke56_tot.data` table
integrates raw to 25.998 ≈ Z — proton-number normalized, the same convention
as the C12 tables.

Data caveats (as in the C12 study): Dutta's published E_m is recoil-subtracted,
so on this axis the points sit low by an event-wise T_rec ≤ ~4.5 MeV (sub-bin);
the fig11 absolute scale is renormalized to the in-window IPSM strength
(∫ = 18.20 ± 0.08, not Z = 26 and not a raw distorted yield); file errors are
statistical only (inflated by 2% pt-to-pt ⊕ 5% model here).

Summary (occupancy units, E < 80 MeV, p_s < 300 MeV/c):

| tune | N_sel (of 2M) | I1 (table) | I2r = I3r | I4r | I4r/I3r | record median [p5, p95] MeV |
|---|---|---|---|---|---|---|
| GEM26_11a_05_000 | 251,502 (12.6%) | — | 26.000 | 10.619 | 0.408 | 10.45 [10.22, 10.75] |
| GEM26_22a_05_000 | 254,047 (12.7%) | 22.630 | 23.423 | 8.997 | 0.384 | 10.48 [10.24, 10.88] |
| GEM26_22b_05_000 | 186,694 (9.3%) | 22.630 | 23.976 | 9.621 | 0.401 | 20.47 [8.32, 59.29] |
| GEM21_11a_05_000 | 213,209 (10.7%) | — | 0.000 / 24.448 | 10.037 | 0.411 | −14.38 [−30.52, −1.78] |

I2r = I3r in every tune (energy-conserving pre-FSI chain; GEM21's I2r = 0 is
an in-window statement — its record sits entirely below E = 0). FSI keeps only
~40% of strength in-window everywhere, while a post-FSI proton exists in
~100% of events: strength leaves the window, not the event. Data integral
18.200 on its own published scale. Regenerate:
`pixi run python results/template/make_emiss_ladder_fe56.py --all-tunes`
(cache: `cache/ladder_fe56/`; delete to re-stream).

### GEM26_11a_05_000 — LocalFGM + Rosenbluth

| piece | algorithm |
|---|---|
| Fe56 ground state | `genie::LocalFGM/Default` (no 2D SF table) |
| QEL-EM cross section | `genie::RosenbluthPXSec/Default` |
| QEL-EM event chain | install default: `FermiMover/Default` → `genie::QELKinematicsGenerator/EM-Default` |

![Fe56 restored E_m ladder, GEM26_11a_05_000](em_ladder_restored_fe56_GEM26_11a_05_000.png)

Panel 1 has no input-table curve (LFG). The record is a δ at S_p (median
10.45 MeV) — with LFG this loses little: the LFG removal energy is itself
essentially fixed. All 26 protons are in-window (I2r = 26.000: LFG momenta
never exceed 300 MeV/c). The pre-FSI proton reproduces the δ; FSI smears it
into a shape that tracks the data tail but, as everywhere, misses the
12.5 MeV peak from below.

### GEM26_22a_05_000 — 2D SpectralFunc + Rosenbluth (FermiMover chain)

| piece | algorithm |
|---|---|
| Fe56 ground state | `genie::SpectralFunc/Default` → `pke56_tot.data` (`NuclearModel@Pdg=1000260560`) |
| QEL-EM cross section | `genie::RosenbluthPXSec/Default` |
| QEL-EM event chain | install default: `FermiMover/Default` → `genie::QELKinematicsGenerator/EM-Default` |

![Fe56 restored E_m ladder, GEM26_22a_05_000 vs Dutta Fig. 11](em_ladder_restored_fe56_GEM26_22a_05_000.png)

The Fe56 instance of the C12 **a-tune finding**: the tune samples the 2D SF
(panel 1, I1 = 22.630 of 26 in-window — the rest is the k > 300 MeV/c SRC
tail), but FermiMover writes `En = M_A − √(p² + M²_Mn55,gs)` into the record,
dropping the sampled w — panel 2 is a δ at S_p ([10,15) bin = 4.7, off scale;
the sampled physics survives only in `GHepParticle::RemovalEnergy`, section 1).
I2r = I3r = 23.423; FSI in-window survival 0.384 with the post-FSI shape
tracking the data above ~20 MeV.

### GEM26_22b_05_000 — 2D SpectralFunc + UnifiedQEL (QELEventGenerator)

| piece | algorithm |
|---|---|
| Fe56 ground state | `genie::SpectralFunc/Default` → `pke56_tot.data` |
| QEL-EM cross section | `genie::UnifiedQELPXSec/Dipole` |
| QEL-EM event chain | tune override: `genie::QELEventGenerator/EM-Default` (samples the nucleon from the nuclear model — SF-consistent) |

![Fe56 restored E_m ladder, GEM26_22b_05_000 vs Dutta Fig. 11](em_ladder_restored_fe56_GEM26_22b_05_000.png)

The **b-tune contrast**: `QELEventGenerator` keeps the sampled w in the
off-shell energy, and the restoration is **exact**: per-event,
m_N − E_n = E_sampled to keV precision (verified from the GHEP dumps —
(m_N − E_n) − w_stored reproduces k²/2(M_Mn55+E) to <1.5 keV, i.e. the
`BindHitNucleon` SpectralFunc reinterpretation lowers only the *stored*
RemovalEnergy by ≤0.9 MeV and cancels identically on this axis; on the
table-native grid the record has zero strength below the table's support).
The record (median 20.5 MeV, p5–p95 [8.3, 59.3]) sits on the dashed table,
with the residual shape difference — peak 1.03 vs 0.94 — coming from the
UnifiedQEL cross-section weighting of the sampled kinematics. An earlier
version of this note attributed an apparent down-shift to `BindHitNucleon`:
that was a half-bin rebinning artifact (the table grid is centered at
5, 10, … MeV, offset by 2.5 MeV from the plot grid, and `GetRandom2` samples
uniformly within table bins), fixed by spreading each table column over its
native bin in the stage-1 rebin. Of the four tunes this record is the
closest in shape to the data. QEL fraction is 9.3% vs 22a's 12.7%,
consistent with the SF-folded UnifiedQEL cross section being smaller than
Rosenbluth (spline QE σ 1.85 vs 2.75 ×10⁻⁴).

### GEM21_11a_05_000 — LocalFGM + SuSAv2 (scaled-C12 surrogate)

| piece | algorithm |
|---|---|
| Fe56 ground state | `genie::LocalFGM/Default` (no 2D SF table) |
| QEL-EM cross section | `genie::HybridXSecAlgorithm/SuSAv2-QEL` — **Fe56 EM tensor is scaled C12** (open_questions.md) |
| QEL-EM event chain | tune override: `genie::QELEventGeneratorSuSA/Default` |

![Fe56 restored E_m ladder, GEM21_11a_05_000 vs Dutta Fig. 11](em_ladder_restored_fe56_GEM21_11a_05_000.png)

The SuSA chain writes an on-shell-like nucleon: m_N − E_n = −T_N < 0, so the
record sits entirely **below the axis** (median −14.4 MeV; I2r = 0 in-window)
— the Fe56 instance of the C12 SuSAv2 note. The pre-FSI proton lands as a
box-like distribution up to ~35 MeV (LFG kinematics through SuSA's own
binding prescription), and FSI degrades it further. The scaled-C12 surrogate
caveat applies to any physics conclusion drawn from this tune on iron.

## Missing momentum: table vs QEL struck-nucleon record

![Fe56 P_miss, input table vs QEL struck-nucleon record, all t05 tunes](pmiss_struck_fe56_t05.png)

The momentum companion of the E_m ladder: unlike the removal energy, the
struck-nucleon 3-momentum survives into the record for every tune, so the
record |p_n| distribution (same caches/selection: `qel && hitnuc==2212`, no
other cuts) is meaningful for all four. Both curves on the table's **native**
20 MeV/c grid (no rebinning — the E_miss half-bin lesson), occupancy scale
(every curve integrates to Z = 26 by construction).

| tune | median |p_n| [MeV/c] | P(p > 250 MeV/c) |
|---|---|---|
| table (sampling weight) | — | 0.158 |
| GEM26_11a_05_000 (LFG) | 165.0 | 0.017 |
| GEM26_22a_05_000 (SF) | 183.6 | 0.185 |
| GEM26_22b_05_000 (SF) | 178.6 | 0.142 |
| GEM21_11a_05_000 (LFG) | 164.9 | 0.017 |

Reading:

- **22a ≈ table over four decades**: the classic FermiMover chain samples k
  *unweighted* from the SF, so the record momentum distribution is essentially
  the table itself. The residual tail enhancement (P(p>250) = 0.185 vs the
  table's 0.158) is the Q² ≥ 1.18 phase-space retry mildly favoring high-k
  configurations.
- **22b follows at low k but its SRC tail is progressively suppressed** (about
  two decades down by 800 MeV/c): `QELEventGenerator` weights the sampled
  kinematics by the UnifiedQEL cross section, which disfavors deep off-shell
  high-k configurations.
- **11a and GEM21 coincide** (both LocalFGM): the LFG shape with the sharp
  cutoff at the local Fermi momentum ≈ 260 MeV/c and no SRC tail —
  P(p > 250) = 1.7% vs 14–19% for the SF tunes.

Regenerate: `pixi run python results/template/make_pmiss_fe56.py`
(reads the `cache/ladder_fe56/` caches).

## Signed missing momentum (± asymmetry) — GEM26_22a_05_000

![Fe56 signed p_m, GEM26_22a_05_000, 4pi](pmiss_signed_fe56_GEM26_22a_05_000.png)

The published Figs. 6–8 momentum distributions carry a left–right (±p_m)
asymmetry that the paper attributes to W_LT interference beyond deForest
σ_cc1 and/or Coulomb distortion (tex 1144–1155). The digitized `fig7_*.dat`
files are exactly symmetrized, so this is simulation-side only (4π, no
spectrometer acceptance; `qel && hitnuc==2212`, Dutta window 0 < E_m < 80 MeV,
2M streamed events → 232k pre-FSI / 90k post-FSI in-window).

**Sign convention** (the paper never states its own): ẑ = q̂, x̂ = the
scattered electron's transverse-to-q direction (in-plane, e′ side);
signed p_m = sign(p_m·x̂)·|p_m| with p_m = p_p′ − q. Positive = p_m tilted
toward the e′ side. If the print's asymmetry turns out mirrored, flip.

**Units**: the top panel is a *density* (counts with the 4π p² phase-space
factor divided out, per d³p_m) — the published fig7 y-axis is ∫S^D dE_m per
d³p_m, which peaks at p_m = 0; raw signed-p_m counts dip at 0 by phase space.

Findings:

- **GEM26_22a does produce an intrinsic ± asymmetry**: integrated
  A = −0.0546 ± 0.0021 (pre-FSI) and −0.0554 ± 0.0033 (post-FSI);
  sign-shuffle controls ±0.001. A(|p|) grows from ~0 at 20 MeV/c to ≈ −8%
  at 300 MeV/c. The plan expectation (A ≈ 0 for the factorized chain) was
  wrong: since pre-FSI p_m ≡ p_n exactly, this is a **kinematic** asymmetry —
  the flux/Q²-window weighting favors initial nucleons moving *away* from
  the e′ side — not a W_LT response effect (the chain has none by
  construction).
- **FSI does not touch the asymmetry** (−5.46% → −5.54%): hA2018 redistributes
  magnitude, not the ± balance.
- **The post-FSI density reproduces the (symmetrized) data shape closely**
  (gray points scaled to the post-FSI integral sit on the red curve) — the
  FSI-distorted GENIE density has the right p_m profile even though the
  E_m profile (ladder section) misses the peak.

Follow-ups (not done): the HMS×SOS in-acceptance version for a direct print
comparison; the other three tunes (22b's QELEventGenerator samples full COM
angles — its intrinsic asymmetry may differ); pixel-measuring the published
fig7 asymmetry.

Regenerate: `pixi run python results/template/make_pmiss_signed_fe56.py`
(cache: `cache/pmiss_signed_fe56/`).

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

## Missing energy: table vs simulation vs Dutta Fig. 11 (GEM26_22a_05_000)

![Fe56 restored E_m ladder, GEM26_22a_05_000 vs Dutta Fig. 11](em_ladder_restored_fe56_GEM26_22a_05_000.png)

The C12 four-stage **restored ladder** (v0 README §12) replicated on Fe56 at the
digitized data's kinematics (Q² = 1.28 (GeV/c)², beam 2.445 GeV): all stages on
the input-table axis E_m + T_rec (record = m_N − E_n, protons = ω − T_p, remnant
Mn55), selection `qel && hitnuc==2212` (explicit here; implicit in the EMQE C12
samples), p_m < 300 MeV/c, occupancy normalization Z·hist/(N_sel·5 MeV) with
Z = 26. Sample: 254k selected of 2M streamed events (20 gst files).

**Model configuration (GEM26_22a_05_000)** — from
`genie-agent/tunes/GEM26_22a/ModelConfiguration.xml` and the install
`config/EventGenerator.xml`; only the QEL-EM chain enters this plot (`qel` cut):

| piece | algorithm |
|---|---|
| Fe56 ground state | `genie::SpectralFunc/Default` → `pke56_tot.data` (Benhar 2D; `NuclearModel@Pdg=1000260560`) |
| QEL-EM cross section | `genie::RosenbluthPXSec/Default` |
| QEL-EM event chain | install default: `FermiMover/Default` → `genie::QELKinematicsGenerator/EM-Default` (classic 12-module thread; no tune `EventGenerator.xml` override) |
| FSI | `genie::HAIntranuke2018/Default` (hA2018) |
| Q² cut (t05) | `EM-MinQ2Limit = 1.18` GeV² (`GEM26_22a_05_000/CommonParam.xml`) |

The FermiMover step in that chain is precisely why panel 2 is a δ: it samples
(p, w) from the 2D SF but writes `En = M_A − √(p² + M²_Mn55,gs)` into the
record (w kept only in `GHepParticle::RemovalEnergy`). RES/DIS/MEC models are
configured identically to the other GEM26 tunes but are excluded here.

- **Panel 1** — `pke56_tot.data` marginal f_{k<300}(E). The raw table integrates
  to 25.998 ≈ Z: the file is proton-number normalized, same convention as C12.
  In-window occupancy I1 = 22.58 of 26 (the rest is the k > 300 MeV/c SRC tail).
- **Panel 2** — the record is a **δ at S_p ≈ 10.2 MeV** ([10,15) bin = 4.7, off
  scale): 22a samples the 2D SF but its classic FermiMover chain drops the
  sampled w from the 4-momentum — the Fe56 instance of the C12 a-tune finding.
  The sampled physics survives only in `GHepParticle::RemovalEnergy` (section 1).
- **Panel 3** — identical to panel 2 (I3r = I2r = 23.42): the pre-FSI chain is
  energy-conserving, ω − T_p ≡ m_N − E_n.
- **Panel 4** — hA2018 FSI smears the δ into a broad distribution that tracks the
  data shape above ~20 MeV but cannot reproduce the 12.5 MeV peak (smearing is
  upward-only from S_p). In-window survival I4r/I3r = 0.384 (I4r = 9.00);
  post-FSI a proton still exists in 99.8% of events — strength leaves the
  window rather than the event.

Data caveats (as in the C12 study): Dutta's published E_m is recoil-subtracted,
so on this axis the points sit low by an event-wise T_rec ≤ ~4.5 MeV (sub-bin);
the fig11 absolute scale is renormalized to the in-window IPSM strength
(∫ = 18.20 ± 0.08, not Z = 26 and not a raw distorted yield); file errors are
statistical only (inflated by 2% pt-to-pt ⊕ 5% model here).

Regenerate: `pixi run python results/template/make_emiss_ladder_fe56.py`
(cache: `cache/ladder_fe56/`; delete to re-stream).

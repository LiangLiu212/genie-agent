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

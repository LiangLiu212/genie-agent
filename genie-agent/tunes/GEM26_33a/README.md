# GEM26_33a — EM Rosenbluth QE with the 2024 (Ankowski-Benhar-Sakuda) C12 spectral function

Custom genie-agent overlay tune (`--gxmlpath genie-agent/tunes`). **Identical to `GEM26_22a`**
except the C12 ground state: the **2024 Ankowski-Benhar-Sakuda proton spectral function**
(`genie::SpectralFunc/pke12_2024`, data `pke12_2024.table`) replaces the older
`genie::SpectralFunc/Default` (Benhar `pke12_tot.data`). The single diff is the C12 line in
`ModelConfiguration.xml`:

```
genie::SpectralFunc/Default  ->  genie::SpectralFunc/pke12_2024
```

- **QEL-EM cross section** → `genie::RosenbluthPXSec/Default` (unchanged from 22a; elementary e–N elastic).
- **C12 ground state** (`NuclearModel@Pdg=1000060120`) → `genie::SpectralFunc/pke12_2024` — the 2024
  SF fit to high-resolution NIKHEF (e,e′p) data, which **resolves the p-shell into discrete
  quasiparticle peaks** (~16 / ~18.5 / ~21 MeV) where `pke12_tot` had one broad ~5-MeV bump; the
  momentum distribution `n(k)` is unchanged.
- `EventGenerator.xml` omitted (like 22a) → the install-default old QEL-EM thread that Rosenbluth needs.

The `pke12_2024` param_set lives in the **genie_inclxx install** (`config/SpectralFunc.xml`,
`feature/pke12_2024` branch; data `data/evgen/nucl/spectral_functions/pke12_2024.table`, converted
to GENIE's uniform-grid format by `convert_pke12_2024.py`).

## Why Rosenbluth shows the SF change cleanly

Rosenbluth has **no removal-energy dependence**, so the reconstructed missing energy
`E_m = ω − T_p` faithfully carries the SF removal-energy marginal `f(E)`. The **22a↔33a** contrast
therefore directly displays the old-vs-2024 SF removal-energy spectrum (the resolved p-shell).

## Comparison set

| Tune | C12 ground state | QE-EM cross section |
|------|------------------|---------------------|
| `GEM26_22a` | SF Default (`pke12_tot.data`)     | Rosenbluth (factorized) |
| **`GEM26_33a`** | **SF 2024 (`pke12_2024.table`)** | **Rosenbluth (factorized)** |
| `GEM26_22b` | SF Default | UnifiedQEL (SF-consistent) |
| `GEM26_33b` | SF 2024    | UnifiedQEL (SF-consistent) |

`22a`↔`33a` isolates the spectral-function update (old vs 2024) at fixed Rosenbluth cross section.
Knot subdirs `_04…_08` carry the same per-knot `EM-MinQ2Limit` Q²-cut overrides as 22a.

## Splines

The Rosenbluth EM-QE spline is **ground-state-independent** (SF vs LFG give identical `gmkspl`
σ(E)), so `GEM26_33a` can **reuse an existing `GEM26_22a` EMQE spline** of the matching knot — no
new spline needed. Tune id: `GEM26_33a_00_000`.

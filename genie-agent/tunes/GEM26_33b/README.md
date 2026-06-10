# GEM26_33b — EM UnifiedQEL (SF-consistent) QE with the 2024 (Ankowski-Benhar-Sakuda) C12 spectral function

Custom genie-agent overlay tune (`--gxmlpath genie-agent/tunes`). **Identical to `GEM26_22b`**
except the C12 ground state: the **2024 Ankowski-Benhar-Sakuda proton spectral function**
(`genie::SpectralFunc/pke12_2024`, data `pke12_2024.table`) replaces the older
`genie::SpectralFunc/Default` (Benhar `pke12_tot.data`). The single diff is the C12 line in
`ModelConfiguration.xml`:

```
genie::SpectralFunc/Default  ->  genie::SpectralFunc/pke12_2024
```

- **QEL-EM cross section** → `genie::UnifiedQELPXSec/Dipole` (unchanged from 22b; the CBF
  spectral-function QEL differential xsec, Noemi hadron tensor, `NewQELXSec` integrator).
- **C12 ground state** (`NuclearModel@Pdg=1000060120`) → `genie::SpectralFunc/pke12_2024` — the 2024
  SF fit to high-resolution NIKHEF (e,e′p) data (resolved p-shell quasiparticle peaks; `n(k)` unchanged).
- `EventGenerator.xml` **kept** (like 22b) → overrides the QEL-EM thread to
  `genie::QELEventGenerator/EM-Default`, required because `UnifiedQELPXSec` is a `kPSQELEvGen` model.

The `pke12_2024` param_set lives in the **genie_inclxx install** (`config/SpectralFunc.xml`,
`feature/pke12_2024` branch; data `data/evgen/nucl/spectral_functions/pke12_2024.table`, converted
to GENIE's uniform-grid format by `convert_pke12_2024.py`).

## Comparison set

| Tune | C12 ground state | QE-EM cross section |
|------|------------------|---------------------|
| `GEM26_22a` | SF Default (`pke12_tot.data`) | Rosenbluth (factorized) |
| `GEM26_33a` | SF 2024 (`pke12_2024.table`)  | Rosenbluth (factorized) |
| `GEM26_22b` | SF Default (`pke12_tot.data`) | UnifiedQEL (SF-consistent) |
| **`GEM26_33b`** | **SF 2024 (`pke12_2024.table`)** | **UnifiedQEL (SF-consistent)** |

`22b`↔`33b` isolates the spectral-function update (old vs 2024) at fixed UnifiedQEL cross section;
`33a`↔`33b` isolates the cross-section model at fixed 2024 SF.
Knot subdirs `_04…_08` carry the same per-knot `EM-MinQ2Limit` Q²-cut overrides as 22b.

## Splines (important: NOT reusable from 22b)

`UnifiedQELPXSec` **folds the spectral function into the cross section** via `NewQELXSec`, so the
`gmkspl` σ(E) is **SF-dependent** — `GEM26_33b`'s spline differs from `GEM26_22b`'s and must be
regenerated (per-knot integral over the 2024 SF; slow — prefer the grid / a background job).
Tune id: `GEM26_33b_00_000`.

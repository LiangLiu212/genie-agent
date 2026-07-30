[← Results home](../README.md)

# Spectral-function table normalization integrals

*2026-07-30 · script: [`integrate_all_pke.py`](integrate_all_pke.py)*

Normalization check of every `pke*` 2D spectral-function table
`P(|k|, E)` in the active GENIE installation (`genie_inclxx`,
`data/evgen/nucl/spectral_functions/`):

$$I \;=\; \int 4\pi k^2\, P(k,E)\, dk\, dE$$

The tables are tabulated in GENIE's **"N·P" convention** — the density carries
an overall factor of the nucleon count of the tabulated species, which
`genie::SpectralFunc` divides out (`targetN`) at read time. So `I` should equal
**Z** for a proton spectral function and **N** for a neutron one.

## Results

| Table | Species | ∫4πk²P dk dE | Expected | I/N | Grid |
|-------|---------|-------------:|:--------:|:---:|------|
| `pke12_tot.data` | C12 p | 5.999988 | Z = 6 | 0.999998 | 40k × 80E, dE=5 MeV |
| `pke12_2024.table` | C12 p | 5.999783 | Z = 6 | 0.999964 | 40k × 11480E, dE=0.025 MeV |
| `pke12_2024.table.origin` | C12 p | 5.999783 | Z = 6 | 0.999964 | 40k × 3125E, non-uniform |
| `pke16_tot.data` | O16 p | 7.999143 | Z = 8 | 0.999893 | 200k × 150E |
| `pke40p_tot.data` | Ar40 p | 18.107865 | Z = 18 | **1.005993** | 200k × 400E |
| `pke40n_tot.data` | Ar40 n | 22.131857 | N = 22 | **1.005993** | 200k × 400E |
| `pke56_tot.data` | Fe56 p | 25.998110 | Z = 26 | 0.999927 | 40k × 80E, dE=5 MeV |

## Findings

- **All seven tables follow the N·P convention** — each integrates to the
  nucleon count of its species to ≲0.01%, except the Ar40 pair (below). This
  includes `pke56_tot.data`, confirming the Benhar Fe56 source
  (`benhar-sf-56fe.data`) is a **proton** SF normalized to Z = 26, same
  convention as the C12/O16 stock tables.
- **The 2024 C12 conversion is lossless.** `pke12_2024.table` (uniform
  0.025 MeV grid written by `convert_pke12_2024.py`) and its non-uniform
  source `pke12_2024.table.origin` integrate to the same value to all printed
  digits (5.999783), independently reproducing the converter's self-test.
  The repo copy [`data/pke12_2024.table`](../../data/pke12_2024.table) is the
  *origin*-format table and gives the identical integral. The 4×10⁻⁵ deficit
  from exactly 6 is the precision of the published Ankowski–Benhar–Sakuda
  table itself.
- **Both stock Ar40 tables sit +0.60% above their nucleon count**, with an
  identical relative excess for protons (18.1079/18) and neutrons
  (22.1319/22) — a shared normalization artifact of how those tables were
  produced (tabulation precision / grid-boundary truncation), not a parsing
  issue and not a p-vs-n asymmetry.
- **The excess is harmless in GENIE.** `SpectralFunc` samples the ground state
  from the *shape* (area-normalized `TH2::GetRandom2`), so an overall scale
  factor cancels; the integral is a data-integrity check, not a physics knob.

## Method

- Uniform-format tables (`pke*_tot.data`, `pke12_2024.table`) are parsed
  exactly as `SpectralFunc::LoadSFDataFile` does (header
  `nE np / Emin pmin / Emax pmax`, then `np` blocks of
  `{k_center, nE (E_center, P) pairs}`), and the Riemann sum uses
  `dk = (p_max−p_min)/np`, `dE = (E_max−E_min)/nE` from the header edge
  ranges — exactly the bin widths of the `TH2D` GENIE builds.
- The origin-format table uses its native per-segment `dE`
  (340 × 0.025 MeV fine NIKHEF region + 2785 × 0.1 MeV Benhar continuum)
  and the header `dk = 20 MeV/c`.

## Reproduce

```bash
pixi run python results/normalization/integrate_all_pke.py            # active install
pixi run python results/normalization/integrate_all_pke.py <data_dir> # explicit dir
```

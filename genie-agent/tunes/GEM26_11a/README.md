# GEM26_11a — EM Rosenbluth QE with Local Fermi Gas ground state

Custom genie-agent overlay tune (use `--gxmlpath genie-agent/tunes`). Based on the stock EM tune
**GEM21_11a**, changed for the electron quasi-elastic ground-state study on **C12** (list `EMQE`):

- **QEL-EM cross section** → `genie::RosenbluthPXSec/Default` (elementary e–N elastic; replaces
  GEM21_11a's `genie::HybridXSecAlgorithm/SuSAv2-QEL`).
- **Nuclear ground state** = `genie::LocalFGM/Default` (Local Fermi Gas) — the unchanged default.

`EventGenerator.xml` is intentionally **omitted** so GENIE uses the global standard QEL-EM thread
(`genie::QELEventGenerator/EM-Default` + `genie::PauliBlocker/Default`) that Rosenbluth requires,
instead of GEM21_11a's SuSAv2-specific `genie::QELEventGeneratorSuSA` chain.

Pairs with **GEM26_22a** (identical except C12 → Benhar spectral function) for the SF-vs-LFG
comparison. Tune id: `GEM26_11a_00_000`.

## EM-MinQ2Limit overrides (PP subdirs)

`_04..._08` = 0.54 / 1.18 / 1.70 / 1.73 / 3.15 GeV² (spline-ladder campaign);
`_09_000` = **0.25 GeV²** (2026-08-17, inclusive (e,e′) comparison vs the QES-archive
12C 2.5 GeV/15° and 56Fe 2.7 GeV/15° settings — both sit entirely above 0.25).
Each subdir is a full CommonParam.xml copy differing only in that one value.

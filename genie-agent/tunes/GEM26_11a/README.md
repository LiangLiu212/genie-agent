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

# GEM26_22a — EM Rosenbluth QE with Spectral Function ground state

Custom genie-agent overlay tune (use `--gxmlpath genie-agent/tunes`). Based on the stock EM tune
**GEM21_11a**, changed for the electron quasi-elastic ground-state study on **C12** (list `EMQE`):

- **QEL-EM cross section** → `genie::RosenbluthPXSec/Default` (elementary e–N elastic; replaces
  GEM21_11a's `genie::HybridXSecAlgorithm/SuSAv2-QEL`).
- **Nuclear ground state**: C12 (`NuclearModel@Pdg=1000060120`) = `genie::SpectralFunc/Default`,
  the Benhar 2D spectral function (data file `pke12_tot.data`). The default `NuclearModel` is left
  `genie::LocalFGM/Default` for any other nucleus.

`EventGenerator.xml` is intentionally **omitted** so GENIE uses the global standard QEL-EM thread
(`genie::QELEventGenerator/EM-Default` + `genie::PauliBlocker/Default`) that Rosenbluth requires,
instead of GEM21_11a's SuSAv2-specific `genie::QELEventGeneratorSuSA` chain.

Pairs with **GEM26_11a** (identical except C12 → Local Fermi Gas) for the SF-vs-LFG comparison.
Tune id: `GEM26_22a_00_000`.

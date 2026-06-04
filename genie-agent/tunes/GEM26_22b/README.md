# GEM26_22b — EM UnifiedQEL (SF-consistent) QE with Spectral Function ground state

Custom genie-agent overlay tune (use `--gxmlpath genie-agent/tunes`). Sibling of **GEM26_22a**,
identical except the electron quasi-elastic cross-section **model** (list `EMQE`, target **C12**):

- **QEL-EM cross section** → `genie::UnifiedQELPXSec/Dipole` (the CBF spectral-function QEL
  differential xsec; `IntegralNuclearModel = genie::SpectralFunc/Default`, `NewQELXSec` integrator,
  Noemi hadron tensor). Replaces GEM26_22a's factorized `genie::RosenbluthPXSec/Default`.
- **Nuclear ground state**: C12 (`NuclearModel@Pdg=1000060120`) = `genie::SpectralFunc/Default`,
  the Benhar 2D spectral function (`pke12_tot.data`) — same as GEM26_22a. Default `NuclearModel`
  left `genie::LocalFGM/Default` for any other nucleus.

## Why `/Dipole` and not `/Default` (important)

The request was "UnifiedQEL model **Default**", but the bare `Default` param set **cannot be loaded**:
`UnifiedQELPXSec::LoadConfig` fetches `CCFormFactorsAlg` unconditionally and the `Default` set omits
it, so config aborts with `FATAL ... Key: CCFormFactorsAlg does not exist`. (That is why every stock
tune uses a *completed* set — `/ZExp_lqcd`, `/ZExp_incl`, `/Dipole`, … = `Default` + a CC form
factor.) `/Dipole` = `Default` + `genie::LwlynSmithFFCC/Dipole`.

For an **EM** interaction this is physically identical to a complete "Default": `UnifiedQELPXSec::XSec`
selects the form-factor model by interaction type and uses **only** `EMFormFactorsAlg`
(`genie::LwlynSmithFFEM/Default`, set in `Default`) for EM — the CC dipole form factor is loaded but
never evaluated. Same SF integral nuclear model, Noemi tensor, and `NewQELXSec` integrator as Default.

## Event generation

`EventGenerator.xml` **overrides the QEL-EM thread to the spectral-function generator**
`genie::QELEventGenerator/EM-Default` (Module-2; no `FermiMover`/`QELKinematicsGenerator`/
`QELPrimaryLeptonGenerator`/`QELHadronicSystemGenerator`). This is **required**: `UnifiedQELPXSec`
is a `kPSQELEvGen` model — it needs the struck-nucleon momentum sampled from the SF and the FS
4-vectors set *before* `XSec` is evaluated. The install-wide default QEL-EM thread wires the classic
`QELKinematicsGenerator/EM-Default`, which scans `dσ/dQ²` (`kPSQ2fE`) with the nucleon at rest and
unset FS vectors → `UnifiedQELPXSec::XSec` hits its early `Q²<Q2min` guard and returns **0 at every
scan point** → `KineGeneratorWithCache::MaxXSec` aborts with `max_xsec<=0` and **no event is
generated** (the spline integral is unaffected, so this surfaces only at `gevgen`). `QELEventGenerator`
samples the SF nucleon, inherits the thread's `XSecModel` (`UnifiedQELPXSec/Dipole`, unchanged) and
its `NuclearModelMap` (C12 → SpectralFunc), and evaluates in `kPSQELEvGen`. The overlay file mirrors
the stock SF QEL-EM thread (cf. `GTEST23_40a/EventGenerator.xml`); verified end-to-end (2026-06-04):
50/50 QE events at 2.445 GeV, Q² respecting the 1.18 cut, zero `max_xsec` aborts.

## Comparison set

| Tune | C12 ground state | QE-EM cross section |
|------|------------------|---------------------|
| `GEM26_11a` | Local Fermi Gas    | Rosenbluth (factorized) |
| `GEM26_22a` | Spectral Function  | Rosenbluth (factorized) |
| **`GEM26_22b`** | Spectral Function | **UnifiedQEL** (SF-consistent) |

`11a`↔`22a` isolates the ground state (SF vs LFG) under a factorized cross section; `22a`↔`22b`
isolates the cross-section model (factorized Rosenbluth vs SF-consistent UnifiedQEL) at fixed SF
ground state. Tune id: `GEM26_22b_00_000`.

## Note on spline generation (slow)

`UnifiedQELPXSec/Dipole` folds the spectral function into the cross section via `NewQELXSec`, so
`gmkspl EMQE` is **much slower** than the Rosenbluth tunes (per-knot integral over the SF). Prefer
generating the spline on the grid (`genie-grid` skill) or as a background job, not a blocking
foreground run. Status as of creation: the tune builds and configures correctly (SF integral model
wired, no errors) — a full spline was not yet produced.

# GEM26_44b — EM QE with INCL++ nuclear ground state AND INCL++ FSI

Custom genie-agent overlay tune (use `--gxmlpath genie-agent/tunes`). Family digit
convention extended: 1 = LFG, 2 = SF (Benhar), 3 = SF2024, **4 = INCL++ ground
state**; letter `b` = `UnifiedQELPXSec` (forced here — see below). Unlike every
other GEM26 family, this one **also changes the FSI**: hA2018 → INCL++ cascade.
Cloned from `GEM26_22b`; plan: `.claude/plans/gem26_44b-incl-gs-fsi.md`.

The chain is unique for an electron probe (verified in source, 2026-07-12):

```
NucleusGenINCL  →  QELEventGeneratorINCL  →  UnifiedQELPXSec
```

- `NucleusGenINCL` is a `NucleusGenI`, not a `NuclearModelI` — only
  `QELEventGeneratorINCL` (and `MECGeneratorINCL`) accept it.
- `QELEventGeneratorINCL` evaluates the xsec exclusively in `kPSQELEvGen`.
- Of the `kPSQELEvGen`-capable models, only `UnifiedQELPXSec::ValidProcess`
  accepts EM (LwlynSmith/Nieves are weak-CC-only); Rosenbluth/SuSAv2 have no
  Jacobian to/from that space.

## What this overlay changes (vs GEM26_22b)

| File | Change |
|------|--------|
| `ModelConfiguration.xml` | `XSecModel@QEL-EM` → `genie::UnifiedQELPXSec/EM_Dipole_incl`; `HadronTransp-Model` → `genie::INCLCascadeIntranuke/Default` |
| `EventGenerator.xml` | `QEL-EM` thread → 6-module INCL shape (`QELEventGeneratorINCL/EM-I-Default`; no VertexGenerator/PauliBlocker — `NucleusGenINCL` sets vertex+momentum, Pauli blocking is internal to INCL) |
| `QELEventGeneratorINCL.xml` | tune-local copy + `EM-I-Default` (= `CC-I-Default` with `Cache-MinEnergy` 5.0 → 0.5 for sub-5-GeV electron beams) |
| `UnifiedQELPXSec.xml` | tune-local copy + `EM_Dipole_incl` (= `ZExp_lqcd_incl` with `IntegralNucleusGen` → `NucleusGenINCL/Default`, CC FF → `/Dipole`) |
| `TuneGeneratorList.xml` | `Default` restricted to **QEL-EM only** (see "EMQE-only rule") |

The `NuclearModel`/`NuclearModel@Pdg` lines in `ModelConfiguration.xml` are left
as in 22b — the INCL thread never consumes them (the generator uses its own
`NuclearModel` sub-alg; the integrator uses `IntegralNucleusGen`).

`CCFormFactorsAlg` in `EM_Dipole_incl` is loaded-but-never-evaluated for EM,
exactly as in 22b's `/Dipole` (see GEM26_22b/README.md).

## Energy convention (Phase-0 findings, 2026-07-12) — READ BEFORE ANALYZING Em

Full write-up: `results/prd-analyzer-v0.1/open_questions.md` (INCL++ entry).
Key facts, all verified by source read:

1. **Off-shell hit nucleon, no removal energy.** The GHEP initial nucleon has
   `E = sqrt(p²+m²) − v_loc(r,p)` where `v_loc` is INCL's local-energy
   prescription (`G4INCLKinematicsUtils.cc:44`). GENIE's `RemovalEnergy` field
   plays no role (`NucleusGenINCL` sets 0 and ignores `Eb` /
   `HitNucleonBindingMode`).
2. **The event momentum distribution is NOT the INCL correlated ground state.**
   Each accept/reject throw resamples the momentum uniformly in a global-p_F
   ball at the fixed ground-state radius, accepting KE > locE
   (`INCLNucleus::ResamplingHitNucleon`); only the vertex radius comes from the
   correlated ground state. In-code `TODO` acknowledges this.
3. **Vertex-level Em = v_loc − T_i (before recoil subtraction), no S_p floor**
   — expect strength near/below zero on Dutta's Em axis, qualitatively unlike
   SF. Pilot must measure this (Phase-0 empirical closure).
4. **Known bug:** `QELEventGeneratorINCL::fEb` is never assigned but is stored
   into GHEP `RemovalEnergy` on accept (`.cxx:286`) — the stored value is
   indeterminate. Do not consume GHEP `RemovalEnergy` for this tune.
5. The INCL path bypasses `QELUtils::BindHitNucleon`, so the Benhar-table
   recoil special case (`QELUtils.cxx:271`) never fires here.

**Correction (2026-09-02, `docs/incl-ground-state-review.md`, verified with a
runtime probe + 500k events):** point 1 describes `HitNucP4` (what the cross
section and lepton kinematics use), not the GHEP record — the record's hit
nucleon is rewritten **on-shell** from INCL after the cascade, so its `E_m`
is `−T`. Point 3 is superseded: the pre-FSI proton carries
`E_m = V₀ − T_ball`, `V₀ = T_F + S = 45.0 MeV` (floor `S = 6.83`), imposed by
INCL's energy balance at cascade insertion. The pre-FSI `|p_m|` is the
local-energy-reduced momentum, not the record's ball.

**Update (2026-09-04, fork branch `feature/incl-vertex-local-energy`,
`docs/incl-vertex-local-energy-option-plan.md`):** the vertex now follows
INCL's own scheme explicitly — the scattering is computed with the on-shell
local-frame nucleon `(p_red, E_ball − T_loc(r))` (`never`: the ball nucleon),
INCL's balance conserves `E_ball − V₀` by rescaling lepton and proton, and the
GHEP initial nucleon is written as the global nucleon `(p_ball, E_ball − V₀)`
with `RemovalEnergy = V₀ − T_ball` (now determinate, in [6.83, 45.0] MeV for
C12). So for samples made with these libraries the record's `E_m = V₀ − T_ball`
equals the pre-FSI proton's, and the record momentum is INCL's ball (with the
p_min(r) floor) in both local-energy settings; the local-energy choice is
visible in `|p_p′ − q|` and in the cross section.

## C12 pilot (2026-07-13) — Phase-0 closure + required source fix

Pilot: 500 events, e- on C12 at 2.445 GeV, spline
`eminus_C12_20260712-175458-df5.xml`, run
`gevgen-eminus_C12_20260713-135340-306-33c062` (+ gst sibling). Gates:

- 500/500 QEL events, rc 0, no `MaxXSec` violations.
- INCL FSI active: leading proton moved (>10 MeV/c) in 64% of events,
  mean final-state hadron multiplicity 2.44.
- **Phase-0 point 3 empirically closed:** vertex-level Em = omega − Tp − Trec
  has mean ≈ −20 MeV with 90% of strength below zero — as predicted,
  qualitatively unlike SF (no S_p floor).
- No Q2 cut in `_00_000` → Mott-dominated sample (median Q2 ≈ 0.05 GeV²);
  the omega/QE-peak comparison vs GEM26_22b needs the matching Q2-cut ladder
  (`_04_000`..`_08_000`, still to be cloned).

**Install-side bug fix required for ANY charged-lepton probe** (in
`feature/for_Anna`, INCLCascadeIntranuke.cxx:857):
`BaryonNumberConservation` mixed charge units — probe in |e|/3
(`GHepParticle::Charge`, TParticlePDG convention) vs target in +e
(`Target::Charge`) — so every electron event "violated" conservation and hit
`exit(1)`; the exit-with-open-TFile then aborted in ROOT teardown as a
misleading `double free or corruption`. Neutrino probes (charge 0) never see
it. Fixed by dividing the probe charge by 3; `libGPhHadTransp` rebuilt
2026-07-13. Runs before the fix: `gevgen-eminus_C12_20260713-133628-*` and
`-133911-*` (rc −6).

## EMQE-only rule (do not relax casually)

`TuneGeneratorList.xml` restricts the tune to the QEL-EM thread. The stock
MEC/RES/DIS-EM threads never reset the `INCLNucleus` singleton — under
`HadronTransp-Model = INCLCascadeIntranuke` they would cascade on a stale
nucleus. Extending this family is config-only but must use INCL-resetting
Module-1 threads:

- **EMMEC**: the `MEC-EM-INCL` thread pattern exists
  (`$GENIE/config/INCL26_07a/EventGenerator.xml`, `MECGeneratorINCL/NucleusGenINCL`
  — correlated NN cluster from INCL). Check `XSecModel@MEC-EM`
  (SuSAv2MECPXSec accepts EM; tensor nucleus coverage is limited).
- **RES/DIS**: swap Module-1 `genie::NucleusGenerator/Default` →
  `genie::NucleusGenerator/INCL` in the `RES-EM-INCL`/`DIS-EM-INCL` thread
  shapes (legacy chains read the hit nucleon off the record and never
  resample, so any `NucleusGenI` drops in).

## Comparison set

| Tune | Ground state | QE-EM xsec | FSI |
|------|--------------|------------|-----|
| `GEM26_11a` | Local Fermi Gas | Rosenbluth | hA2018 |
| `GEM26_22a` | Spectral Function | Rosenbluth | hA2018 |
| `GEM26_22b` | Spectral Function | UnifiedQEL | hA2018 |
| **`GEM26_44b`** | **INCL++** | UnifiedQEL | **INCL++** |

`22b`↔`44b` changes BOTH ground state and FSI (deliberate: the "full INCL"
configuration). Tune id: `GEM26_44b_00_000`. Q²-cut PP variants
(`GEM26_44b_04_000` …) can be cloned from the 22b pattern when needed.

`GEM26_44b_05_000` (added 2026-07-31): the Dutta Q²-cut variant —
`CommonParam.xml` byte-copied from `GEM26_22b_05_000` (`EM-MinQ2Limit = 1.18`).
The cut binds on this path with no further changes: `UnifiedQELPXSec::XSec`
returns 0 below `kinematics::electromagnetic::kMinQ2Limit` for EM
(UnifiedQELPXSec.cxx:128-132), and both the event generator (accept/reject)
and `INCLQELXSec` (spline integration) evaluate through it.

## Spline generation (slow — worse than 22b)

`EM_Dipole_incl` integrates over the INCL ground state via `INCLQELXSec`
(default `NumNucleonThrows = 500`, each throw re-initializing the INCL
nucleus). Prefer grid generation with `--expected-lifetime 48h` (the 22b SF
Fe56 spline already needed >13 h). Throttle fallback: tune-local
`INCLQELXSec.xml` lowering `NumNucleonThrows` (precision tradeoff on the
e-p/e-n channel ratio via the spline normalization).

## Environment

Needs the `genie_inclxx` installation (INCL++ libs + `INCLXX_DATA_DIR`); local
runs get it from `config/env/genie_inclxx.json`, grid workers source
`thisinclxx.sh` from the install tarball.

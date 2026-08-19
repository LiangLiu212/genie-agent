# Plan: GEM26_44b — electron scattering with INCL++ ground state + INCL++ FSI

## Context

The EM (e,e'p) campaign (results/prd-analyzer-v0.1, E91-013 replication) compares
GENIE ground-state/xsec models on C12/Fe56: LFG, Benhar SF, SF2024, SuSAv2 —
all with hA2018 FSI. The user now wants a configuration where BOTH the nuclear
ground state and the FSI come from INCL++. Nothing in `genie-agent/tunes/`
does this today; the building blocks exist in the active `genie_inclxx`
install but are unassembled:

- INCL ground state = `genie::NucleusGenINCL/Default` — a `NucleusGenI`
  (EventRecordVisitorI), NOT a `NuclearModelI`. (`genie::INCLNuclearModel` and
  `genie::HINCLCascadeIntranuke` are dead master_config stubs with no classes.)
- INCL FSI = `genie::INCLCascadeIntranuke/Default`.
- The standard EM QE generators dynamic_cast `NuclearModel` to `NuclearModelI`,
  so `NucleusGenINCL` only works through `genie::QELEventGeneratorINCL`
  (casts to `NucleusGenI`, QELEventGeneratorINCL.cxx:396-397). That generator
  is EM-capable (no CC guard; `ComputeFullQELPXSec` handles EM min-angle,
  QELUtils.cxx:544-568; `SF-MinAngleEMscattering` param) but is wired for EM
  nowhere. Verified by direct read 2026-07-12.
- FSI/GS share the `INCLNucleus` singleton: `INCLCascadeIntranuke` cascades on
  the same nucleus `NucleusGenINCL` reset for the event — the two are designed
  to be used together.

**User decisions (2026-07-12):** one new family only (full INCL GS + INCL FSI;
no FSI-isolation intermediate). C12 pilot first at 2.445 GeV; Fe56/Q2-ladder
decided after. **Investigate the INCL energy bookkeeping BEFORE any runs**
(Phase 0 below is a gate): `NucleusGenINCL` sets GENIE `RemovalEnergy=0`
(FIXME, NucleusGenINCL.cxx:263), `BindHitNucleon` ignores `Eb`
(`(void)Eb`, line 357), and the accept branch stores `fEb` into the GHEP
nucleon (QELEventGeneratorINCL.cxx:~286) — the (e,e'p) missing-energy analysis
is directly sensitive to this convention.

GENIE source changes: **one bug fix required** (found by the Phase 2 pilot,
2026-07-13; the tune itself is still a pure GXMLPATH overlay — never edit
`$GENIE/config`):

- `INCLCascadeIntranuke::BaryonNumberConservation` (INCLCascadeIntranuke.cxx:857)
  summed `Probe()->Charge()` (in **|e|/3**, TParticlePDG convention) with
  `Target::Charge()` (in **+e**) for the initial-state charge, while the
  final-state sum divides per-particle charge by 3. Neutrino probes (charge 0)
  never trip it; ANY charged-lepton probe fails the check on every event →
  `exit(1)` mid-run. The exit with an open GHEP TFile then aborts in ROOT
  teardown (`TROOT::CloseFiles` → `WriteStreamerInfo` → cling autoload during
  `_dl_fini` → `double free or corruption`), which masks the real error — the
  only stdout symptom is the FATAL branch's `evrec->Print`, which looks like a
  successful event print. Fixed on `feature/for_Anna` by dividing the probe
  charge by 3 (one line + comment); rebuilt `libGPhHadTransp`. Verified with a
  same-seed 2-event run (rc 0). Run fingerprints record the install as dirty
  until the fix is committed upstream.

## Phase 0 (GATE): INCL vertex energy bookkeeping investigation

Deliverable: a short note (`genie-agent/tunes/GEM26_44b/README.md` section +
entry in `results/prd-analyzer-v0.1/open_questions.md`) answering:

1. What is `INCLNucleus::getHitNucleonEnergy()` exactly — kinetic+potential?
   on-shell mass + Fermi KE − potential? Read
   `Generator/src/Physics/NuclearState/INCLNucleus.cxx` (energy accessors,
   `reset()`, particle initialization) and the relevant upstream INCL++
   classes (`inclxx_genie/inclxx` — `NuclearPotential`, `ParticleTable`) to
   pin the convention. Is the hit nucleon off-shell in the GHEP record
   (E != sqrt(p²+m²))?
2. Where does the binding show up in energy balance: given `RemovalEnergy=0`,
   what does `ComputeFullQELPXSec`/`QELUtils` do with the INCL 4-momentum,
   and what vertex-level Em = omega − Tp − Trec distribution is implied?
   Trace `fEb` in QELEventGeneratorINCL (is it ever nonzero?).
3. What does the remnant bookkeeping look like after INCL FSI + ABLA
   de-excitation (does the A−1 remnant carry excitation energy that restores
   the Em budget)?
4. Cross-reference the existing recoil-convention open question
   (Dutta vs BindHitNucleon, QELUtils.cxx:271) — record whether the INCL path
   sidesteps or worsens it.

Only after this note is written and the convention understood, proceed.
(A 3-event diagnostic run in Phase 2 step 1 is allowed as part of the
investigation if code reading is ambiguous — it is a smoke test, not
production.)

## Confirmed chain (user, 2026-07-12 review)

For eminus the chain is unique — verified in source:
`NucleusGenINCL -> QELEventGeneratorINCL -> UnifiedQELPXSec`.
(QELEventGeneratorINCL is the only generator accepting a NucleusGenI; it
evaluates in kPSQELEvGen; UnifiedQELPXSec is the only kPSQELEvGen-capable
model whose ValidProcess accepts EM — LwlynSmith/Nieves are IsWeakCC-only.)

Template = the working Hybrid CC chain, swapping NucleusGenHybridStruck ->
NucleusGenINCL at its two occurrences (QELEventGeneratorINCL param_set and
UnifiedQELPXSec IntegralNucleusGen). Note NucleusGenHybridStruck/Default is
itself a wrapper: FermiMover (SF/LFG) momentum + INCL-vertex=true wrapping
NucleusGenINCL — i.e. Hybrid = SF/LFG momentum with INCL nucleus/vertex init;
full-INCL drops the wrapper so momentum AND vertex come from INCL++.

## Channel coverage beyond QE (reviewed with user 2026-07-12)

ALL FOUR channels can take the INCL ground state CONFIG-ONLY (user-corrected
2026-07-12; verified in source):

| Channel | INCL GS config-only route | Existing EM thread (INCL26_07a, inert) |
|---|---|---|
| QE  | QELEventGeneratorINCL/EM-I-Default (this plan's thread) | none — new QEL-EM thread here |
| MEC | MECGeneratorINCL/NucleusGenINCL (correlated NN cluster, GenerateCluster/GetClusterBindP4) | MEC-EM-INCL (4-module), SuSAv2MECPXSec accepts EM (kPSTlctl) |
| RES | swap Module-1 to NucleusGenerator/INCL in the RES-EM-INCL shape | RES-EM-INCL (ships Module-1=/Default=Hybrid) |
| DIS | same Module-1 swap in DIS-EM-INCL shape | DIS-EM-INCL (ships /Default) |

- Why RES/DIS need no special generator: legacy chains sample the nucleon
  once in Module-1; RESKinematicsGenerator/DISKinematicsGenerator never
  resample — they read init_state.Tgt().HitNucP4() off the record
  (DISKinematicsGenerator.cxx:76, "can be off m-shell"), no NuclearModelI
  dependence. NucleusGenerator dispatcher's INCL param_set (-> NucleusGenINCL)
  already exists in config/NucleusGenerator.xml. The shipped -INCL threads
  using /Default (Hybrid) is a physics choice, not a technical necessity.
  QE alone needs the dedicated generator (resamples inside its rejection
  loop via the model interface).
- Stock RES-EM/DIS-EM/MEC-EM threads never touch the INCLNucleus singleton →
  must not run under INCLCascadeIntranuke (basis of the QEL-EM-only
  TuneGeneratorList). Extensions must use INCL-resetting Module-1 threads.
- With the Module-1 swap, a genlist-EM inclusive run can be all-INCL across
  QE/MEC/RES/DIS, config only; per-channel physics validation still owed.
  EMMEC via MEC-EM-INCL is the natural first extension; SuSAv2 MEC tensor
  nucleus coverage caveat (Fe56 scaling) applies.

## Phase 1: new tune family `genie-agent/tunes/GEM26_44b/`

Naming: digit convention extended — 1=LFG, 2=SF, 3=SF2024, **4=INCL++ GS**;
letter `b` = UnifiedQELPXSec (forced: `ComputeFullQELPXSec` evaluates the xsec
in `kPSQELEvGen`; `RosenbluthPXSec` computes in `kPSQ2fE` and
`KineUtils::Jacobian` has no `kPSQELEvGen` case → Rosenbluth would abort).
`GEM*` prefix + genlist `EMQE` passes both validators
(`genie-agent/lib/validation.py`, `jobsub-agent/adapters/genie/common.py`).
README documents that this family also changes FSI (hA2018 → INCL++).

Copy `genie-agent/tunes/GEM26_22b/` as baseline, then:

1. **ModelConfiguration.xml** — two line changes:
   - `XSecModel@genie::EventGenerator/QEL-EM` → `genie::UnifiedQELPXSec/EM_Dipole_incl`
   - `HadronTransp-Model` → `genie::INCLCascadeIntranuke/Default`
   Leave `NuclearModel`/`NuclearModel@Pdg` lines as-is (unused by the INCL
   thread; generator uses its own SubAlg, integrator uses IntegralNucleusGen).

2. **EventGenerator.xml** — replace the `QEL-EM` param_set with the 6-module
   CC-INCL thread shape (verified at `config/INCL26_07a/EventGenerator.xml:162-171`),
   swapping generator and interaction list:
   ```
   Module-0 genie::InitialStateAppender/Default
   Module-1 genie::QELEventGeneratorINCL/EM-I-Default
   Module-2 genie::UnstableParticleDecayer/BeforeHadronTransport
   Module-3 genie::NucDeExcitationSim/Default
   Module-4 genie::HadronTransporter/Default
   Module-5 genie::UnstableParticleDecayer/AfterHadronTransport
   ILstGen  genie::QELInteractionListGenerator/EM-Default
   ```
   No VertexGenerator/FermiMover/PauliBlocker — `NucleusGenINCL` sets vertex
   and momentum itself; Pauli blocking is internal to INCL.

   Why neither existing EM thread works (reviewed with user 2026-07-12):
   - Stock 7-module `QEL-EM` (QELEventGeneratorSuSA monolith): casts its
     NuclearModel sub-alg to NuclearModelI — NucleusGenINCL (a NucleusGenI)
     fails the assert. Kinematics in kPSQELEvGen, vertex via VertexGenerator.
   - INCL26_07a's inert 11-module `QEL-EM-INCL` (legacy decomposed chain):
     INCL in name only — Module-1 `NucleusGenerator/Default` dispatches to
     `NucleusGenHybridStruck/Default` (SF/LFG; verified in
     config/NucleusGenerator.xml — only its `INCL` param_set selects
     NucleusGenINCL), and Module-2 `QELKinematicsGenerator/EM-Default` scans
     dsigma/dQ2 in kPSQ2fE with the nucleon at rest — incompatible with
     UnifiedQELPXSec (the same 0-xsec abort that forced 22b's thread
     override). Its `NucBindEnergyAggregator` (legacy post-FSI binding
     bookkeeping) is unnecessary on the INCL path where binding lives in
     INCL internal energies (Phase-0 topic).

3. **QELEventGeneratorINCL.xml** — tune-local copy of the install file
   (`config/QELEventGeneratorINCL.xml`), adding one param_set cloned from
   `CC-I-Default` (verified lines 43-50):
   ```xml
   <param_set name="EM-I-Default">
     <param type="double" name="Cache-MinEnergy"> 0.5 </param>
     <param type="alg"    name="NuclearModel"> genie::NucleusGenINCL/Default </param>
     <param type="string" name="HitNucleonBindingMode"> UseNuclearModel </param>
     <param type="double" name="MaxXSec-SafetyFactor"> 1.6 </param>
   </param_set>
   ```
   `Cache-MinEnergy` lowered 5.0 → 0.5: below it, KineGeneratorWithCache
   re-scans max-xsec per event, and our beams are 0.5-4 GeV.

4. **UnifiedQELPXSec.xml** — tune-local copy, adding a param_set modeled on
   `ZExp_lqcd_incl` (verified lines 90-95) but integrating over the INCL GS:
   ```xml
   <param_set name="EM_Dipole_incl">
     <param type="alg" name="XSec-Integrator">      genie::INCLQELXSec/Default    </param>
     <param type="alg" name="IntegralNucleusGen">   genie::NucleusGenINCL/Default </param>
     <param type="alg" name="IntegralNuclearModel"> genie::NuclearModelMap/Default</param>
     <param type="alg" name="CCFormFactorsAlg">     genie::LwlynSmithFFCC/Dipole  </param>
   </param_set>
   ```
   `CCFormFactorsAlg` is fetched unconditionally by LoadConfig but never
   evaluated for EM (same reasoning as GEM26_22b/README.md). EM form factors,
   Pauli config, binding mode inherit from the `Default` set via GENIE's
   param_set layering. `INCLQELXSec::Integrate` dynamic_casts
   `IntegralNucleusGen` to `NucleusGenI` and samples via
   `GenerateNucleon(..., BothRPResamping)` (INCLQELXSec.cxx:62-64,165;
   NucleusGenINCL.cxx:407-413 verified) — no GHepRecord needed, so gmkspl works.

5. **TuneGeneratorList.xml** — restrict `Default` to the single QEL-EM thread
   (NGenerators=1). RES/DIS-EM threads never reset the `INCLNucleus`
   singleton; running them with INCL FSI would cascade on a stale nucleus.
   This family is EMQE-only by construction.

6. **CommonParam.xml, MECInteractionListGenerator.xml** — byte-copies from
   GEM26_22b (stock EM-MinQ2Limit; the t04-t08 PP-ladder subdirs can be cloned
   later exactly as in 22b). **README.md** — family semantics, EMQE-only rule,
   Phase-0 energy-convention findings, MEC-EM deferral note (the
   `MECGeneratorINCL/NucleusGenINCL` pattern exists at
   INCL26_07a/EventGenerator.xml:519-527 if EMMEC is wanted later).

## Phase 2: C12 pilot (local, genie_inclxx installation)

1. **Config smoke test** (minutes; surfaces every LoadConfig assert —
   dynamic_cast failures die here, before physics):
   ```
   pixi run python genie-agent/scripts/run_gmkspl.py --probes eminus --targets C12 \
       --tune GEM26_44b_00_000 --genlist EMQE -e 0.5 -n 3 \
       --gxmlpath genie-agent/tunes --foreground --label gem26_44b-smoke
   ```
2. **C12 spline** — same command, `-e 3 -n 10` first (local pilot convention),
   background; check `outputs.spline_count > 0` and sigma(2.445) > 0 via
   plot/jq. INCL-folded integration (500 nucleus re-inits per throw batch)
   may be slow even for C12 — if local wall time is prohibitive, go grid
   early with `--expected-lifetime 48h`.
3. **Pilot gevgen** at E91-013 kinematics:
   ```
   pixi run python genie-agent/scripts/run_gevgen.py --probe eminus --target C12 \
       -n 500 -e 2.445 --cross-sections <abs path to step-2 spline> \
       --tune GEM26_44b_00_000 --genlist EMQE --gxmlpath genie-agent/tunes --foreground
   ```
   then `run_gntpc.py -f gst`.
4. **Pilot checks** (gate for scaling up):
   - all events generated, no `max_xsec<=0` abort, count `xsec > xsec_max`
     warnings (bump `MaxXSec-SafetyFactor` if frequent — MaxXSec is scanned
     with the nucleon at rest on this path, NucleusGenINCL.cxx:361-368);
   - INCL cascade actually ran (FSI-moved protons / remnant present);
   - omega/QE-peak position+width vs a matching GEM26_22b sample;
   - vertex-level Em distribution vs the Phase-0 prediction — this closes the
     investigation loop.

## Phase 3 (deferred until pilot passes; separate decision): Fe56 + grid

- Publish updated tunes tarball (jobsub-tarball skill); reuse the
  `genie_inclxx` install tarball label.
- Grid splines: `run_gmkspl_grid.py --probes eminus --targets C12 --targets Fe56
  --tune GEM26_44b_00_000 --genlist EMQE -e 10 -n 30 --tarball-label <install>
  --tune-tarball-label <tunes> --expected-lifetime 48h` (Fe56 INCL-folded
  spline is the CPU driver; the 22b SF Fe56 spline already needed >13h).
  Fallback if infeasible: tune-local `INCLQELXSec.xml` lowering
  `NumNucleonThrows` 500→~100 (README-flagged precision tradeoff on the
  e-p/e-n channel ratio), last resort: SF integrator (declared approximation).
- Do NOT reuse 22b splines: spline keys carry the xsec algorithm/config id;
  a mismatched key silently forces inline recomputation at gevgen startup.
- Q2-cut PP ladder (`GEM26_44b_04_000..08_000`) cloned from the 22b pattern
  when the analysis needs it.

## Verification summary

- Phase 0 note written and reviewed (gate).
- Smoke gmkspl exits 0 (config asserts pass).
- Spline: `outputs.spline_count > 0`, sigma monotone/positive at 2.445 GeV.
- Pilot gevgen: 500/500 events, gst produced, QE peak sane vs 22b, Em
  distribution matches Phase-0 expectation, FSI activity visible.
- All runs are logged with fingerprints (tune_xml_sha256 covers the new
  overlay); replay-without-LLM invariant preserved.

## Key risks

| Risk | Mitigation |
|---|---|
| `assert(fNucleusGen)` / `IntegralNucleusGen` cast abort | smoke test first; param_sets above are clones of the tested CC-I-Default/ZExp_lqcd_incl |
| Rosenbluth-style xsec under this generator (no kPSQELEvGen Jacobian) | UnifiedQELPXSec forced; documented in README |
| RemovalEnergy=0 skews Em analysis | Phase 0 gate + open_questions.md entry |
| INCL-folded spline CPU (Fe56) | grid 48h lifetime; NumNucleonThrows throttle fallback |
| Singleton staleness from non-INCL threads | TuneGeneratorList restricted to QEL-EM; EMQE-only rule |

Critical reference files:
- templates: `genie-agent/tunes/GEM26_22b/*` (baseline), install
  `config/QELEventGeneratorINCL.xml`, `config/UnifiedQELPXSec.xml`,
  `config/INCL26_07a/EventGenerator.xml` (thread shape)
- source ground truth: `Generator/src/Physics/{NuclearState/NucleusGenINCL.cxx,
  NuclearState/INCLNucleus.cxx, QuasiElastic/EventGen/QELEventGeneratorINCL.cxx,
  QuasiElastic/XSection/INCLQELXSec.cxx, HadronTransport/INCLCascadeIntranuke.cxx}`

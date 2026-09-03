# Plan: one INCL initial nucleon — local-energy frame + well-depth binding (GEM26_44b)

Status: plan only (2026-09-03), no code changed. Follows
[`incl-ground-state-review.md`](incl-ground-state-review.md), which found four
different "initial nucleons" per event. This plan makes them one.

## Convention to implement

For the struck nucleon at INCL radius r with resampled ball momentum p_ball
(direction p̂, T_ball = √(p_ball² + m²) − m, m = 938.2796):

    T_loc(r)  = local energy (KinematicsUtils::getLocalEnergy, evaluated on the resampled state)
    E_loc     = E_ball − T_loc(r)                       (local-energy frame, on-shell)
    p_i       = √(E_loc² − m²) · p̂                      (= "p_red": p_i² = p_ball² − p_min(r)²)
    E_i       = E_loc − V₀,   V₀ = Particle::getPotentialEnergy() = T_F + S = 45.00 MeV for T ≤ T_F
    E_m       ≡ m − E_i = V₀ − T_red,  T_red = E_loc − m   ∈ [S, V₀] = [6.83, 45.0] MeV

`(p_i, E_i)` is off-shell exactly like GENIE's other `UseNuclearModel` tunes;
`UnifiedQELPXSec` already handles it (`UnifiedQELPXSec.cxx:80-85`
ε_B = E_onshell − E = V₀, folded into q̃ at `:117-119`, flux factor with
E_onshell). It is used **everywhere**: cross section, lepton kinematics, INCL
energy balance at cascade insertion, and the GHEP record. Expected
r–p correlation of the nucleon the physics sees: LFG-like (falls with r).

## Edits (all under `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator/src`, branch off `feature/for_Anna`)

**E1 `Physics/NuclearState/INCLNucleus.{h,cxx}`**
- `ResamplingHitNucleon` (`.cxx:514-536`): evaluate `locE = getLocalEnergy(nucleus_, hitNucleon_)`
  *inside* the loop, after `adjustEnergyFromMomentum()`, and accept on `KE > locE`.
  On the resampled state the reflection ratio is 1, so the threshold is the strict
  `p_min(r)` and `E_loc ≥ m` is guaranteed (removes the NaN of §4 of the review).
- Replace the mutating getters (`.cxx:315-336`) by one const computation,
  e.g. `TLorentzVector getHitNucleonP4() const` returning `(p_i, E_i)` in MeV
  per the convention above (never `setEnergy`/`adjustMomentumFromEnergy` on
  `hitNucleon_` inside a getter). Keep `getHitNucleonMomentum()` /
  `getHitNucleonEnergy()` (`.h:66-67`) as wrappers so `NucleusGenINCL` keeps its calls.
- `getRemovalEnergy` (`.cxx:362-375`): return `m − E_i = V₀ − T_red` (the E_m
  analogue that analyses read from GHEP `RemovalEnergy`); delete the dead branches.
- `isRPValid` (`.cxx:476-487`) is already in reduced terms
  (`p < √((E_F − locE)² − m²)`); leave it.

**E2 `Physics/NuclearState/NucleusGenINCL.cxx`**
- `BindHitNucleon` (`:373-381`) and `setInitialStateMomentum` (`:252-263`): fill
  `HitNucP4` / the GHEP nucleon from the new getter (GeV); replace
  `nucleon->SetRemovalEnergy(0)` (`:263`) by `incl_nucleus->getRemovalEnergy()/1000`.
- `setTargetNucleusRemnant` (`:338-341`, `E = M_A − E_i`) unchanged — the remnant now
  carries the binding, as in the other tunes.
- Optional: make `SetHitNucleonOnShellMom` (`:425-428`) set the INCL particle's
  momentum, so the max-xsec scan (`QELEventGeneratorINCL.cxx:463-470`) stops being a no-op.

**E3 `Physics/QuasiElastic/EventGen/QELEventGeneratorINCL.{h,cxx}`**
- Initialise `fEb = 0.` in both constructors (`.h:49`); at accept replace
  `nucleon->SetRemovalEnergy(fEb)` (`.cxx:286`) by
  `nucleon->SetRemovalEnergy(nucleon->Mass() − p4ptr.E())` (= E_m of the convention).
- Nothing else: `:170` (`GenerateNucleon(fixRadius)`), `:181` (`BindHitNucleon`) and
  `:201-202` (`ComputeFullQELPXSec`) now conserve (probe + (p_i, E_i)).

**E4 `Physics/HadronTransport/G4INCLGENIEAvatar.cxx` — "always subtract the local energy"**
- `preInteraction`, non-hybrid branch, line 84:
  `oldTotalEnergy = lepton_initial_energy + particle1->getEnergy() − particle1->getPotentialEnergy();`
  → subtract `KinematicsUtils::getLocalEnergy(theNucleus, particle1)` as well.
  Compute it **before** line 87 (`transformToLocalEnergyFrame(theNucleus, particle1)`),
  which moves the particle itself into the local frame for the boost — no double
  subtraction. The balance then equals `E_e + E_i` of the interaction, so
  `enforceEnergyConservation` (`:452-464`; the functor `:471-511` scales the outgoing
  lepton *and* proton CM momenta by one factor α and writes the lepton back at
  `:388-390`) finds α = 1 (the proton's V(T ≈ 0.7 GeV) = 0, its locE = 0): **no
  rescaling of lepton or proton**, 3-momentum conserved in GHEP and the GHEP lepton
  equals the generator's.
- Lines 75-80 (`kHitNucleon` record entry ← `particle1` momentum/mass): move after
  line 87 so the INCL-side record holds the local-frame momentum, or drop it (the entry
  is only consumed by E5's rewrite).

**E5 `Physics/HadronTransport/G4INCLGENIECascadeAction.cxx`**
- `afterNPVAvatarUserAction` rewrite loop (`:103-110`): skip particles with
  `Status() == kIStNucleonTarget` (11) — keep `evr++`/`idx++` — so the GHEP
  initial nucleon stays the `(p_i, E_i)` written at accept (off-shell, like every
  other tune). Everything else keeps the current on-shell rewrite.

**E6 Rebuild** (clean env from `setup_env.sh`; GENIE's make does not track headers):
`make clean && make` in `Physics/NuclearState`; `make` in
`Physics/QuasiElastic/EventGen`; `make clean && make` in `Physics/HadronTransport`
(includes `INCLNucleus.h`). Then `refresh_genie_env.py --installation genie_inclxx`
is *not* needed (env unchanged) but bump the registry stamp.

**E7 Splines.** `INCLQELXSec` (`Physics/QuasiElastic/XSection/INCLQELXSec.cxx:153-177`)
integrates through `BindHitNucleon`, so the C12 EMQE spline of
`GEM26_44b_05_000` must be regenerated (the 07-31 job took 8053 s locally).
Shape validation (V3) can run on the existing spline — for a mono-energetic,
single-process `gevgen` the spline only normalises; final samples need the new one.
The spline/event sampling mismatch (`BothRPResamping` fresh nucleus per throw vs
`fixRadius` ball) is untouched by this plan.

## Validation

- **V1 probe** (`results/template/probe_incl_hitnuc.cxx`, add the new getter):
  2000 nuclei → `p_i² = p_ball² − p_min(r)²` exactly, `E_i = E_loc − 45.00`, no NaN.
- **V2 smoke**: 2-event `gevgen` with `QELEvent`/`QELKinematics` at NOTICE:
  `HitNucP4().M()` ≈ 0.89–0.93 GeV (off-shell), `pn:` = p_i; rc 0.
- **V3 shapes** (50k local, existing spline): `dump_hitnuc` + local ladder cache →
  record ⟨p⟩ ≈ 150 MeV/c, corr(p, r) ≈ −0.65; stage-2 `m − E_n = V₀ − T_red`
  (no longer empty, mean ≈ 31 MeV); stage 3 identical to stage 2 in E and
  `|p_p′ − q| = p_rec` exactly (no rescaling); post-FSI floor re-measured.
- **V4 physics**: new spline → 500k → `analysis/dutta-qe --local` and the v1.0
  INCL note ladders, before/after.

## Expected observables (from today's 500k sample, protons, aligned dump ⊗ ladder cache)

| quantity | today | after the change |
|---|---|---|
| momentum used by xsec / lepton kinematics | p_red: ⟨p⟩ 150 MeV/c, corr(p, r) −0.65 | same |
| momentum in the GHEP record | ball: ⟨p⟩ 225, corr +0.45, ≤ 270 | p_red (LFG-like), p95 ≈ 246 |
| initial energy in the lepton kinematics, E − m | +14 MeV (on-shell) | −31 MeV → ω at fixed final state **+45 MeV**; QE peak and Q² slice shift; xsec via ε_B = 45 MeV |
| E_m (pre-FSI) | V₀ − T_ball: mean 17.5, p5/50/95 7.5/15.6/34.0 | V₀ − T_red: mean **31.0**, 13.4/32.4/44.0 |
| Dutta windows [10,25) / [30,50) | 58 % / 10 % | 27 % / 58 % |
| ⟨p⟩ in [30,50) window (frac p < 100) | 138 MeV/c (9 %) | 106 MeV/c (41 %) |
| E_m–p_m correlation | −0.99 (deep ↔ slow) | −0.98 (deep ↔ slow) |
| GHEP bookkeeping | initial nucleon on-shell; lepton + proton rescaled by INCL; 3-momentum not conserved | initial nucleon off-shell; no rescaling; conserved |

Reading: the deep window inherits the low-momentum (s-shell-like) strength, and
the E_m–p_m pairing keeps the physical sign, but the bulk of the strength moves
from the p-shell window to 30–45 MeV — expect *worse* agreement with fig 9's
17.5 MeV peak and *better*-shaped |p_m| in the s-shell window. The +45 MeV move of
the lepton kinematics is the largest single effect and changes the Dutta Q² slice
population; compare inclusive-style ω distributions before/after.

## Alternative / companion

A configurable vertex local-energy option (`always` / `never`, plus a separate
momentum-floor switch), with the same edit points, is planned in
[`incl-vertex-local-energy-option-plan.md`](incl-vertex-local-energy-option-plan.md);
this plan's E4 corresponds to its `always` value.

## Notes / risks
- T_ball ≤ T_F always, so V₀ is exactly 45.00 MeV (the energy dependence of the
  potential never enters for the struck nucleon).
- The fuzzy r–p correlation now enters only through INCL's own sampling of r;
  the acceptance floor becomes the strict `p_min(r)`.
- The record's neutrons keep INCL's single nucleon mass (1.29 MeV off PDG).
- `results/template/make_incl_groundstate_record.py` needs its "record = ball"
  assumptions swapped (record = truncated-ball *reduced*; E_m = V₀ − T_red) to
  serve as the after-change check.

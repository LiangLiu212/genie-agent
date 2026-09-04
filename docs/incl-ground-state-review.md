# INCL++ nuclear ground state in GENIE — position, momentum, potential energy, local energy

Review of the INCL++ ground-state model as it reaches GENIE events in the
`GEM26_44b` tune (INCL++ ground state + INCL++ cascade FSI), 2026-09-02.
Sources: the vendored INCL++ library
`/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/inclxx_genie/inclxx/` and the
GENIE interface in `…/GENIE_INCLXX/Generator` (`feature/for_Anna` @
`cc9c9b417`; the NuclearState/QuasiElastic libraries were built 2026-06-30
from the same source — no changes since). Evidence: source reads (file:line
below), a runtime probe of the interface
([`results/template/probe_incl_hitnuc.cxx`](../results/template/probe_incl_hitnuc.cxx)),
a 3-event `gevgen` run with the generator's NOTICE lines, and the 500k-event
e⁻ C12 2.445 GeV sample of 2026-09-01 (hit nucleon dumped with
`dump_hitnuc`, per-event aligned with the v1.0 ladder cache). Figure:
[`results/prd-analyzer-v1.0/incl_groundstate_record_c12.png`](../results/prd-analyzer-v1.0/incl_groundstate_record_c12.png)
(script [`make_incl_groundstate_record.py`](../results/template/make_incl_groundstate_record.py)).

## 0. The chain in one table

Four different "initial nucleons" exist in one event. Everything below hangs
on keeping them apart.

| stage | position | momentum | energy | where |
|---|---|---|---|---|
| (a) INCL ground state | MHO density, r–p correlated (fuzzy) | Fermi sphere p_F = 270.34 | on-shell, V₀ = 45.0 MeV kept separately | `ParticleSampler`, `Nucleus::initializeParticles` |
| (b) resampled struck nucleon = **GHEP record** | same r as (a) | **uniform p_F ball, accepted if T > T_loc(r)** | **on-shell** `√(p²+m²)` | `INCLNucleus::ResamplingHitNucleon`; written back to GHEP after the cascade |
| (c) cross section + lepton kinematics | — | **local-energy-reduced** `p_red` | on-shell `E_ball − v_loc` | `getHitNucleonMomentum/Energy` → `HitNucP4` |
| (d) cascade insertion → **pre-FSI proton in GHEP** | — | — | struck nucleon counted as `E_ball − V₀` | `GENIEAvatar::postInteraction` rescales the QE proton |

Consequences for the analyses: the record's stage-2 hit nucleon has
`m_N − E_n = −T` (no binding at all); the pre-FSI proton carries
`E_m = ω − T_p′ = V₀ − T_ball ∈ [S, V₀] = [6.83, 45.0]` MeV; and the pre-FSI
`|p_m| = |p_p′ − q|` is the reduced `p_red`, not the record's momentum.

## 1. Position

**Density.** For `6 < A ≤ 19` INCL uses the modified harmonic oscillator,
`ρ(r) ∝ (1 + α x²) e^{−x²}`, `x = r/a`
(`incl_physics/src/G4INCLNuclearDensityFactory.cc:61-66`,
`include/G4INCLNDFModifiedHarmonicOscillator.hh:51-54`). With the default
fuzzy r–p correlation (coefficient < 1) the parameters come from the HFB
table `data/table_radius_hfb.dat` (`utils/src/G4INCLParticleTable.cc:1204-1215,
1254-1260`; note the deliberate name swap `getRadiusParameter → α`,
`getSurfaceDiffuseness → a`). **C12: proton a = 1.72905 fm, α = 0.849882;
neutron a = 1.71874 fm, α = 0.83426.** Maximum radius
`R_max = 5.5 + 0.3(A−6)/12 = 5.65 fm` (`:1226-1227`); tabulated RMS radius
2.47 fm (`positionRMS[6][12]`, `:156`); transmission radius 3.35 fm for
protons (`G4INCLNuclearDensity.cc:132-136`).

**How positions are drawn.** Not from ρ(r) directly: INCL builds the
*reflection-radius* distribution `g(R) = −R³ dρ/dR` and its CDF `F(R)`
(`G4INCLNuclearDensityFactory.cc:42-87`, `G4INCLIFunction1D.cc:86-111`), and
stores the inverse table `R(u)` with `u = F(R)^{1/3}`. A nucleon of momentum
`p` gets reflection radius `R(p/p_F)` and a position uniform inside that
sphere (`G4INCLParticleSampler.cc:107-118`) — uniform filling of nested
spheres reproduces ρ(r) exactly when `dN/dR ∝ −R³ρ′`. The defining relation:

    F(R(p)) = (p/p_F)³ — the fraction of nucleons with reflection radius
    below R(p) equals the fraction of the Fermi sphere below p.

**Record check** (figure, top left): the hit-nucleon radius follows
`r²ρ_MHO(r)` with the HFB parameters: ⟨r⟩ = 2.27 fm (model 2.31), RMS 2.43
(table 2.47); a ~2 % deficit beyond 4.5 fm not investigated. The position is
the one quantity that survives the whole chain untouched (GENIE never
resamples it; `X4` is stored in fm, unconverted —
`NucleusGenINCL.cxx:221`).

## 2. Momentum

**INCL ground state.** Fermi momentum `p_F = 1.37 ħc = 270.34 MeV/c`
(`ConstantFermiMomentum`, `G4INCLConfig.cc:51-53`, `G4INCLGlobals.hh:14,20`),
isospin factor `(2Z/A)^{1/3} = 1` for C12
(`G4INCLNuclearPotentialIsospin.cc:38,46`). Momenta are uniform in the Fermi
sphere; with the strict correlation the radius follows `R(p/p_F)` as above.
The default is the **fuzzy** correlation
(`rpCorrelationCoefficientProton = 0.5`, `…Neutron = 0.73`,
`G4INCLConfig.cc:59-61`): `(x, y)` are correlated Gaussians turned into
uniforms, `|p| = y p_F`, reflection sphere `R(x)`
(`G4INCLParticleSampler.cc:128-140`, `G4INCLRandom.cc:146-165`) — the
marginals are exact, only the joint correlation is loosened, and the
"uncorrelated momentum" `x p_F` is what wall reflection uses
(`G4INCLParticle.hh:1100-1105`). No centre-of-mass correction is applied to
the target (`internalBoostToCM` is projectile-only). GENIE never sets the
coefficient (`INCLNucleus.cxx:181` is commented out), so these defaults hold.

**What GENIE does with it.** The struck nucleon is a random index of the
right species (`INCLNucleus::getNucleon`, `:457-474`), and then every
accept/reject throw calls `ResamplingHitNucleon()` (`:514-536`,
via `QELEventGeneratorINCL.cxx:170` → `NucleusGenINCL::GenerateNucleon(fixRadius)`):

```cpp
double locE = KinematicsUtils::getLocalEnergy(nucleus_, hitNucleon_);   // once, original nucleon
while(true){ momentumVector = Random::sphereVector(theFermiMomentum);    // uniform in the global p_F ball
  ...; if(KE > locE) break; }
```

The position is untouched; the momentum is redrawn uniformly in the ball and
accepted when `T > T_loc(r)` (§4). The in-code comment
(`QELEventGeneratorINCL.cxx:98-103`, "TODO: understand the effect of the
re-sampling") acknowledges it. **So the record's momentum is not INCL's
correlated ground state**: it is a p_F ball with an r-dependent floor.

**Record check** (figure, top right and middle left): `|p| ≤ 270.3` at every
radius; the marginal is the r-integrated truncated ball (⟨|p|⟩ 225.3 vs model
225.2, pure ball 202.8); the 1st/5th percentile and ⟨p⟩(r) per radius bin
follow the truncated-ball prediction with `p_min(r) = p_F F(r)^{1/3}` to
1–3 MeV/c (1st percentile 62/117/201/252/269 vs model 58/117/204/254/269 at
r ≈ 0.4/1.9/2.9/3.9/4.9 fm). Correlation `corr(p, r) = +0.455` — the mirror
image of LFG's −0.70 (there the *ceiling* k_F(r) falls with r; here the
*floor* rises).

**The momentum the physics actually used is different again.** For the cross
section and the lepton kinematics, `NucleusGenINCL::BindHitNucleon`
(`:354-382`) fills `HitNucP4` from `INCLNucleus::getHitNucleonMomentum/Energy`
(`INCLNucleus.cxx:315-336`), which subtract the local energy and rescale the
momentum on-shell:

```cpp
hitNucleon_->setEnergy(oldEnergy - localEnergy);  hitNucleon_->adjustMomentumFromEnergy();
```

The probe confirms `v_loc` after resampling is `T_loc(r)` (corr 0.98 with the
formula), and the 3-event NOTICE run shows `HitNucP4().M() = 0.93828 GeV`
at accept — **on-shell, reduced momentum**. Per event (dump ⊗ ladder cache,
346k protons): `p_i = |p_p′ − q|` has ⟨p_i⟩ = 152 MeV/c, `corr(p_i, r) = −0.65`,
24 % below 100 MeV/c (record: 1 %), and tracks
`√((E_ball − T_loc(r))² − m²)` (corr 0.977; figure, bottom-left inset). At
the surface the reduced momentum is ~10 MeV/c. This is the `|p_m|` the
Dutta-style pre-FSI analysis sees — a local-Fermi-gas-like falling profile —
while the record shows the rising ball floor.

## 3. Potential energy

**Definition.** Default `IsospinEnergyPotential` (`G4INCLConfig.cc:34-36`,
also what GENIE sets — `NucleusGenINCL.xml:54`). Depth
`V₀ = T_F + S` with `T_F = √(p_F² + m²) − m = 38.17 MeV` and the INCL
separation energy `S = 6.83 MeV` (`INCL_DEFAULT_SEPARATION_ENERGY`,
`G4INCLParticleTable.cc:306`, target-independent by default):
**V₀ = 45.00 MeV** for C12 protons and neutrons
(`G4INCLNuclearPotentialIsospin.cc:29-52`). Energy dependence above the Fermi
energy (`G4INCLNuclearPotentialEnergyIsospin.cc:18,28-44`):

    V(T) = V₀                          for T ≤ T_F
    V(T) = V₀ − 0.287 (T − T_F)        above, clipped at 0 (→ 0 at T ≈ 195 MeV)

so a 0.7 GeV QE proton feels **no** potential on its way out. INCL nucleon
mass 938.2796 MeV for both species (`:26, 349-350`) — the record's neutrons
sit exactly m_n − m_p = 1.29 MeV off the PDG mass.

**Bookkeeping.** The particle's `theEnergy` is on-shell inside the nucleus;
`V` is stored separately (`G4INCLParticle.hh:862-868`) and subtracted
whenever an "outside" energy is needed: `Nucleus::computeTotalEnergy` sums
`T − V`, and emission pays it, `T_out = T_in − V(p) + ΔQ`
(`G4INCLTransmissionChannel.cc:31-45`, `G4INCLSurfaceAvatar.cc:166-191`) —
the separation energy is *inside* V₀, there is no second subtraction.

**Where it enters the GENIE event.** Not in the cross section and not in the
lepton kinematics (stage (c) is on-shell). It enters when the QE proton is
handed to INCL: `G4INCLGENIEQELChannel.cxx:22-36` overwrites the struck INCL
particle with the outgoing proton momentum, on-shell; then the non-hybrid
`GENIEAvatar::postInteraction` (the `kNucmINCL` path taken by `GEM26_44b`)
enforces INCL's energy balance with the struck nucleon counted as
`E_ball − V₀` (`G4INCLGENIEAvatar.cxx:84`, `oldTotalEnergy = lepton_initial_energy
+ particle1->getEnergy() − particle1->getPotentialEnergy()`). The
`ViolationLeptonEMomentumFunctor` (`:455-511`) boosts the outgoing **lepton and
proton** to the probe+nucleon CM frame and scales both CM momenta by one factor α
until `Σ(E − V) + E_lepton` matches; the rescaled lepton is written back to the
record (`:388-390`; the avatar holds the cascade action's own record,
`INCLCascadeIntranuke.cxx:316`), so the GHEP lepton is no longer the
generator's: measured over the 500k sample, the record's Q² sits 0.5–1.8 % below
the selected `Q2s` (mean −1.3 %, i.e. E′ lowered by ≈ 20 MeV), and the record's
energy balance is exact only with that rescaled lepton. The net condition is
`T_p′ = ω + T_ball − V₀` with ω from the rescaled lepton.
`afterNPVAvatarUserAction` (`G4INCLGENIECascadeAction.cxx:89-108`) then rewrites
**every** pre-existing GHEP particle from the INCL-side record with
`E = √(p² + m²)`: the pre-FSI proton and the lepton get the rescaled momenta, and
the initial nucleon gets the raw ball momentum back. **Measured**: `E_m(pre-FSI) = ω − T_p′ = 45.00 − T_rec` to
0.01 MeV over 346k events (figure, bottom right), range [6.83, 44.9], mean
17.5. The effective removal energy of the INCL chain is therefore
**V₀ − T = S + (T_F − T)**: a Fermi-gas binding with the well depth, floor
at S — not the `v_loc − T_i` of the Phase-0 notes (which described stage (c),
not what reaches the record).

## 4. Local energy

**Formula** (`G4INCLKinematicsUtils.cc:44-77`):

```cpp
pfl0 = (T ≤ T_F) ? p_F : sqrt(tf0 (tf0 + 2m)),  tf0 = V(p) − S      // effective Fermi momentum
pl   = pfl0 * getMinPFromR(t, r * R(p/pfl0) / R(p_refl/pfl0))       // local Fermi momentum at r
vloc = sqrt(pl² + m²) − m
```

`getMinPFromR` is the inverse of the reflection map (§1): `p_min(r)` is the
smallest momentum that can reach radius r, so **T_loc(r) = √(p_min(r)² + m²) − m
is 0 at the centre and T_F = 38.2 MeV at R_max** (C12: 1.1 MeV at 1.1 fm,
10 at 2.1, 25 at 3.1, 35 at 4.1 fm; figure, middle right). Physically INCL
keeps one constant well but measures a collision's energy relative to the
*local* Fermi sea; by default it is applied only to the first collision
(`FirstCollisionLocalEnergy`, `G4INCLConfig.cc:37-40`;
`G4INCLInteractionAvatar.cc:310-325`, `:79-92`), subtracting `vloc` and
rescaling the momentum (`transformToLocalEnergyFrame`, `:36-42`).

**Three uses in the GENIE chain.**
1. *Acceptance threshold* of the resampling (§2): evaluated once on the
   original correlated nucleon; with the fuzzy correlation the radius is
   rescaled by `R(y)/R(x)`, which is why the record floor matches the strict
   `p_min(r)` only to a few MeV/c.
2. *Reduction of the struck nucleon for the cross section / lepton kinematics*
   (§2): `getHitNucleonMomentum/Energy` subtract `T_loc(r)` and rescale the
   momentum — at the surface the interaction sees an almost stationary
   nucleon.
3. *Cascade insertion*: `transformToLocalEnergyFrame` at
   `G4INCLGENIEAvatar.cxx:87` before boosting, and the `energy + locE`
   restorations at `:546-548, 565-567`.

**Side effect (bug).** When `E − v_loc < m` (accepted `T_ball` just above the
original threshold, `T_loc` of the resampled state larger),
`adjustMomentumFromEnergy` zeroes the momentum and the "restore" step
divides by it: the INCL particle's momentum becomes NaN until the next throw
resets it (probe: `p_now` NaN in a fraction of throws; the returned `p3` is 0
for those). Harmless for the accepted event only because the record is later
rewritten from the ball momentum (§3).

## 5. What each analysis stage sees (Dutta-style ladders)

| ladder stage | quantity | INCL chain value |
|---|---|---|
| 2 — record hit nucleon | `m_N − E_n`, `|p_n|` | `−T_ball` (on-shell), ball with floor `p_min(r)`, ≤ 270 MeV/c |
| 3 — pre-FSI proton | `ω − T_p′`, `|p_p′ − q|` | `V₀ − T_ball` ∈ [6.83, 45] MeV; `≈ p_red(r)`, LFG-like falling profile |
| 4 — post-FSI | — | cascade on the same nucleus; QE proton pays `V(T) = 0` at exit |

The empty stage-2 panels and the stage-3 floor "at ~5 MeV" in the INCL note
are exactly `−T` and `S = 6.83` MeV; the stage-2/stage-3 `|p_m|` mismatch
(ball vs 100–220 MeV/c plateau) is the reduced momentum, not FSI.

## 6. Issues for upstream (all verified in source and data)

Update 2026-09-03: items 2–6 and the vertex part of 1 are addressed on the fork
branch `feature/incl-vertex-local-energy` (`d7cd3f5d4`; plans in
`incl-vertex-local-energy-option-plan.md`, `incl-local-frame-binding-plan.md`);
items 7–8 remain.

1. `ResamplingHitNucleon` replaces INCL's correlated momentum by a global-p_F
   ball with a one-sided local-energy cut (`INCLNucleus.cxx:514-536`).
2. The cross section and lepton kinematics use an on-shell nucleon with the
   local-energy-*reduced* momentum (`:315-336`); no binding energy enters the
   QE kinematics at all.
3. Energy conservation is re-imposed only afterwards, by INCL scaling the
   outgoing lepton *and* proton CM momenta by a common factor
   (`G4INCLGENIEAvatar.cxx:84, 455-511`; lepton written back at `:388-390`), so
   the GHEP lepton differs from the generator's and the record does not
   conserve 3-momentum between the initial nucleon, lepton and pre-FSI proton
   (the remnant absorbs it).
4. The initial nucleon in GHEP is rewritten from the INCL side after the
   cascade (`G4INCLGENIECascadeAction.cxx:99-108`): it is not the 4-vector the
   kinematics used.
5. `getHitNucleonMomentum` corrupts the INCL particle (NaN momentum) when
   `E − v_loc < m`.
6. `RemovalEnergy` is written twice (0 at `NucleusGenINCL.cxx:263`, then the
   never-assigned `fEb` at `QELEventGeneratorINCL.cxx:286`); the dump shows a
   constant 7.5 × 10⁻⁹⁰.
7. Spline integration (`INCLQELXSec`, `BothRPResamping` → fresh correlated
   nucleus per throw) and event generation (`fixRadius` → ball at frozen r)
   sample different initial-state distributions.
8. `X4` positions are stored in fm; `SetHitNucleonOnShellMom` is a no-op, so
   the max-xsec momentum scan never reaches the interaction.

## 7. Corrections to earlier notes

- Phase-0 (`results/prd-analyzer-v0.1/open_questions.md`, tune README): "the
  GHEP hit nucleon is written with `E = √(p²+m²) − v_loc`" describes
  `HitNucP4` (stage c), not the record; the record is on-shell and its `E_m`
  is `−T`. "Vertex-level `E_m = v_loc − T_i`" is superseded by the measured
  `E_m = V₀ − T` (stage d).
- INCL note (`results/prd-analyzer-v1.0/electron_c12_scattering_genie_incl.md`):
  the pre-FSI floor is `S = 6.83` MeV, not "5 MeV"; the stage-3 `|p_m|` is the
  reduced momentum.

## Reproduce

```bash
# hit-nucleon dump (genie_inclxx spack env, recipe in dump_hitnuc.cxx)
dump_hitnuc results/prd-analyzer-v0.1/cache/hitnuc_c12/GEM26_44b_05_000.csv genie-agent/genie-runs/GEM26_44b_05_000-2026-09-01/*.ghep.root
# figure + model-vs-record table (needs the v1.0 ladder cache for the bottom row)
pixi run python results/template/make_incl_groundstate_record.py
# interface probe (build recipe in-file; GXMLPATH=genie-agent/tunes)
results/template/probe_incl_hitnuc 2000 probe.csv
```

# Plan: make the GENIE–INCL QE vertex honour INCL's local-energy option

Status: **implemented 2026-09-03** on the fork branch
`feature/incl-vertex-local-energy` (`LiangLiu212/Generator` @ `d7cd3f5d4`, off
`feature/for_Anna` @ `cc9c9b417`), together with the binding plan's getter/record
items; the `genie_inclxx` install now runs these libraries. Decisions taken with
the user on 2026-09-03 (single switch; QE avatar keeps counting as the first
collision). Validation (20k e⁻ C12 EMQE events per setting, existing spline):
record nucleon = interaction nucleon (invariant mass 892.6 MeV), stage-2 and
stage-3 E_m identical, `|p_p′ − q| = p_rec` to 0.004 MeV/c, record `Q2 == Q2s`,
`E_m = V₀ − T` to 0.01 MeV; corr(p, r) = −0.67 (on, ⟨p⟩ 147 MeV/c, E_m mean
31.5) / +0.45 (`never`, floor kept, ⟨p⟩ 226, E_m mean 17.4; fork commit of
2026-09-04 — the first version had dropped the floor for `never`: ⟨p⟩ 203,
corr 0.00). Not done: new splines (E7) and the tune overlay (E8) — the `never`
runs used a scratch `GXMLPATH` override of `NucleusGenINCL.xml`.
Companion to [`incl-local-frame-binding-plan.md`](incl-local-frame-binding-plan.md)
(the E = E_red − V₀ convention) and grounded in
[`incl-ground-state-review.md`](incl-ground-state-review.md).

## Why

INCL++ has `localEnergyBBType` / `localEnergyPiType` ∈ {`always`,
`first-collision`, `never`} (`utils/include/G4INCLConfigEnums.hh:30-34`), honoured
in the cascade by `InteractionAvatar::shouldUseLocalEnergy()`
(`incl_physics/src/G4INCLInteractionAvatar.cc:310-325`) and by avatar generation
(`G4INCLStandardPropagationModel.cc:337-347`). In GENIE:

- the option never reaches the vertex — every vertex-side use calls
  `getLocalEnergy` unconditionally: `INCLNucleus.cxx:318, 333` (getters), `:480`
  (`isRPValid`), `:516` (`ResamplingHitNucleon`), `NucleusGenINCL.cxx:140` (MEC
  cluster), `G4INCLGENIEAvatar.cxx:87, 120` (`transformToLocalEnergyFrame`) and
  `:455` (functor built with `localE = true`);
- `"never"` cannot be selected: `NucleusGenINCL.cxx:538-540, 553-555` map it to
  `FirstCollisionLocalEnergy`;
- the XML `Default` set (`config/NucleusGenINCL.xml:48-55`) carries no
  `local-energy-*` params (the header `:28,32` claims `always`), so the effective
  value is the code fallback `first-collision`;
- the QE avatar increments the accepted-collision counter
  (`G4INCLGENIEAvatar.cxx:448`), so under `first-collision` the cascade's own NN
  collisions never see local energy in a QE event.

Goal: one switch that turns the local energy on/off at the vertex *and* in the
cascade, selectable from tune config, so "with vs without local energy" can be
generated and compared without code edits.

## Semantics (decided)

| `local-energy-BB` | vertex (struck nucleon → xsec, lepton kinematics, `isRPValid`, resampling floor, GENIE avatar) | cascade (INCL semantics, unchanged) |
|---|---|---|
| `always` | on | every NN collision |
| `first-collision` (default) | on — the vertex *is* the first collision | none (the QE avatar consumed the flag; kept as today) |
| `never` | off: struck nucleon = INCL's own `(p_ball, E_ball − V₀)`; the resampling still applies the ground-state floor `T > T_loc(r)` (changed 2026-09-04: the floor is a ground-state constraint, not the energy correction) | none |

`local-energy-pi` keeps its INCL meaning (πN collisions, Δ decays) and is not
consulted by the vertex. The resampling floor `T > T_loc(r)` (INCL's r–p
constraint: a nucleon at radius r needs the momentum whose reflection radius
reaches r) is applied in every mode; `never` only switches off the local-energy
transform of the accepted momentum (`vertexLocE() = 0`). With the binding plan in place, the vertex nucleon is
`(p_i, E_i)` with `E_loc = E_ball − vertexLocE`, `p_i = √(E_loc² − m²) p̂`,
`E_i = E_loc − V₀`, where `vertexLocE` is `T_loc(r)` (on) or 0 (off).

## Edits (all under `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator`, branch off `feature/for_Anna`)

**E1 `config/NucleusGenINCL.xml`** — the `Default` set already carried
`local-energy-BB/pi = first-collision` (an earlier read of this file was wrong);
done: header documentation fixed, complete `NoLocalEnergy` param_set added
(GENIE param_sets do not inherit from `Default`, and a `--` inside an XML comment
silently breaks the whole file — every param then reads back empty).

**E2 `src/Physics/NuclearState/NucleusGenINCL.cxx` `LoadConfig` (`:526-556`)** —
map `"never"` → `G4INCL::NeverLocalEnergy` for both params. `:140` (MEC cluster
local-frame momentum): gate the subtraction on the vertex flag.

**E3 `src/Physics/NuclearState/INCLNucleus.{h,cxx}`** — in `configure`
(`:161-205`) keep `bool useVertexLocE_ = (localEnergyTypeBB_ != G4INCL::NeverLocalEnergy)`
next to the existing `setLocalEnergyBBType` call (`:172`); public getter
`useVertexLocalEnergy()`. One helper
`double vertexLocE() const { return useVertexLocE_ ? KinematicsUtils::getLocalEnergy(nucleus_, hitNucleon_) : 0.; }`
used by:
- the getters (`:315-336`), rewritten per the binding plan as one const
  computation of `(p_i, E_i)`;
- `isRPValid` (`:476-487`): `MaxMomAtR = √((E_F − vertexLocE())² − m²)` → p_F when off;
- `ResamplingHitNucleon` (`:514-536`): threshold `getLocalEnergy(resampled state)`
  in every mode (evaluated inside the loop on the resampled state, which also
  removes the NaN side effect described in the review).
Delete the commented `setLocalEnergy*Type(NeverLocalEnergy)` lines (`:182-183`).

**E4 `src/Physics/HadronTransport/G4INCLGENIEAvatar.{h,cxx}`** — read
`INCLNucleus::Instance()->useVertexLocalEnergy()` into a member in both
constructors (`.h:24-25`; HadronTransport already includes `INCLNucleus.h`), then
- `preInteraction` non-hybrid: line 84 (with the binding plan's E4)
  `oldTotalEnergy = lepton_initial_energy + E1 − V1 − (flag ? getLocalEnergy(theNucleus, particle1) : 0)`;
  line 87 `transformToLocalEnergyFrame` only if the flag; same for the cluster
  loop at `:120`;
- `enforceEnergyConservation` (`:455`): pass the flag as the functor's `localE`
  instead of the hard-coded `true`;
- `:448` (`incrementAcceptedCollisions`) unchanged — the QE avatar stays the first
  collision; hybrid path (`postInteractionHybridModel`, INCL26_07a) untouched.

**E5** — binding-plan items unchanged: record rewrite skip for
`kIStNucleonTarget` (`G4INCLGENIECascadeAction.cxx:103-110`), `fEb`
initialisation, `RemovalEnergy = m − E_i`. With either option the functor then
finds α = 1 (no lepton/proton rescaling).

**E6 Build** — `make clean && make` in `Physics/NuclearState` and
`Physics/HadronTransport` (header changes); `make` in
`Physics/QuasiElastic/EventGen`.

**E7 Splines** — `INCLQELXSec` (`Physics/QuasiElastic/XSection/INCLQELXSec.cxx:153-177`)
integrates through the same getters, so each option value needs its own spline
(≈ 2.2 h each for C12 EMQE locally, cf. the 07-31 job). Shapes (V3) can use the
existing spline. The spline/event sampling mismatch (`BothRPResamping` fresh
nucleus per throw vs `fixRadius` ball) is untouched by this plan.

**E8 Tune overlay** — under `genie-agent/tunes/GEM26_44b/` add a tune-local
`NucleusGenINCL.xml` copy carrying `NoLocalEnergy`, and a sub-tune whose
`QELEventGeneratorINCL.xml` `EM-I-Default` `NuclearModel` and
`UnifiedQELPXSec.xml` `IntegralNucleusGen` both point at
`NucleusGenINCL/NoLocalEnergy` (spline and events must agree).

## Validation

Figure: [`results/prd-analyzer-v1.0/struck_pr_c12_all_t05_locE.png`](../results/prd-analyzer-v1.0/struck_pr_c12_all_t05_locE.png)
— struck-nucleon (r, |p|) for LFG (`GEM26_11a`, campaign), the old INCL record
(`GEM26_44b` 500k, ball with the rising floor), and the new branch's record with
local energy on (LFG-like, corr −0.67) and `never` (floor kept: the same
truncated ball as the old record, corr +0.45, but now the nucleon the kinematics
used); 20k events each for the new runs (`make_struck_pr.py --csv …`).

- **V1 probe** (`results/template/probe_incl_hitnuc.cxx`, both settings):
  `never` → `p_i = p_ball` exactly, `E_i = E_ball − 45.00`, `isRPValid` bound = p_F,
  no floor; default → the binding-plan numbers (`p_i² = p_ball² − p_min(r)²`).
- **V2** 2-event smoke per setting with `QELEvent` NOTICE: `HitNucP4().M()`
  off-shell by 45 MeV in both; `pn:` = p_ball vs p_red.
- **V3** 50k local EMQE per setting on the existing spline → `dump_hitnuc` + local
  ladder cache: record corr(p, r) 0 (`never`) / −0.65 (default); stage 2 = stage 3
  in E; `|p_p′ − q| = p_rec` exactly (no rescaling); record `Q2 == Q2s`.
- **V4** splines + 500k per setting → `analysis/dutta-qe --local`, the v1.0 INCL
  note ladders, and an inclusive-style ω comparison.

## Expected observables (protons, from today's 500k sample; binding E = … − V₀ in both columns)

| quantity | default (`first-collision`/`always`) | `never` |
|---|---|---|
| momentum used everywhere | p_red: ⟨p⟩ 150 MeV/c, p < 100: 24 % | ball with floor: ⟨p⟩ 225, p < 100: 1 %, cut 270 |
| corr(p, r) | −0.65 (LFG-like) | +0.46 (INCL-like) |
| E − m used by the lepton kinematics | −31 MeV | −17.5 MeV |
| E_m (pre-FSI) | V₀ − T_red: mean 31.0 | V₀ − T_ball: mean 17.5 |
| Dutta windows [10,25) / [30,50) | 27 % / 58 % | 58 % / 10 % |
| Moniz C12 Fermi-gas reference | ⟨p⟩ 166 (k_F 221) | |

(A pure p_F ball without the floor — the 2026-09-03 first version of `never`,
replaced on 2026-09-04 — gave ⟨p⟩ 203, corr 0, E_m mean 22, windows ≈ 50 % / 24 %.)

## Notes
- The option is read once per job from the `NucleusGenINCL` param_set the tune
  binds and lives in the INCL `Config` singleton shared with the cascade.
- `results/template/make_incl_groundstate_record.py` assumes "record = truncated
  ball"; for the default the record becomes p_red, for `never` a pure ball — swap
  the model lines accordingly when validating.

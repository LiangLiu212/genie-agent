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
corr 0.00). Splines (E7) regenerated 2026-09-04 with `gmkspl -n 30 -e 3.0` (EMQE, e⁻ C12):
`genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-043319-d42.xml`
(label `locE-on`, 5157 s) and `…-043319-f8a.xml` (label `locE-never`, 5350 s,
run with the tracked override `genie-agent/tunes-locE-never/` first in
`GXMLPATH`). Against the 07-31 spline at 2.445 GeV: e-p ×0.859 (on) / ×0.844
(never), e-n ×0.860 / ×0.816 — the 45 MeV binding now in the kinematics
(ε_B in q̃) plus the changed momenta; figure
`results/prd-analyzer-v1.0/spline_gem26_44b_locE.png`
(`make_spline_44b_locE.py`). The tune overlay (E8) is still open — the `never`
setting is selected by the override directory, and runs must carry the matching
spline and `--label`.
Companion to [`incl-local-frame-binding-plan.md`](incl-local-frame-binding-plan.md)
(the E = E_red − V₀ convention) and grounded in
[`incl-ground-state-review.md`](incl-ground-state-review.md).

## Convention revised (2026-09-04): INCL's own scheme

Committed as `6bd7803d6` on `feature/incl-vertex-local-energy` (pushed to `LiangLiu212/Generator`, 2026-09-04).

After looking at the E_m spectra of the 200k samples (the "on" setting moved the
pre-FSI E_m to `V₀ − T_red`, edge at 45 MeV, and the post-FSI peak from 15–20
to 50–55 MeV), the user re-specified the vertex to follow INCL's
`InteractionAvatar` exactly:

- **The scattering is computed in the local frame.** The nucleon handed to the
  cross section and the lepton/proton kinematics (`HitNucP4`, from
  `INCLNucleus::getHitNucleonP4`) is the on-shell local-frame nucleon
  `(p_red, E_ball − T_loc(r))` when local energy is on, and the on-shell ball
  nucleon `(p_ball, E_ball)` under `never`. No potential is subtracted there.
- **Energy conservation uses `E − V`, with no local-energy term.**
  `G4INCLGENIEAvatar::preInteraction` sets
  `oldTotalEnergy = E_lep + E_ball − V₀` (the `− locE1` term of the first
  implementation is removed) and INCL's `ViolationLeptonEMomentumFunctor`
  rescales lepton and proton to it, as INCL does for its own collisions. The
  lepton therefore moves by the difference `V₀ − T_loc(r)` (on) or `V₀`
  (`never`) between the scattering energy and the conserved one (per cent
  level in Q²).
- **The record holds the global nucleon** `(p_ball, E_ball − V₀)`
  (`INCLNucleus::getHitNucleonRecordP4`, written through the new virtual
  `NucleusGenI::SetRecordHitNucleon`, default = the interaction's `HitNucP4`),
  so `RemovalEnergy = V₀ − T_ball ∈ [S, V₀]` and stage 2 = stage 3 in E_m; the
  post-cascade on-shell rewrite still skips the initial-state nucleon.

Consequences: E_m = `V₀ − T_ball` in both settings (the old chain's spectrum,
post-FSI peak back at 15–20 MeV on the data); the record's (r, p) is the
INCL ball with the floor (corr ≈ +0.47) in both settings; the local-energy
choice shows in the scattering only — stage-3 `|p_p′ − q| ≈ p_red` (LFG-like,
corr ≈ −0.67) with local energy on, `≈ p_ball` under `never` — and in the
cross section (the spline integrand sees the local-frame nucleon, on-shell,
i.e. the 07-31 convention again for "on"). The formulas in *Semantics* and
*Expected observables* below describe the first implementation
(`E_i = E_loc − V₀`) and are superseded by this section.

Validation (2026-09-04, 20k e⁻ C12 EMQE events per setting on the 07-31
spline, `genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-153523-28c`
= on, `…-153524-64b` = never; probe `probe_incl_hitnuc` 20k nuclei per
param_set; checks `check_locframe_run.py`):

| quantity (QEL, hit proton) | local energy on | never |
|---|---|---|
| record ⟨p⟩, max, corr(p, r) | 225.6 MeV/c, 270.34, +0.466 | 225.5, 270.33, +0.466 |
| `RemovalEnergy` = m − E_n = V₀ − T_ball | to 0.009 MeV; mean 17.46, range [6.83, 44.67] | same; mean 17.50 |
| stage 3 − stage 2 E_m | 0.0001 MeV max | 0.0000 |
| Q²(record) − Q²s (lepton rescaled by INCL) | −1.27 % mean, [−1.98, −0.28] (∝ V₀ − T_loc(r)) | −1.81 % mean, [−1.99, −1.70] (∝ V₀) |
| \|p_p′ − q\| / p_red(r, p_ball) | 1.02 mean (p10–p90 0.88–1.13) | — |
| \|p_p′ − q\| / p_ball | 0.67 mean, corr(·, r) = −0.66 | 1.007 mean, corr = +0.43 |
| scattering nucleon (probe): ⟨p_i⟩, corr(p_i, r) | 148.3 MeV/c, −0.668 (on-shell to 2e-4 MeV) | 225.8, +0.468 |

Splines regenerated under this convention (2026-09-04, `gmkspl -n 30 -e 3.0`,
EMQE): jobs `gmkspl-eminus_C12_20260904-153639-9f4` (label `locframe-on`) and
`…-153640-9bc` (`locframe-never`, override directory first in `GXMLPATH`).

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
| `never` | off: scattering nucleon = INCL's own on-shell `(p_ball, E_ball)` (record `(p_ball, E_ball − V₀)` as in every mode); the resampling still applies the ground-state floor `T > T_loc(r)` (changed 2026-09-04: the floor is a ground-state constraint, not the energy correction) | none |

`local-energy-pi` keeps its INCL meaning (πN collisions, Δ decays) and is not
consulted by the vertex. The resampling floor `T > T_loc(r)` (INCL's r–p
constraint: a nucleon at radius r needs the momentum whose reflection radius
reaches r) is applied in every mode; `never` only switches off the local-energy
transform of the accepted momentum (`vertexLocE() = 0`). First implementation (superseded, see *Convention revised*): the vertex
nucleon was `(p_i, E_i)` with `E_loc = E_ball − vertexLocE`,
`p_i = √(E_loc² − m²) p̂`, `E_i = E_loc − V₀`. Since 2026-09-04 the scattering
nucleon is the on-shell `(p_i, E_loc)` and the record nucleon
`(p_ball, E_ball − V₀)`; the balance is `E − V` without a local-energy term.

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

## Samples (2026-09-04): 200k events per setting

`genie-runs/GEM26_44b_05_000-2026-09-04/`, e⁻ C12 2.445 GeV EMQE, 4 × 50k chunks
each, distinct seeds, the matching new spline, `--label`:
- `locE-on` (d42 spline): `eminus_C12_20260904-135725-84c`, `-135727-8b5`,
  `-135727-a11`, `-135728-d90` — 200,000 gst entries.
- `locE-never` (f8a spline, override dir first in `GXMLPATH`):
  `-135728-089`, `-135728-a87`, `-143137-3cd`, `-143137-546` — 200,000 gst
  entries (`-135728-69b` and `-135729-d99` aborted, see below; their partial
  outputs are unreadable and their logs carry rc −6).
The first two `never` chunks and all `on` chunks were generated with the
rejection-loop resampling, the last two with the direct draw — statistically
the same distribution.

**Superseded (convention revised, same day)** — the samples above and the
d42/f8a splines use the first convention. Under the INCL scheme:
- splines (`gmkspl -n 30 -e 3.0`, EMQE): `eminus_C12_20260904-153639-9f4.xml`
  (label `locframe-on`, 5452 s) and `…-153640-9bc.xml` (`locframe-never`,
  5768 s, override dir first). At 2.445 GeV vs the 07-31 spline: e-p ×1.019 /
  e-n ×0.964 (on — the same integrand convention as 07-31, the strict floor and
  gmkspl's few-% integration wobble) and ×0.972 / ×0.963 (never);
  `results/prd-analyzer-v1.0/spline_gem26_44b_locframe.png`.
- `locframe-on-200k` (9f4 spline): `eminus_C12_20260904-170929-740`,
  `-170930-58d`, `-170930-0b5`, `-170931-b2b` — 4 × 50k, seeds 20260911–14,
  ~1050 s each, rc 0.
- `locframe-never-200k` (9bc spline, override dir first): `-171310-ad8`,
  `-171310-15a`, `-171310-6f2`, `-171310-ff5` — seeds 20260921–24.
- registered in the ladder scripts as `GEM26_44b_05_000_lfon` / `_lfnever`;
  stage-3 momentum csvs via `results/template/make_stage3_csv.py`.

## Resampling exhaustion (found and fixed 2026-09-04)

Producing 200k events per setting (4 × 50k chunks), two `never` chunks aborted
(`double free or corruption` at ROOT teardown). Reproduced deterministically
(seed 914797872, event 11209) with unbuffered output: `FATAL
INCLNucleus::ResamplingHitNucleon: Resampling the momentum of struck nucleon
more than 10000 times!` → `exit(1)` with the output TFile open. Cause: with the
floor evaluated strictly on the resampled state, a nucleon sampled within
~0.05 fm of R_max has an acceptance `1 − (p_min/p_F)³ ≲ 10⁻⁴` per throw, so the
10,000-throw loop exhausts at ≈ 10⁻⁵ per event (2 in 157k); the `on` setting
is equally exposed (0 in 200k, consistent with chance). Fix (fork commit after
`cbffacc10`): `ResamplingHitNucleon` draws `|p|³` uniformly on `[p_min(r)³, p_F³]`
with an isotropic direction — the exact distribution the loop accepted, with no
rejection and no `exit`. Chunks generated before the fix are statistically
identical and were kept; the two lost chunks were regenerated.

## Notes
- The option is read once per job from the `NucleusGenINCL` param_set the tune
  binds and lives in the INCL `Config` singleton shared with the cascade.
- `results/template/make_incl_groundstate_record.py` assumes "record = truncated
  ball"; for the default the record becomes p_red, for `never` a pure ball — swap
  the model lines accordingly when validating.

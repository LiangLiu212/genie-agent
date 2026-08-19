# RES-EM Q2toQD2 assert: root cause, fix, and 22a/22b resubmission (2026-07-16)

Executed version of the approved plan (investigation by two Explore subagents over
the GENIE source + tune wiring, then hand-verified line by line). Fixes the crash
that killed the GEM26_22a/22b halves of the Fe56 full-EM campaign
(`fe56-em-t05-fullem-splines.md`).

## Symptom

`gevgen: KineUtils.cxx:1096: genie::utils::kinematics::Q2toQD2(double):
Assertion 'Q2>0' failed.` — SIGABRT, stochastic (O(0.5k-66k) events in),
e- at 2.445 GeV, genlist EM/EMRES, tunes GEM26_22a/22b/33a `_05_000`, C12 and
Fe56 alike. Grid campaign 2026-07-16: 22a 0/100 procs survived, 22b 1/100.

## Root cause (line-verified)

- The only active callers of `Q2toQD2` are `RESKinematicsGenerator.cxx:152-153`
  — the **RES-EM thread**. (QEL/DMEL callers are commented out in this version;
  no QEL-EM configuration can reach the transform. The 07-09 local crash was
  genlist EMRES — no QEL generator loaded.)
- `KPhaseSpace::Q2Lim_W` → `electromagnetic::InelQ2Lim_W` (`KineUtils.cxx:598-634`)
  floors `Q2.min` to `EM-MinQ2Limit` (line 630; read once from CommonParam
  `[Lepton]`, default 0.02; the t05 knob sets **1.18 GeV²** in
  `<tune>_05_000/CommonParam.xml:289` — knob scan: t04 0.54, t05 1.18, t06 1.70,
  t07 1.73, t08 3.15) and **voids the range to (-1,-1)** when the kinematic
  `Q2.max < Q2.min` (line 631).
- The importance-sampling branch (`RESKinematicsGenerator.cxx:143-153`) had **no
  window-validity guard** — unlike its `fGenerateUniformly` sibling (:133) and
  the W guard (:82-88) — so `Q2toQD2(-1 - kASmallNum)` → assert.
- Trigger: nucleons drawn by `FermiMover` from the **Benhar 2D
  `genie::SpectralFunc`** high removal-energy/momentum tail lower the
  hit-nucleon-rest-frame probe energy enough that the RES `Q2.max` at `W.min`
  drops below 1.18. Tune split is exactly the ground-state model:
  22a/22b (crash) map C12+Fe56 → `SpectralFunc/Default`
  (`ModelConfiguration.xml:39,43`); 11a/GEM21 (immune) use `LocalFGM`
  (their SpectralFunc1d lines are inside a comment block). 22a's QEL-EM is
  RosenbluthPXSec — identical to 11a — killing the initial QEL theory.
- Guard-event rate: ~0.4% of events (C12 EMRES), ~0.07% (Fe56 full EM).

## Fix

One-line guard (user-applied, message body by user preference) after
`Range1D_t Q2 = kps.Q2Lim_W();` in the importance-sampling branch:

```cpp
if(Q2.max<=0. || Q2.min>=Q2.max){
  LOG("RESKinematics", pNOTICE)
     << "void EM Q2 window at W=" << W.min
     << "  Q2.min=" << Q2.min << "  Q2.max=" << Q2.max;
  continue;
}
```

A voided window (fixed nucleon → void every iteration) exits via the existing
`kRjMaxIterations = 1000` handler: pWARN "Could not select a valid (W,Q^2)
pair" + `EVGThreadException` fast-forward → event regenerated. The pNOTICE is
invisible at default verbosity (Messenger.xml sets RESKinematics to WARN) —
one WARN line per occurrence, no spam. Note the printed values are always
`-1/-1` (the range is voided inside `InelQ2Lim_W` before returning; instrument
KineUtils.cxx:631 to see the real sub-floor `Q2.max`).

- Commit: **`3d97c78aa`** on `feature/for_Anna` in
  `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator` (only file;
  pre-existing dirty `NewQELXSec.xml` / `INCLCascadeIntranuke.cxx` untouched).
- Rebuild: package-level `gmake` in `src/Physics/Resonance/EventGen` under the
  parent-stripped `setup_env.sh` shell; `libGPhResEG-999.999.999.so` relinked
  (13:48:19). No env re-snapshot needed.

## Verification (all local, runners with fixed seeds)

| Check | Config | Pre-patch | Post-patch |
|---|---|---|---|
| Deterministic repro | 22a_05, C12, EMRES, n=2000, seed 1843326923 | rc -6, assert at event **1568** | rc 0, 2000/2000, **8 guarded events** (one exactly at 1568) |
| Invariance | 22a_00 (same SF+RES path, floor 0.02), same seed | reference gst | gst identical on **110/110 physics branches** |
| Fe56 smoke | 22a_05, Fe56, genlist EM, n=20000, PNFS spline | (campaign died on grid) | rc 0, 74 s, 14 guarded events |

Invariance caveat: gst branch `E_exci` differs run-to-run even with identical
binary+seed (constant ~1e-317 denormal per run) — pre-existing uninitialized
variable in this fork's custom branch (INCL-only fill, hA2018 runs never set
it). Unrelated to the patch; worth fixing separately.

## Deployment + resubmission

- Tarball `tarball_1d672b16595e.tar` (507 MB; recipe mirrors the 07-14
  genie_inclxx tarball: `Generator` sans src/.git + `inclxx_genie/install` +
  `setup_env.sh`), published under **new label `genie_inclxx_q2guard`**
  (old `genie_inclxx` → `0570c927…` left intact — it generated the completed
  11a/GEM21 samples).
- Resubmission: `.claude/plans/submit_fe56_em_gevgen_q2guard.sh` — 22a+22b only,
  `--tarball-label genie_inclxx_q2guard`, otherwise the original campaign
  parameters (eminus Fe56, genlist EM, -e 2.445, -n 100000, -N 100, 24h,
  PNFS-direct splines from the 07-15 gmkspl jobs).
- Submitted 2026-07-16 14:18 (dry-run argv checked: `-R` = the q2guard CVMFS dir):

| Tune | jobid | cluster |
|---|---|---|
| GEM26_22a_05_000 | gevgen_grid-eminus_Fe56_20260716-141800-db180e | 85476495@jobsub01 |
| GEM26_22b_05_000 | gevgen_grid-eminus_Fe56_20260716-141807-aabcd3 | 85476496@jobsub01 |

  200 processes confirmed idle in `jobsub_q` at 14:18.

## Follow-ups (not done)

- Report the missing guard upstream to GENIE-MC (bug present in stock GENIE).
- Fix the uninitialized `E_exci` gst branch in this fork.
- GEM26_33a/33b t05 campaigns inherit the fix automatically when run with the
  q2guard tarball.

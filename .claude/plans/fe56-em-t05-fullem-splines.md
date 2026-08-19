# Fe56 t05 full-EM spline batch — one gmkspl job per tune (executed 2026-07-15)

Tracked copy of the approved plan; precursor to the Fe56 full-EM event
campaign (4 × 10M at 2.445 GeV). Supersedes per-channel generation: per user
direction, **one gmkspl grid job per tune with genlist `EM`** (QEL+RES+DIS+MEC
in a single XML; 55 splines = 2 QE + 1 MEC + 36 RES + 16 DIS). No gspladd.

## Batch (submitted 2026-07-15 18:14 UTC from the gpvm)

Common: `run_gmkspl_grid.py --probes eminus --targets Fe56 --genlist EM
-e 10 -n 30 -N 1 --tarball-label genie_inclxx` (tarball `0570c927…`, 07-14;
overlays: `gem26_emq2lim` = `f433c6db…` with the Fe56 SF fix, `gem21_emq2lim`).

| Tune | Overlay | Lifetime | jobid | cluster |
|---|---|---|---|---|
| GEM26_11a_05_000 | gem26_emq2lim | 24h | gmkspl_grid-eminus_Fe56_20260715-181408-75876c | 29162731.0@jobsub05 |
| GEM26_22a_05_000 | gem26_emq2lim | 24h | gmkspl_grid-eminus_Fe56_20260715-181410-1ab904 | 70897171.0@jobsub03 |
| GEM26_22b_05_000 | gem26_emq2lim | **48h** | gmkspl_grid-eminus_Fe56_20260715-181412-cc4a07 | 92478670.0@jobsub02 |
| GEM21_11a_05_000 | gem21_emq2lim | 24h | gmkspl_grid-eminus_Fe56_20260715-181414-ebd2f6 | 92478671.0@jobsub02 |

- 22b carries the SF-folded UnifiedQEL QE (3.5–8 h alone on grid workers,
  measured from the 07-14 batch PNFS mtimes; MEC ~10 min, RES ~35–55 min,
  DIS ~1 h) → the combined job straddles the 8 h default, hence 48h.
- GEM21_11a (LFG+SuSAv2) runs under **genie_inclxx** — verified 2026-07-15:
  stock G21_11a family + identical `HybridXSecAlgorithm.xml::SuSAv2-QEL`
  param set; `HybridXSecAlgorithm.cxx` + all SuSAv2 tensors byte-identical to
  genie_dev; `SuSAv2QELPXSec.cxx` differs only by a relocated equivalent
  phase-space guard. **EM QE tensor is C12-only in both installs** → Fe56 EM
  SuSAv2 (QE and MEC) is C12-scaled (open_questions.md corrected from "Ar40").
- Model matrix (tunes/*/ModelConfiguration.xml): RES-EM
  `BergerSehgalRESPXSec2014/EM-NoPauliBlock`, DIS-EM
  `KNOTunedQPMDISPXSec/Default`, MEC-EM `SuSAv2MECPXSec/Default` identical
  across all four; QEL-EM differs (Rosenbluth ×2 / UnifiedQELPXSec-Dipole /
  Hybrid SuSAv2-QEL). genlist `EM` = exactly those 4 generators. All hA2018
  FSI (GEM26 a/b letters = QE model, NOT FSI; only GEM26_44b is INCL++).

## After the drain

1. Pull the 4 XMLs (direct NFS cp; `job.py pull` lacks ifdh on this host) →
   `genie-agent/splines/fe56-em/<TUNE>_EM.xml`.
2. Verify: 55 splines each, tgt 1000260560, channel sums σ(2.445) vs t05
   references (QE 22b 1.85e-4, 22a/11a 2.75e-4, MEC 6.6e-5, RES 5.1e-4,
   DIS 6.3e-4; physics zeros: EMRES res 3/4/5/17 proton). Identity web:
   MEC/RES/DIS identical across tunes; 22b ≡ 07-14 per-channel set; 11a/22a
   QE ≡ 07-11 files; GEM21 QE ≡ June genie_dev susav2 Fe56 rows. Mismatch →
   stop.
3. Republish `fe56-em/` under label `fe56_em_splines` (resolve path via
   catalog, never hardcode).
4. Next phase (separate approval): 4 gevgen submissions, genlist `EM`,
   `-n 100000 -N 100`, `-e 2.445`, with these `<TUNE>_EM.xml` CVMFS splines.

**Persistent mirror (2026-07-17):** all four spline XMLs copied from scratch to
`/pnfs/dune/persistent/users/liangliu/...` with the directory structure
preserved (same path, `scratch` → `persistent`), sha256-verified
(11a c0175baeea97…, 22a ef920f12d65b…, 22b f7302a0c80cb…, GEM21 5bc053d0cb66…).
The scratch originals expire ~30 d after 2026-07-15; the gridlog
`pnfs_output_dir` paths map to the mirror by the same substitution.

## Step 4 executed 2026-07-16 (PNFS-direct deviation)

All four spline jobs drained `done` 1/1. Per user direction the splines were
**not** pulled/republished (steps 1+3 above superseded): each gevgen job takes
its spline straight off PNFS via `--cross-sections /pnfs/...` (jobsub `-f` by
reference). Step 2 verification ran in place on /pnfs
(scratch script, 2026-07-16): 55 splines each, tgt 1000260560, channel sums at
2.445 GeV within 1% of the references above, MEC/RES/DIS bit-identical across
tunes (spread 0), GEM21 SuSAv2 QE = 2.247e-4 (report-only). Cross-file
byte-identity checks vs the 07-11/07-14 sets were skipped.

Submission script: `.claude/plans/submit_fe56_em_gevgen.sh` (dry default,
`--go`). Common: `run_gevgen_grid.py --probe eminus --target Fe56 --genlist EM
-e 2.445 -n 100000 -N 100 --tarball-label genie_inclxx --expected-lifetime 24h`
(10M events/tune; spline = the tune's 07-15 gmkspl output `0000/*.xml`).

| Tune | Overlay | jobid | cluster |
|---|---|---|---|
| GEM26_11a_05_000 | gem26_emq2lim | gevgen_grid-eminus_Fe56_20260716-113802-04ca08 | 70906413@jobsub03 |
| GEM26_22a_05_000 | gem26_emq2lim | gevgen_grid-eminus_Fe56_20260716-113807-f03225 | 85476169@jobsub01 |
| GEM26_22b_05_000 | gem26_emq2lim | gevgen_grid-eminus_Fe56_20260716-113812-4a8586 | 29168915@jobsub05 |
| GEM21_11a_05_000 | gem21_emq2lim | gevgen_grid-eminus_Fe56_20260716-113817-eab560 | 85476175@jobsub01 |

All 400 processes confirmed idle in `jobsub_q` at 11:38. Scale expectation from
the 07-14 batch (10k EMQE = 11M ghep + 7.8M gst): ~a few hundred MB/process,
O(100-200 GB) scratch total. Worker seed = CLUSTER + PROCESS.

### Outcome (checked 12:12-12:30, queue fully drained ~30 min after submit)

| Tune | Result | PNFS triplets |
|---|---|---|
| GEM26_11a_05_000 | **done** | 100/100 (88M ghep + 97M gst per proc) |
| GEM26_22a_05_000 | **failed** | 0/100 |
| GEM26_22b_05_000 | **partial** | 1/100 (proc 63 survived) |
| GEM21_11a_05_000 | **done** | 100/100 |

22a (100/100 procs) and 22b (99/100) all SIGABRT'd (exit 134) on the same
GENIE assertion, stochastically mid-run:
`KineUtils.cxx:1096: genie::utils::kinematics::Q2toQD2(double): Assertion
'Q2>0' failed.` 22a died at events ~0.5k-47k; 22b later (~5k-66k) and proc 63
luckily cleared all 100k.

**Root cause (corrected 2026-07-16 after source trace; the first-pass "UnifiedQEL
QEL kinematics" attribution was wrong):** the crash is in the **RES-EM thread**,
and the crash/immune split across tunes tracks the **nuclear ground-state model**,
not the QE model (22a's QEL-EM is RosenbluthPXSec, same as 11a; the 07-09 local
crash used genlist EMRES with no QEL generator loaded). Chain: `FermiMover`
samples the struck nucleon from the tune's nuclear model — 22a/22b map C12+Fe56
to the Benhar 2D `genie::SpectralFunc` (ModelConfiguration.xml:39,43) while
11a/GEM21 fall back to LocalFGM; a 2D-SF draw from the high removal-energy/
momentum tail can push the kinematic RES `Q2.max` at `W.min` below the
`EM-MinQ2Limit = 1.18` floor (t05, `_05_000/CommonParam.xml:289`), whereupon
`InelQ2Lim_W` (KineUtils.cxx:630-631) voids the window to `(-1,-1)`; the
importance-sampling branch of `RESKinematicsGenerator.cxx:143-153` had no
validity guard (its fGenerateUniformly sibling at :133 does) and passed -1
into `Q2toQD2` → assert. **Pre-existing, not grid-specific**: local runlog has
GEM26_22a_05_000 and GEM26_33a_05_000 C12 EMRES 200k rc=-6, while the same
tunes' _00_000 EMRES runs (default floor 0.02) completed — same SF mapping, no
crash. The t05 *splines* are unaffected (spline/ComputeMaxXSec paths are
guarded / scan in log-Q2).

**Fix (applied 2026-07-16):** one-line guard
`if(Q2.max<=0. || Q2.min>=Q2.max){ LOG(...); continue; }` after `Q2Lim_W()` in
the importance-sampling branch (mirrors the uniform branch); a voided window
now exits via the existing kRjMaxIterations=1000 handler (EVGThreadException
fast-forward, event regenerated). Committed in the GENIE_INCLXX Generator
checkout as `3d97c78aa` (branch feature/for_Anna); RES package rebuilt in
place. Verified: (i) deterministic repro — 22a_05 C12 EMRES seed 1843326923
died at event 1568 pre-patch, completes 2000/2000 post-patch with 8 guarded
events; (ii) invariance — 22a_00 same-seed gst identical pre/post on all 110
physics branches (the 111th, `E_exci`, is run-to-run nondeterministic garbage
from a pre-existing uninitialized variable in this fork, unrelated); (iii)
Fe56 smoke — 22a_05 Fe56 genlist EM 20k events rc 0, 14 guarded events, 74 s.
Details: `.claude/plans/fix-res-em-q2window-assert.md`. Patched install
published as tarball label `genie_inclxx_q2guard`
(`/cvmfs/fifeuser2.../e12554237f66…`); 22a/22b resubmitted 2026-07-16 14:18
via `submit_fe56_em_gevgen_q2guard.sh`:
GEM26_22a_05_000 = gevgen_grid-eminus_Fe56_20260716-141800-db180e
(cluster 85476495@jobsub01), GEM26_22b_05_000 =
gevgen_grid-eminus_Fe56_20260716-141807-aabcd3 (85476496@jobsub01);
200 processes confirmed idle at 14:18.

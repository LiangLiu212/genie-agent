# rc-v380 spline set (samples A–G) — campaign log

Approved plan: `~/.claude/plans/plan-a-multi-tune-gmkspl-abundant-snowglobe.md` (2026-09-03).
Template campaign: `g18_02a-v362-5tev-spline-set.md` (v3.6.2, 5 TeV) / `incl26_07a-xsec-spline-set.md`.

## Fixed inputs

- GENIE **rc-v380** (pre-release v3.8.0), `GENIE-MC/Generator` branch `rc-v380`, commit
  `29238ed97a99aff90c32390951b607185e59f1c5` ("Add temporary AR23_20n_00_000 tune for testing
  hN2025 and BY2021", 2026-09-02), cloned `--depth 1` into
  `/exp/dune/app/users/liangliu/GENIE/GENIE_RC/Generator`. Built 2026-09-03 **Pythia8-only**
  (`--disable-pythia6 --enable-pythia8`, spack `pythia8@8.317`); recipe `$GENIEBASE/build_genie.sh`.
- Installation key `genie_rc` (genie_env.json; `active_installation` flipped to it 2026-09-03 for
  this campaign — local runs without `--installation` now default to rc-v380).
- Grid tarball label `genie_rc` (428 MB, published 2026-09-03 18:00 UTC) →
  `/cvmfs/fifeuser1.opensciencegrid.org/sw/dune/0086a59e4ab68d9a6d5119322dab7a594e4696f7f1e6a84538cd6a8446febfeb`
  (RCDS purge ~30 d; `tarball.py verify --label genie_rc`).
- Worker templates `jobsub-agent/adapters/genie/templates/{gmkspl,gevgen}_grid.sh` patched
  2026-09-03 to `spack load … pythia8@8.317` + `export PYTHIA8DATA` (libGPhHadnz NEEDS libpythia8).
- Channels = tune `Default` (18 generators, identical for G18_10a, G24_12a, AR23_20m, AR23_20n,
  AR25_20i) as 16 genlists (union verified == Default):
  `CCQE NCEL CCMEC NCMEC CCRES NCRES CCDIS NCDIS CCCOHPION NCCOHPION CCDFR NCDFR
   NuEElastic IMD LambdaCCQE Charm`.
- Probes: `numu`, `numubar` (one submission per probe). Knots `-n 100` (≤10 GeV), `-n 200` (Fe56, 50 GeV).
- gmkspl has no minimum energy; the requested 0.1 GeV floors are the physics thresholds.

## Required spline sets (assignment table, all rows run here)

| Sample | Tune | Target | Energy | `-e` | `-n` | Assigned to | Status |
|---|---|---|---|---|---|---|---|
| A | G18_10a_02_11b | Ar40 | 0.1–10 GeV | 10 | 100 | Person 1 | pending |
| B | AR23_20m_00_000 | Ar40 | 0.1–10 GeV | 10 | 100 | Person 1 | pending |
| C | AR23_20n_00_000 | Ar40 | 0.1–10 GeV | 10 | 100 | Person 1 | pending |
| D | G24_12a_00_000 | C12 | 0.1–5 GeV | 5 | 100 | Person 2 | pending |
| D | G24_12a_00_000 | Ar40 | 0.1–5 GeV | 5 | 100 | Person 2 | pending |
| E | AR25_20i_00_000 | C12 | 0.1–3 GeV | 3 | 100 | Person 3 | pending |
| E | AR25_20i_00_000 | Ar40 | 0.1–3 GeV | 3 | 100 | Person 3 | pending |
| F | GDM18_00a_00_000 | Ar40 | DM beam range | – | – | Person 4 | **deferred** (see below) |
| G | G18_10a_02_11b | Fe56 | 5–50 GeV | 50 | 200 | Person 4 | pending |

Submissions: 7 rows × 2 probes × 15 lists (IMD dropped, see deviations) + Fe56 2 × 16 = **242**.

### Sample F deferral
`gmkspl_dm`/`gevgen_dm` are not in the `genie_rc` build (needs `./configure --enable-boosted-dark-matter`).
Needed before F can run: DM mass, mediator mass/coupling, DM beam energy range. Then: rebuild
(`build_genie.sh` + the BDM flag), `tarball.py build` + `publish --label genie_rc --overwrite`,
re-snapshot `genie_rc`, add a `gmkspl_dm` row.

## Stage 0 — preconditions and gates (2026-09-03)

- [x] Worker templates patched (pythia8@8.317 + PYTHIA8DATA), `bash -n` clean.
- [x] `active_installation` → `genie_rc`.
- [x] `tarball.py verify --label genie_rc`: exists / ok (age 0d).
- [x] **Charm go/no-go** (numu C12, `-n 30 -e 5`, local `genie_rc`):
      G18_10a_02_11b `gmkspl-numu_C12_20260903-192646-281-9c1625` rc 0, 431.7 s, **9 splines**
      (6× AivazisCharmPXSecLO DIS-CC-CHARM n/p × s/v/3(s) + 3× KovalenkoQELCharmPXSec Λc+/Σc+/Σc++);
      AR23_20n_00_000 `gmkspl-numu_C12_20260903-193401-f01-76f0a1` rc 0, 401.4 s, 9 splines. **GO.**
- [x] `NuEElastic` resolves (1 spline `NuElectronPXSec/Default … NuEEL`) for both tunes.
- [x] `IMD` resolves but writes **0 splines at -e 5** for both tunes (rc 0):
      inverse muon decay threshold E ≥ (m_μ² − m_e²)/2m_e ≈ 10.9 GeV → empty for every row
      with `-e ≤ 10`. See deviations.

## Stage 1 — campaign scripts

- [x] `.claude/plans/submit_rc_v380_splines.sh` (wave; print mode = 242 commands: 15 lists × 2
      probes × 7 rows + 16 × 2 for Fe56; 80 × 43200 s, 162 × 14400 s; `--go`, `--sample`,
      `--lists`, `--probes`, `--dry-run`; resume guard on `.extra.{tune,target,probe,genlist}`,
      installation `genie_rc`; `--project rc_v380_splines`).
- [x] `.claude/plans/submit_rc_v380_pilot.sh` (`--smoke`, `--pilot`: thin filter wrapper over the wave script).
- [x] `.claude/plans/merge_rc_v380_splines.sh` (pull + stage + `gspladd -d` per (tune, target),
      coverage report, duplicate/nknots/tune/sha256 checks; products under
      `/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380/<TUNE>/`).

## Stage 2 — smoke (numu Ar40 CCQE, G18_10a_02_11b, -e 10 -n 100)

- [x] dry-run 19:45 UTC: argv verified (`-p 14 -t 1000180400 -T G18_10a_02_11b -L CCQE -e 10.0
      -n 100`, `--expected-lifetime 14400`, `-R …/0086a59e…` = genie_rc tarball,
      `(TARGET.Microarch>="x86_64-v3")`). Dry-run artifact record (status `pending`, ignored by
      the resume guard): `gmkspl_grid-numu_Ar40_20260903-194507-1139b8`.
- [x] submitted 19:45:29 UTC: `gmkspl_grid-numu_Ar40_20260903-194529-cc1282`,
      cluster `71837794.0@jobsub03.fnal.gov`, PNFS
      `…/rc_v380_splines/CC/genie_rc/G18_10a_02_11b/numu_Ar40_20260903-194529_spl/14_1000180400_G18_10a_02_11b`.
- [x] **Cancelled 21:25 UTC** after 100 min running with no output: the local timing probe
      showed G18_10a's Nieves(+RPA) CCQE on Ar40 costs **2187 s for 10 knots** (30 evaluations,
      ~95 s per above-threshold knot) vs 155 s for G24_12a → ~3 h at 100 knots on the pod,
      i.e. the 14400 s lifetime would have evicted it (restart-from-zero loop). Record status
      `cancelled` (resume guard resubmits CCQE with a long lifetime in the wave).
- [x] Replacement smoke (same gate, seconds of compute): numu Ar40 `NuEElastic`,
      `gmkspl_grid-numu_Ar40_20260903-212533-1c0a81`, cluster `30088520.0@jobsub05.fnal.gov`,
      submitted 21:25:33 UTC.
- [x] **Gate green 21:30 UTC**: done in 5.0 min wall (PNFS output 21:28:57, 3.4 min after
      submission); pulled XML 7160 B, 1 spline
      `genie::NuElectronPXSec/Default/nu:14;tgt:1000180400;proc:Weak[NC],NuEEL;`,
      `genie_tune=G18_10a_02_11b`, `nknots=100`. The Pythia8-linked `genie_rc` tarball runs on a
      worker with the patched templates.

### Local cost probes (this pod, numu Ar40, 10 knots = 30 evaluations; 2026-09-03)

| List (G18_10a_02_11b, -e 10) | wall | splines | note |
|---|---|---|---|
| CCQE | 2187 s | 1 | Nieves+RPA; ~95 s per above-threshold knot → ~3 h at 100 knots |
| Charm | 401 s | 9 | |
| CCCOHPION / NCCOHPION | 110 s / 98 s | 1 / 1 | |
| CCMEC / NCMEC | 58 s / 0.9 s | 1 / 3 | |
| NCEL / NuEElastic | 1.1 s / 0.6 s | 2 / 1 | |
| CCDFR / NCDFR | 0.7 s | **0** | physics-empty on nuclei (also 0 in v3.6.2, numu C12) |
| LambdaCCQE | 0.8 s | **0** (numu) / 3 (numubar) | needs an antineutrino |
| CCDIS / NCDIS | 1178 s / 2108 s | 8 / 16 | → ~1.3 h / ~2.3 h at 100 knots |
| CCRES / NCRES | 1560 s / 2568 s | 34 / 25 | → ~1.7 h / ~2.9 h at 100 knots |

Projection rule used: 100 knots ≈ 4× the 10-knot time (30 → ~120 evaluations); Fe56 at 200 knots
to 50 GeV ≈ 7–9× (more knots, DIS phase space grows with E); allow 2× for slower workers.
Bands: 14400 s (COH/MEC/NCEL/NuE/Lambda/IMD, all ≤ 2 min locally), 43200 s (Ar40/C12 CCQE-G18/G24,
DIS, RES, Charm), 85000 s (Valencia-tune CCQE; every Fe56 long-band job).

CCQE (10 knots, -e as in the matrix): G24_12a_00_000 155 s (Martini-QEL hybrid, fast);
**AR23_20n_00_000 3465 s** (Nieves/ZExp: 14 s at 0.16 GeV rising to ~200–240 s per knot above
2 GeV; smooth, no pathological knot). NOTE the earlier "stuck on the first knot for 49 min"
reading was an artifact: gmkspl's stdout is block-buffered through the supervisor, so the
per-knot NOTICE lines only appear in chunks. Projection at 100 knots (~120 evaluations, pod
speed): G18_10a ~3.6 h, AR23_20n ~5.6 h; Fe56 at 200 knots to 50 GeV ~9 h → CCQE for the
Valencia tunes and for Fe56 needs the 85000 s (23.6 h) band, not 43200 s.

### Matrix trimmed accordingly (wave script updated 21:35 UTC)
CCDFR/NCDFR dropped for all rows, LambdaCCQE dropped for numu, CCQE moved to the long-lifetime
band: **202 submissions** (7 rows × (12 numu + 13 numubar) + Fe56 (13 + 14)).

## Stage 3 — pilot (CCDIS Ar40, Charm Ar40, NCDIS Ar40 for row A; CCDIS Fe56 -e 50 -n 200)

- [ ] wall times (PNFS mtimes): CCDIS Ar40 xxx · Charm Ar40 xxx · NCDIS Ar40 xxx · CCDIS Fe56 xxx
- [ ] lifetimes set: DIS/Charm/RES xxx s · others xxx s

## Stage 3 — pilot
Replaced by the local cost probes above (grid pilot skipped): the 43200 s band covers CCQE
(G18_10a, ~3 h) and DIS/Charm/RES with margin; 14400 s covers the rest (≤ 2 min locally).

## Stage 4 — wave

- [x] **Wave 1 launched 21:36:39 UTC** (detached; log
      `/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380/logs/wave1-20260903.log`):
      rows A, D, G complete + rows B, C, E without CCQE = 194 submissions, ~3 s each.
      First job: A numu Ar40 CCQE `gmkspl_grid-numu_Ar40_20260903-213639-0266e3`,
      cluster `93584179.0@jobsub02`, lifetime 43200 s.
- [x] Wave 1 finished 21:45:01 UTC: **193 submitted, 193 confirmed**, 1 skipped (NuEElastic smoke), 0 errors.
- [x] 21:46–21:47 UTC: **row G re-lifetimed** — its 2 CCQE + 10 DIS/RES/Charm jobs (43200 s)
      cancelled minutes after submission and resubmitted with `LIFE_LONG=85000` (200 knots to
      50 GeV projects to ~9 h CCQE / ≥5 h DIS locally); **rows B, C CCQE submitted** with
      85000 s (AR23_20n probe: ~5.6 h at 100 knots locally). 12 `cancelled` records remain in
      the run dir (harmless; the resume guard ignores them).
- [x] **Row E CCQE runs locally, not on the grid** (decided 23:4x UTC): the AR25_20i probe
      (`SpectralFunc/ApproxElements` for C12 and Ar40) took **10000 s for 10 knots to 3 GeV**
      (~430 s per knot) → ~11 h at 100 knots on this pod, up to ~2× on a slow worker, i.e. at
      or beyond the 85000 s lifetime (eviction = restart from zero). Same binaries, same
      `-n 100 -e 3`, only the host differs: 4 supervised background runs of
      `run_gmkspl.py --installation genie_rc --label rc_v380_splines` (numu/numubar × C12/Ar40),
      picked up by `merge_rc_v380_splines.sh`'s labelled-local fallback. Grid with 172800 s or
      50 knots remain the alternatives if the user prefers.
- [ ] submissions 203 live/done of 207 planned (202 combos + smoke; row E CCQE pending) ·
      done xxx · resubmits xxx (ledger below)

## Stage 5 — merge & validate

- [ ] 8 merged XMLs under `/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380/<TUNE>/`
  - [x] **D / G24_12a_00_000 / Ar40** merged 23:17 UTC: `gxspl-Ar40-numu-numubar-k100-e5.xml`,
        25/25 jobs, 218 splines, 0 duplicate keys, nknots=100, one `genie_tune` section,
        sha256 `7d4e69a7f98c724ab312b0feb87ef583b5646bac8b6d5360f74f1112d07e938c`.
        Validated 23:19 UTC: all splines reach 5 GeV; per-probe coverage CC/NC × QES, RES, DIS,
        MEC, COH + NuEEL; `gspl2root` → `xsec_graphs-Ar40.root` (2.1 MB, rc 0); local
        `gevgen --event-generator-list Default` numu Ar40 200 ev @ 3 GeV
        (`gevgen-numu_Ar40_20260903-231923-206-3e33f3`): rc 0, 200 events (QE 34 / RES 74 /
        DIS 74 / MEC 18; CC 154 / NC 46), 219 splines loaded, **0 on-the-fly spline
        computations**, 0 selection failures.
  - [x] **D / G24_12a_00_000 / C12** merged 2026-09-04 00:01 UTC: `gxspl-C12-numu-numubar-k100-e5.xml`,
        25/25 jobs, 218 splines, 0 duplicates, nknots=100, Emax 5 GeV everywhere,
        sha256 `1cf574b8003e731827e7772e0882c548e8eeeb4f060220acc5a3d0095954aeb0`;
        `gspl2root` ok (`xsec_graphs-C12.root`, 2.1 MB); gevgen numubar C12 `Default` 200 ev
        @ 3 GeV (`gevgen-numubar_C12_20260904-000141-e32-da4371`): rc 0, 200 events, 0
        on-the-fly splines, 0 selection failures.
- 00:02 UTC re-poll: 187 done, 11 running (CCQE Ar40 ×5, CCRES ×3, Fe56 CCQE ×2 + CCRES ×1), 0 failed.
  - [x] **A / G18_10a_02_11b / Ar40** merged 00:24 UTC: `gxspl-Ar40-numu-numubar-k100-e10.xml`,
        25/25 jobs, 211 splines, 0 duplicates, nknots=100, Emax 10 GeV, 11 process types,
        sha256 `6a045c06dd511bc1eb2db4e4f6a4bde71267396bdae41c8332a6bc00ee65e7c6`;
        `gspl2root` ok (`xsec_graphs-Ar40.root`, 2.2 MB); gevgen numu Ar40 `Default` 200 ev
        @ 6 GeV (`gevgen-numu_Ar40_20260904-002432-805-589742`): rc 0, 200 events, 0 on-the-fly
        splines, 0 selection failures.
- 00:23 UTC: 6 grid jobs left, all CCQE: AR23_20m Ar40 ×2, AR23_20n Ar40 ×2, G18_10a Fe56 ×2.
- [ ] key/knot/tune checks xxx · gspl2root xxx · gevgen Default smoke ×8 xxx

## Stage 6 — preserve

- [ ] persistent mirror + sha256 (scratch / persistent / local) xxx
- [ ] run-manifest rebuilt xxx · genie-grid skill + memory updated xxx

## Deviations / notes

- 2026-09-03: **IMD excluded for rows A–E** (`-e ≤ 10 GeV` < 10.9 GeV threshold; local gate wrote
  0 splines at 5 GeV). Only the Fe56 50 GeV row (G) submits `IMD`. gevgen with `Default` on the
  A–E merged sets will compute the (zero) IMD spline on the fly at startup — expected, tolerated in
  the Stage 5 check (precedent: AR23's NUsmall product ships no IMD-ANH splines).

- 2026-09-04 00:00 UTC: **bearer token expired at 23:30 UTC** (2–3 h lifetime); `job.py
  list/status` then re-poll silently (jobsub_q `ExpiredSignatureError`) and report stale
  statuses, and `xrdfs` refuses. Refreshed with `htgettoken -a htvaultprod.fnal.gov -i dune`
  (non-interactive while the kinit ticket is valid); the queue monitor now refreshes the token
  before every poll. The **Kerberos ticket expires 2026-09-04 05:30 UTC** — after that no
  polling/pulling until the user runs `kinit` (grid jobs themselves are unaffected).
- Re-poll at 00:00 UTC: 183 done, 15 running, 0 failed/held.

## Ledger

(filled by Stage 4: row · probe · list · jobid · status · wall · sha256)

# Plan: scale the 18 EM-QES gevgen jobs to 10M events each

**Status:** SUBMITTED 2026-06-01 — 18 clusters × 20 processes = 360 grid jobs,
180M events total (`n=500000, N=20` uniform). Submission script:
`.claude/plans/submit_emqes_10M.sh`. Jobid/cluster table at bottom. Created 2026-06-01.
**Goal:** extend the 18 EM-QES `e-` gevgen grid jobs (JLab E91-013 / nucl-ex_0303011
kinematics) from 1000 events each to **10M events each** (180M total), split for
grid parallelism.

## Context / what already exists

- **18 settings** = 6 beam-energy/Q2 points × 3 targets (C12, Fe56, Au197). The
  1000-event versions ran 2026-06-01 (see `results/pages/q2_dist_emqes.md` and
  `jobsub-agent/jobsub-runs/gevgen_grid-2026-06-01/`).
- **Splines already on `/pnfs`** for tunes 04–08 × all 3 targets (gmkspl grid
  jobs done 2026-06-01). **No gmkspl needed.**
  Path: `/pnfs/dune/scratch/users/liangliu/jobsub-agent/prd_paper/EM/genie_dev/GEM21_11a_0X_000/.../0000/spl_grid_*.xml`
- Tarballs: `--tarball-label genie_dev --tune-tarball-label gem21_emq2lim`.

### The 6 beam settings (target-independent)
| Beam E (GeV) | Q2 point (GeV/c)2 | Tune | EM-MinQ2Limit (GeV2) |
|---|---|---|---|
| 2.445 | 0.64 | GEM21_11a_04_000 | 0.54 |
| 0.845 | 0.64 | GEM21_11a_04_000 | 0.54 |
| 2.445 | 1.28 | GEM21_11a_05_000 | 1.18 |
| 3.245 | 1.80 | GEM21_11a_06_000 | 1.70 |
| 1.645 | 1.83 | GEM21_11a_07_000 | 1.73 |
| 3.245 | 3.25 | GEM21_11a_08_000 | 3.15 |

## Adapter parallelism model (confirmed in code)

`run_gevgen_grid.py`: `-n` = events **per process**, `-N` = **number of grid
processes**. Total events for a setting = `N × n`.
Worker `gevgen_grid.sh`: per-process seed = `$CLUSTER + $PROCESS` (reproducible,
non-overlapping); each process writes its own `pNNNN/` subdir. So splitting one
setting across N processes is statistically clean — just `hadd` at the end.
**One submit = one (probe,target,energy,tune) cluster of N processes.** All 18
settings stay separate submits; N/n can differ per setting.

## Decisions (user-approved 2026-06-01)

- **Sizing:** calibrate first, then set N per target so each process runs ~2 h.
- **Outputs:** keep BOTH GHEP + gst (no worker change). ~180 GB on /pnfs scratch.

## Steps

### Step 0 — Calibrate per-event time (3 jobs, ~10 min)
One process each, mid-Q2 setting (tune 05, E=2.445), small stats:
```bash
pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
    --probe eminus --target <C12|Fe56|Au197> -n 20000 -e 2.445 \
    --cross-sections <tune05 spline on /pnfs for that target> \
    --tune GEM21_11a_05_000 --genlist EMQE \
    --tarball-label genie_dev --tune-tarball-label gem21_emq2lim -N 1
```
Read `Approximate processing time/event` from each `.ghep.status` (fetch via the
`pnfs-fetch` skill recipe). Record real ms/evt per target.

### Step 1 — Splines
Already on /pnfs (see Context). Verify presence; do NOT regenerate.

### Step 2 — Size N per target (~2 h/process target) — DONE 2026-06-01
**Measured** ms/evt from today's 1000-evt jobs (tune 05, E=2.445, spline
preloaded) read from each `.ghep.status` (`processing time/event`):

| Target | measured ms/evt | n/process | proc time | N | total |
|---|---|---|---|---|---|
| C12 | 7.69 | 500,000 | 1.07 h | 20 | 10.0M |
| Fe56 | 8.58 | 500,000 | 1.19 h | 20 | 10.0M |
| Au197 | 9.13 | 500,000 | 1.27 h | 20 | 10.0M |

Key finding: the three targets clock nearly identically (~8–9 ms), NOT the
7/11/22 spread originally guessed — EM-QES time is dominated by the elementary
cross-section, not nuclear size. So **uniform `n=500000, N=20` for all 18
settings**: exactly 10M events each, ~1.1–1.3 h/process, **360 processes total**.

### Step 3 — Submit production (18 loops)
Reuse the 2026-06-01 submission loop; swap `-n 1000 -N 1` for per-target
`-n`/`-N` from Step 2. **Dry-run one setting first** (`--dry-run`), inspect
`command_str`, then submit all 18. Optionally stage per-target-class in waves.

### Step 4 — Track & merge
- `pixi run python jobsub-agent/scripts/job.py status <jobid>` per cluster, or jq
  sweep over `jobsub-agent/jobsub-runs/*/*.gridlog`.
- Per setting when done: pull N files, `hadd merged.ghep.root pNNNN/*.ghep.root`
  (and gst) → 18 merged 10M-event files.
- Watch the false-`failed` caveat: a transient landscape.fnal.gov 500 in fetchlog
  can mark a finished job `failed` even though outputs are on /pnfs (see
  jobsub-jobs / pnfs-fetch skills). Verify with `find /pnfs/...` before retrying.

## Pre-launch logistics
- **Disk:** ~180 GB GHEP+gst total (GHEP ≈ 0.6 MB/1000 evt → ~6 GB/setting GHEP +
  ~4 GB gst). Per process (n=500k) ≈ 300 MB. Check scratch quota first.
- **Token:** submission needs a live token; running jobs carry their own proxy.
  Refresh: `htgettoken -a htvaultprod.fnal.gov -i dune`.

## Open items
- Exact ms/evt per target (fills Step 2 table) — pending Step 0.
- Confirm /pnfs scratch quota ≥ ~200 GB headroom.

## Submitted clusters (2026-06-01)

| target | tune | E (GeV) | jobid | cluster |
|---|---|---|---|---|
| Au197 | 04 | 0.845 | gevgen_grid-eminus_Au197_20260601-153751-8c8a58 | 28321813.0@jobsub05.fnal.gov |
| C12 | 04 | 0.845 | gevgen_grid-eminus_C12_20260601-153746-8c16de | 70238441.0@jobsub03.fnal.gov |
| Fe56 | 04 | 0.845 | gevgen_grid-eminus_Fe56_20260601-153749-e843c5 | 28321812.0@jobsub05.fnal.gov |
| Au197 | 04 | 2.445 | gevgen_grid-eminus_Au197_20260601-153744-0abcb5 | 70238440.0@jobsub03.fnal.gov |
| C12 | 04 | 2.445 | gevgen_grid-eminus_C12_20260601-153739-98354a | 84496603.0@jobsub01.fnal.gov |
| Fe56 | 04 | 2.445 | gevgen_grid-eminus_Fe56_20260601-153741-74b432 | 28321811.0@jobsub05.fnal.gov |
| Au197 | 05 | 2.445 | gevgen_grid-eminus_Au197_20260601-153801-f37fa6 | 70238442.0@jobsub03.fnal.gov |
| C12 | 05 | 2.445 | gevgen_grid-eminus_C12_20260601-153754-c4e658 | 84496604.0@jobsub01.fnal.gov |
| Fe56 | 05 | 2.445 | gevgen_grid-eminus_Fe56_20260601-153757-bb7a27 | 28032030.0@jobsub04.fnal.gov |
| Au197 | 06 | 3.245 | gevgen_grid-eminus_Au197_20260601-153809-505e7a | 91654713.0@jobsub02.fnal.gov |
| C12 | 06 | 3.245 | gevgen_grid-eminus_C12_20260601-153804-343693 | 70238443.0@jobsub03.fnal.gov |
| Fe56 | 06 | 3.245 | gevgen_grid-eminus_Fe56_20260601-153806-1590b5 | 84496606.0@jobsub01.fnal.gov |
| Au197 | 07 | 1.645 | gevgen_grid-eminus_Au197_20260601-153817-0605f1 | 91654716.0@jobsub02.fnal.gov |
| C12 | 07 | 1.645 | gevgen_grid-eminus_C12_20260601-153812-52a08c | 91654714.0@jobsub02.fnal.gov |
| Fe56 | 07 | 1.645 | gevgen_grid-eminus_Fe56_20260601-153815-dca88f | 28321814.0@jobsub05.fnal.gov |
| Au197 | 08 | 3.245 | gevgen_grid-eminus_Au197_20260601-153825-74c090 | 28321815.0@jobsub05.fnal.gov |
| C12 | 08 | 3.245 | gevgen_grid-eminus_C12_20260601-153820-409050 | 28032031.0@jobsub04.fnal.gov |
| Fe56 | 08 | 3.245 | gevgen_grid-eminus_Fe56_20260601-153822-0d55ac | 70238444.0@jobsub03.fnal.gov |

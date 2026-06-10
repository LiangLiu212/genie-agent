# 100x statistics campaign for the prd-analyzer t05 samples (1B events/model)

## Context

The prd-analyzer compares five QE-EM models at the E91-013 t05 point (e- on C12 @ 2.445 GeV,
Q2 = 1.28) with 10M events/model. The pencil-cut branch (`prd/electron/angle_cut_0.1_degree`)
showed stage 2 is statistics-starved there: only 25-104 events survive from 10M. Generating
100x (1 billion events per model) gives O(2.5k-10k) pencil-cut stage-2 events and ~25x smaller
statistical errors everywhere else.

User decisions already made: **keep ghep + gst on PNFS** (no worker/adapter code changes,
~5.4 TB total on dune scratch) and **scope = the five t05 models only**.

## Measured inputs (from the existing campaigns)

- Runtime: 100k ev = 25-30 min/process; 500k = ~80 min -> **1M = 2.5-3 h**, well under the
  default 8 h lifetime. Memory was fine at 500k (GENIE writes incrementally).
- Sizes: per 1M events ghep = 516 MB, gst = 553 MB -> ~1.07 TB/model, **~5.4 TB campaign total**
  on `/pnfs/dune/scratch` (30-day LRU eviction).
- Splines: already on PNFS per tune (reused; no new gmkspl).
- Worker seed = `CLUSTER + PROCESS` (`jobsub-agent/adapters/genie/templates/gevgen_grid.sh`).

## Campaign shape

One cluster per model: `-N 1000` processes x `-n 1000000` events = 1B/model, 5 submissions:

| model | tune | install tarball | tune tarball |
|---|---|---|---|
| LFG | GEM26_11a_05_000 | genie_inclxx (2026-06-09) | gem26_emq2lim (2026-06-09) |
| SF | GEM26_22a_05_000 | genie_inclxx | gem26_emq2lim |
| SuSAv2 | GEM21_11a_05_000 | genie_dev (2026-06-01) | gem21_emq2lim (2026-06-01) |
| SF(2024)+UQEL | GEM26_33b_05_000 | genie_inclxx | gem26_emq2lim |
| SF+UQEL | GEM26_22b_05_000 | genie_inclxx | gem26_emq2lim |

Submission command per model (genie-grid adapter, same pattern as the 10M campaign):

```
pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
    --probe eminus --target C12 -n 1000000 -e 2.445 \
    --cross-sections <that tune's existing PNFS spline xml> \
    --tune <tune> --genlist EMQE \
    --tarball-label <install label> --tune-tarball-label <tune label> \
    -N 1000 [--dry-run first]
```

Seed correctness: one cluster per model means seeds `CLUSTER+0..CLUSTER+999` are unique within
each sample. The 1B samples **replace** the 10M ones in the analysis (never combined), so seed
collisions with the old clusters are irrelevant.

## Execution steps

1. **Save this plan** into the repo's tracked `.claude/plans/` (repo convention).
2. **Preflight**: `tarball.py` staleness check on all four labels; `find` each tune's spline
   xml on PNFS; fresh token (`htgettoken -i dune`).
3. **Pilots**: two `-N 2 -n 1000000` clusters (one genie_inclxx model + SuSAv2/genie_dev).
   Verify: outputs land (~516 + 553 MB), runtime ~3 h, seed line in fetched log, gst streams
   via XRootD and has 1M entries. Pilot stems are separate dirs - excluded from analysis.
4. **Full submit**: 5 clusters x 1000 procs (≈14k slot-hours; drains roughly overnight).
5. **Track** via jobsub-jobs skill (queue poll + PNFS sweep; expect 1000 triplets/model).
   Shortfall >1%: fill-in cluster for the missing process count, only after checking the
   fill-in cluster id's seed range `[C_f, C_f+n)` is disjoint from the production range.
6. **Analysis updates** (on `main`, then `git merge main` into each `prd/electron/angle_cut_*`
   branch - clean, since branches only diverge in `selection.py` CUTS + README + figures):
   - `results/prd-analyzer/samples.py`: point the five SAMPLES leaf dirs at the new stems.
   - `results/prd-analyzer/build_cache.py`: parallelize the per-file streaming loop
     (ProcessPoolExecutor, ~8 workers; files are independent; merge arrays at the end).
     Serial would be ~2.5 h/model at the measured ~60 MB/s.
   - **Superset cache** (stream once, reuse on all three branches): build the stage-1 cache
     with the loosest electron window (theta_e +-6; El window is identical on all branches)
     into `cache/superset/<model>.npz` (~17M rows/model). New small `recut_cache.py`: filter
     superset rows by the branch's `CUTS["theta_e"]` and recompute the stage2 mask from the
     cached `has_p/Tp/theta_p` columns (all columns are already in the npz schema) -> writes
     the standard `cache/<model>.npz`. Each branch then replots without re-streaming.
7. **Re-render per branch** (0.1, 1, 6 degree): recut -> run the four plot scripts -> update
   README Ns/efficiencies -> commit per branch (push when asked).

## Verification

- Pilot: `uproot.open(root://...)["gst"].num_entries == 1_000_000`; seed printed in log.
- Post-drain PNFS sweep: 1000 x (ghep+gst+status) per model; spot-check file sizes.
- Superset cache: `ntot == 1e9` per model; stage-1 fraction ~1.7% (matches the 10M +-6 run).
- Recut cross-check: `MAX_FILES=2` direct build at +-0.1 vs recut of the same two files'
  superset rows - identical row counts and stage2 sums.
- End state: pencil-branch stage-2 N ≈ 100x current (LFG ~10k ... SF ~2.5k); figures readable.

## Costs / risks

- ~14k slot-hours, ~1 day wall clock; 5.4 TB scratch with 30-day LRU - build the superset
  caches promptly after drain (the npz then survives eviction; everything is regenerable from
  logged seeds anyway).
- 1M ev/proc memory assumed flat vs 500k - the pilot validates before the full submit.
- No jobsub-agent adapter/worker changes needed (ghep kept; defaults for lifetime/disk/memory).

## Files to modify (execution phase)

- `results/prd-analyzer/samples.py` - five new leaf dirs + docstring counts
- `results/prd-analyzer/build_cache.py` - parallel streaming + superset mode
- `results/prd-analyzer/recut_cache.py` - new (superset -> branch cache)
- `results/prd-analyzer/README.md` - per-branch numbers after replot
- `.claude/plans/` in the repo - this plan, tracked

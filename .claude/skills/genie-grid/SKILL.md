---
name: genie-grid
description: Run GENIE gmkspl/gevgen jobs on the Fermilab DUNE grid via jobsub-agent's GENIE adapter. Use when the user wants to generate cross-section splines or neutrino events at grid scale (many jobs), submit gmkspl/gevgen to the grid, or pull grid GENIE outputs back. For LOCAL single GENIE runs use genie-agent's run_gmkspl/run_gevgen instead.
---

# GENIE on the grid (`jobsub-agent/adapters/genie/`)

The GENIE adapter wraps jobsub-agent's generic core to submit gmkspl/gevgen at
grid scale. It resolves PDGs from the shared `shared/pdg.json` (same source as
genie-agent), validates GENIE rules, references a **published tarball by label**,
builds the worker args + PNFS output path, and submits.

## Prerequisites
1. A grid node with jobsub_lite + a valid token (`htgettoken … -i dune`) — see
   the **jobsub-submit** skill for the auth notes.
2. A **published GENIE tarball** in the catalog — see the **jobsub-tarball**
   skill. You pass its label as `--tarball-label`.
3. For gevgen: a cross-section spline reachable by the grid. Stage it to
   `/pnfs/dune/scratch/users/$USER/...` and pass the `/pnfs/...` path — the grid
   file-transfer host **cannot** read `/exp/dune/data`. A local path still works
   (uploaded via `-f file://`) but is slow for large splines.

## Commands
```bash
# splines (gmkspl) — probe/target lists, -N defaults to 1
pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
    --probes numu,numubar --targets C12,Ar40 \
    --tune G18_02a_00_000 --genlist CCQE -e 10 -n 100 \
    --tarball-label genie_rc_main -N 1 [--dry-run]

# events (gevgen) — one probe/target, mono-energetic, -N processes share inputs
pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
    --probe numu --target C12 -n 1000 -e 3.0 \
    --cross-sections /pnfs/.../spline.xml \
    --tune G18_02a_00_000 --genlist CCQE \
    --tarball-label genie_rc_main -N 100 [--dry-run]
```
`--tune`/`--genlist` default to genie-agent's `default_tune`/`default_generator_list`.
Add `--tune-tarball-label <label>` to overlay custom tunes via GXMLPATH (worker
`-X`). **Dry-run first** (`--dry-run` → `--no_submit`) to inspect the argv.

## Validation rules the adapter enforces (errors)
- `generator_list='Default'` is rejected (PYTHIA6 charm broken).
- Charged-lepton probe (`eminus`/…) ⇒ a `GEM*` tune **and** an `EM*` generator
  list; neutrino probe ⇒ non-GEM tune and a non-EM list.
- targets must be a nucleus PDG or free nucleon; `-N` > 0.
- gevgen: scalar `--energy` only (no flux/energy-range on the grid yet);
  `--cross-sections` must be absolute.

## After submitting — track + pull (jobsub-jobs skill)
```bash
pixi run python jobsub-agent/scripts/job.py status <jobid>
pixi run python jobsub-agent/scripts/job.py pull   <jobid> --suffix .ghep.root   # gevgen
pixi run python jobsub-agent/scripts/job.py pull   <jobid> --suffix .xml         # gmkspl
```
Outputs land under `/pnfs/dune/scratch/users/$USER/jobsub-agent/<project>/<channel>/
<installation>/<tune>/<stem>_{gev,spl}/...`; `pull` copies them locally. The
adapter stamps `.extra.output_suffix` so status/pull know what to look for.
Per-process seed on the worker is `$CLUSTER + $PROCESS` (reproducible).

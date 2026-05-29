---
name: jobsub-tarball
description: Build, publish (to RCDS/CVMFS), and catalog tarballs for jobsub-agent grid jobs via scripts/tarball.py. Use when the user wants to build a code/install tarball for the grid, publish it to CVMFS under a label, list/verify the tarball catalog, check tarball staleness, or adopt a published tarball from an existing job.
---

# Tarballs for jobsub-agent (`scripts/tarball.py`)

Grid jobs ship their code/install via `jobsub_submit --tar_file_name`. jobsub-agent
builds a tarball, publishes it to RCDS (which lands it under a random
`/cvmfs/fifeuserN.opensciencegrid.org/sw/dune/<hash>/`), and records the real
CVMFS path in a label→entry catalog (`config/catalog.json`). Grid run scripts
then reference the tarball by **label**.

```bash
# build (or reuse cached) a tarball of selected top-level trees under a dir
pixi run python jobsub-agent/scripts/tarball.py build --build-dir /abs/install \
    --toplevel Generator --toplevel data --exclude-component src --exclude-suffix .o [--force]

# publish a local tarball to CVMFS under a label (runs ONE sentinel grid job)
pixi run python jobsub-agent/scripts/tarball.py publish --tarball /abs/x.tar --label genie_rc_main

pixi run python jobsub-agent/scripts/tarball.py list [--verify]
pixi run python jobsub-agent/scripts/tarball.py verify --label genie_rc_main
pixi run python jobsub-agent/scripts/tarball.py label-from-job --label genie_rc_main --jobid <jobid>
```

## How publish works
`publish` submits a one-process **sentinel** grid job (`lib/templates/publish_only.sh`)
that echoes `PUBLISH_SENTINEL_CVMFS_DIR=<path>`; jobsub-agent polls until it
drains, fetches its log, and greps that path. So `publish` needs jobsub_lite +
a token (a grid node) and takes a few minutes. The cache key for `build` is
sha1(build_dir + sorted mtimes of the selected trees) — re-running `build`
reuses the cached `.tar` unless `--force`.

## Staleness (RCDS garbage-collects ~30 days)
`verify` / `list --verify` report `recommendation`: `ok` (< 21d), `warn`
(21–28d), `republish` (> 28d or the CVMFS path is gone). The GENIE grid run
scripts auto-verify the label and **refuse to submit** an expired tarball,
telling you to republish:
```bash
pixi run python jobsub-agent/scripts/tarball.py publish --tarball <x.tar> --label <label> --overwrite
```

## GENIE specifics
The GENIE install lives in `genie-agent`'s active installation. Build with that
install's dir as `--build-dir` and GENIE's tree list, e.g.:
```bash
--toplevel Generator --toplevel Reweight --toplevel data \
--toplevel inclxx_genie/install --toplevel setup_env.sh \
--exclude-component src --exclude-component .git --exclude-suffix .o --exclude-suffix .d
```
For a GXMLPATH tune overlay, build an overlay tarball (`build_overlay_tarball`
in `lib/tarball.py`; xml/md only) and pass its label as `--tune-tarball-label`
to the grid run scripts. See the **genie-grid** skill.

# jobsub-agent

A **generic `jobsub_lite` grid-submission toolkit** (core `lib/`) plus a thin
**GENIE adapter** (`adapters/genie/`). Sibling of `genie-agent/`: genie-agent
makes local splines/GHEPs; jobsub-agent submits the grid-scale versions and
pulls the outputs back. The core has zero GENIE knowledge — PDGs, worker
scripts, and PNFS schemes live only in the adapter.

Design + build order live in `../.claude/plans/jobsub-agent.md` (source of
truth; update it when the design changes).

## Layout

```
jobsub-agent/
├── config/jobsub.json        # jobsub_lite bins + group/role + pnfs base (machine-local, gitignored)
├── lib/                      # GENERIC core — no GENIE imports
│   └── templates/            #   publish_only.sh (generic sentinel worker)
├── scripts/                  # generic CLI: submit.py, job.py, tarball.py
├── adapters/genie/           # GENIE-specific layer
│   ├── pdg.py                #   thin loader of repo-shared ../shared/pdg.json
│   └── templates/            #   gmkspl_grid.sh, gevgen_grid.sh (workers)
└── jobsub-runs/              # per-job records + submit/fetched logs (gitignored)
    └── <runtype>-YYYY-MM-DD/<stem>.{gridlog,submit.log,command.json}
```

`config/` and `jobsub-runs/` are **gitignored** (machine-specific bin paths,
the CVMFS publish `catalog.json`, generated run artefacts) — same convention as
`genie-agent/`. `config/jobsub.json` is created locally; its schema:

| key | meaning |
|---|---|
| `jobsub_bin` / `jobsub_q_bin` / `jobsub_rm_bin` / `jobsub_fetchlog_bin` | absolute `jobsub_lite` binary paths |
| `default_group` / `default_role` / `default_disk` | jobsub `-G` / `--role` / `--disk` defaults |
| `default_project` | top dir under the PNFS scratch scheme |
| `pnfs_scratch_base` | e.g. `/pnfs/dune/scratch/users` (`/$USER/...` appended at runtime) |
| `append_condor_requirements` | passed to `--append_condor_requirements` |

## Running (once built)

```bash
pixi run python jobsub-agent/scripts/submit.py  ...      # generic submit
pixi run python jobsub-agent/scripts/job.py     status|list|cancel|fetchlog|pull <jobid>
pixi run python jobsub-agent/scripts/tarball.py build|publish|list|verify ...
pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py ...   # GENIE grid runs
```

## Status

Build order (see the plan). **Step 1 — scaffold + config + gitignore — done.**
Remaining: `lib/{config,submit_env,records}` → `submit` → `monitor`/`control`/
`job.py` → `outputs` → `tarball`/`publish` → GENIE adapter → skills → e2e.

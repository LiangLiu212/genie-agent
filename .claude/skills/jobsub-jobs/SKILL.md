---
name: jobsub-jobs
description: Track, steer, and query jobsub-agent grid jobs — status/list/cancel/fetchlog/pull via scripts/job.py, and jq over the .gridlog records. Use when the user asks about grid job status, wants to cancel/fetch logs/pull outputs of a grid job, or wants to find/filter past grid submissions by status/cluster/tune/probe-target.
---

# Steering + querying jobsub-agent grid jobs

Every submission writes one self-contained JSON record:
`jobsub-agent/jobsub-runs/<runtype>-YYYY-MM-DD/<stem>.gridlog`. There is **no
registry** — the jobid `<runtype>-<stem>-<6hex>` decodes itself and `jq` over
the `.gridlog` files IS the query layer. Glob: **`jobsub-agent/jobsub-runs/*/*.gridlog`**.

## Control surface (`scripts/job.py`)
```bash
pixi run python jobsub-agent/scripts/job.py status   <jobid>   # re-poll jobsub_q + show
pixi run python jobsub-agent/scripts/job.py list     [--active]
pixi run python jobsub-agent/scripts/job.py cancel   <jobid>   # jobsub_rm
pixi run python jobsub-agent/scripts/job.py fetchlog <jobid>   # -> <stem>.fetched/
pixi run python jobsub-agent/scripts/job.py pull     <jobid> [--suffix .ghep.root] [--overwrite]
```
`status`/`list` re-poll `jobsub_q` for non-terminal jobs and persist the result.
These need jobsub_lite + a token (a grid node) — see the **jobsub-submit** skill.

## Status model
`pending` (record written, not yet submitted) → `submitted` (got a cluster id) →
`running` / `held` → terminal: `done` (queue drained + all outputs present),
`partial` (some outputs), `failed` (submit failed or zero outputs), `cancelled`.

When the queue drains, completion is decided by the **DONE sentinel** in fetched
worker logs (a standalone `DONE` line per process) — more reliable than the
ifdh PNFS count, which is the fallback. `processes_done_source` records which
was used.

## jq query recipes (over `jobsub-agent/jobsub-runs/*/*.gridlog`)
```bash
# all jobs: id / status / cluster / progress
jq -r '[.jobid,.status,.cluster_id,(.processes_done|tostring)+"/"+(.n_jobs|tostring)]|@tsv' jobsub-agent/jobsub-runs/*/*.gridlog
# only still-running/held
jq -r 'select(.status=="running" or .status=="held")|.jobid' jobsub-agent/jobsub-runs/*/*.gridlog
# failed/partial
jq -r 'select(.status=="failed" or .status=="partial")|[.jobid,.status,.fetchlog_error]|@tsv' jobsub-agent/jobsub-runs/*/*.gridlog
# by GENIE probe/target/tune (adapter stores these under .extra)
jq -r 'select(.extra.tune=="G18_02a_00_000")|[.jobid,.extra.probe,.extra.target,.status]|@tsv' jobsub-agent/jobsub-runs/*/*.gridlog
# the exact jobsub_submit command for a job
jq -r '.command_str' jobsub-agent/jobsub-runs/*/<stem>.gridlog
```

## Useful fields
Top level: `jobid`, `runtype`, `cluster_id`, `status`, `n_jobs`,
`processes_done`, `processes_done_source`, `outputs_pulled`, `submitted`,
`finished`, `submit_log_file`, `command_str`, `pnfs_output_dir`,
`local_output_dir`, `fetchlog_error`. Adapter metadata under `.extra`
(`probe`, `target`, `tune`, `genlist`, `channel`, `kind`, `output_suffix`).

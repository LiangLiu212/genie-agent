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

## Drain verdicts are gated on a healthy poll (fixed 2026-06-09) — but old records don't self-heal
`job.py status`/`list` decide the queue is drained by parsing their own
`jobsub_q` subprocess. On this host that poll can come back **empty** when the
jobsub_lite OpenTelemetry import crashes (`KeyError:
'OTEL_EXPORTER_JAEGER_ENDPOINT'`) — indistinguishable from a drained queue by
output alone. `lib/monitor.py::refresh_status` now **only drains when the poll
is healthy** (no error AND `raw_returncode == 0`); a crashed/timed-out poll
keeps the previous status instead of stamping `failed` on a running cluster.

Two caveats remain:
- **Records mislabelled before the fix stay wrong** — terminal states
  short-circuit and are never re-polled. E.g. the 2026-06-03 GEM26_22b spline
  jobs are stamped `failed` (with the OTEL traceback in `fetchlog_error`) but
  their splines landed on PNFS hours later. For any *pre-fix* terminal verdict,
  cross-check by hand:
  ```bash
  jobsub_q -G dune "$USER"     # handles missing tracing gracefully; also refreshes the token
  ```
  and check PNFS (below). A job is only really failed when its processes are
  **gone from `jobsub_q`** *and* it has no PNFS output.
- An unhealthy poll now means status simply doesn't advance — a job can look
  `running`/`submitted` longer than it really is until a healthy poll lands.

## Is a job done? Check the queue, then PNFS

`jobsub_q -G dune <user>` is the raw scheduler — the ground truth. Each row is a
**per-process subjob** `<cluster_id>.<proc>@jobsubNN.fnal.gov`
(e.g. `28032030.3@jobsub04.fnal.gov` = process 3 of cluster 28032030). A
20-process submission appears as up to 20 such rows under one cluster id; rows
still listed = processes not yet terminated.

**A process gone from `jobsub_q` has terminated — succeeded OR failed — and the
queue does not say which.** Decide by what landed on PNFS. Outputs go in
**per-process subdirs**, not the top of `pnfs_output_dir`:
`<pnfs_output_dir>/0000/…`, `0001/…` — one dir per process. A successful process
writes a triplet: `*.ghep.root` + `*.ghep.status` + `*.gst.root` (gmkspl: an
`*.xml`). So count recursively, not at the top level:
```bash
d=$(jq -r '.pnfs_output_dir' jobsub-agent/jobsub-runs/*/<stem>.gridlog)
find "$d" -name '*.ghep.root' | wc -l      # processes that succeeded
# compare to n_jobs; a process whose subdir has no .ghep.root failed
```
`job.py status`/`list` may still report `done=0/N` after outputs exist — its
count gates on the DONE sentinel in *fetched* logs, so fetch first
(`job.py fetchlog <jobid>`) or trust the PNFS file count.

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
`finished`, `submit_log_file`, `command_str`, `pnfs_output_dir` (base for the
per-process subdir sweep above), `local_output_dir`, `fetchlog_error`. Adapter
metadata under `.extra`
(`probe`, `target`, `tune`, `genlist`, `channel`, `kind`, `output_suffix`).

## Per-job status table (PROC / DONE / RUN, grouped by target)

The preferred summary for a multi-process batch: one row per submission with
**PROC** (`n_jobs`), **DONE** (outputs on PNFS, the ground truth), and **RUN**
(processes still in the live `jobsub_q`). DONE comes from the per-process subdir
sweep; RUN from the raw scheduler. Filter to the batch you care about (here:
`gevgen_grid` with `n_jobs==20`), group by `.extra.target`, and print subtotals
+ a grand total. Reads ground truth directly — does not rely on `job.py`'s
sentinel-gated `processes_done`.

```bash
cd /exp/dune/data/users/liangliu/genie-dev
# 1) live running-process count per cluster id (one jobsub_q poll, reused below)
jobsub_q -G dune "$USER" 2>/dev/null \
  | grep -oE '^[0-9]+\.' | tr -d '.' | sort | uniq -c \
  | awk '{print $2"\t"$1}' > /tmp/running.tsv

# 2) one row per matching submission
printf '%-3s %-6s %-15s %-8s %4s %5s %5s\n' '#' TGT JOBID STATUS PROC DONE RUN
i=0
for f in jobsub-agent/jobsub-runs/*/*.gridlog; do
  n=$(jq -r '.n_jobs' "$f");      [ "$n" = "20" ]            || continue   # batch filter
  rt=$(jq -r '.runtype' "$f");    [ "$rt" = "gevgen_grid" ]  || continue   # runtype filter
  i=$((i+1))
  jid=$(jq -r '.jobid' "$f");  st=$(jq -r '.status' "$f")
  tgt=$(jq -r '.extra.target' "$f")
  cl=$(jq -r '.cluster_id // ""' "$f"); clnum=${cl%%.*}
  suf=$(jq -r '.extra.output_suffix // ".ghep.root"' "$f")
  d=$(jq -r '.pnfs_output_dir // ""' "$f")
  run=$(awk -v c="$clnum" '$1==c{print $2}' /tmp/running.tsv); run=${run:-0}
  ok=0; [ -d "$d" ] && ok=$(find "$d" -name "*${suf}" 2>/dev/null | wc -l)
  short=$(echo "$jid" | grep -oE '[0-9]{6}-[0-9a-f]{6}$')   # HHMMSS-6hex
  printf '%-3s %-6s %-15s %-8s %4s %5s %5s\n' "$i" "$tgt" "$short" "$st" "$n" "$ok" "$run"
done | sort -k2     # group rows by target
```

Notes:
- DONE+RUN can briefly exceed PROC for one job — snapshot skew between the
  `jobsub_q` poll and the PNFS sweep while files are landing; the per-job
  ceiling is still `n_jobs`.
- `partial` vs `running` only reflects whether *any* process has drained yet;
  both are healthy mid-flight states.
- A terminated process (gone from the queue) with **no** PNFS output is a real
  failure — `FAIL = PROC − RUN − DONE` when that is > 0.

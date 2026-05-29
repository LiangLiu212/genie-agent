---
name: jobsub-submit
description: Submit a worker script to the Fermilab DUNE grid via jobsub_lite using jobsub-agent's generic submitter. Use when the user wants to submit a (non-GENIE-specific) grid job, run scripts/submit.py, dry-run a submission, or debug jobsub_lite auth/env issues. For GENIE gmkspl/gevgen grid jobs use the genie-grid skill instead.
---

# Submitting grid jobs with jobsub-agent (`scripts/submit.py`)

`jobsub-agent/` is a generic `jobsub_lite` submission toolkit (sibling of
`genie-agent/`). `scripts/submit.py` builds a `jobsub_submit` command from flags
+ a worker script and records the job as a registry-free `.gridlog`.

```bash
pixi run python jobsub-agent/scripts/submit.py \
    --worker /abs/worker.sh -N 100 \
    [--tar-file-name dropbox:///abs/install.tar] [-f /pnfs/.../input] \
    [--memory 2000MB] [--expected-lifetime 8h] [--dry-run] -- <worker args...>
```

- Everything after `--` is forwarded to the worker script.
- `--dry-run` appends `--no_submit`: the record is written `pending`, nothing is
  actually submitted. **Always dry-run first** to check the argv (it's saved to
  `<stem>.command.json`).
- Group/role/disk/append_condor_requirements default from `config/jobsub.json`.

## Always invoke through pixi
`pixi run python …` (Python 3.14 env). Track/steer jobs with the **jobsub-jobs**
skill (`scripts/job.py`).

## Auth + environment (read this if a real submit fails)
- jobsub_lite needs a valid **token** (`htgettoken`/`BEARER_TOKEN_FILE`) and
  **kerberos** (`KRB5CCNAME`), and must run on a node with `/opt/jobsub_lite`
  (e.g. a dunegpvm). The user runs these logins themselves — suggest typing
  `! htgettoken -a htvaultprod.fnal.gov -i dune` in the session.
- jobsub-agent runs every jobsub call under a **scrubbed env**
  (`lib/submit_env.py`): it drops `PIXI_*`/`CONDA_*`/`PYTHONHOME`/`PYTHONPATH`
  so pixi doesn't poison jobsub_lite's own python, while passing auth vars
  through. If a submit fails with a python/import error, this scrub is why it's
  *not* the cause; check the token/kerberos first.

## What gets written
`jobsub-runs/<runtype>-YYYY-MM-DD/<stem>.{gridlog,command.json,submit.log}`.
`runtype` defaults to `jobsub` (override with `--runtype`). The `.gridlog` is
the mutable record; `submit.log` is the combined jobsub_submit output;
`command.json` is the exact argv.

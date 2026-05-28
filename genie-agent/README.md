# genie-agent

CLI runners for GENIE binaries (`gmkspl`, future `gevgen`/`gntpc`). Runs under
**pixi** and shells out to GENIE binaries that live in a **spack** environment,
keeping the two envs cleanly separated. Each run writes a single mutable
`<stem>.log` JSON next to its artefacts.

## Layout

```
genie-agent/
├── config/
│   ├── genie_env.json          # installations + defaults
│   └── env/
│       └── <installation>.json # cached spack env per installation
├── lib/                        # shared modules (imported by scripts)
├── scripts/                    # CLI entry points
│   ├── run_gmkspl.py           # generate cross-section splines
│   ├── refresh_genie_env.py    # snapshot a setup_env.sh to config/env/
│   └── job.py                  # status / cancel / list background jobs
└── genie-runs/                 # output: genie-runs/<tune>-YYYY-MM-DD/
```

All scripts are launched via `pixi run python scripts/<name>.py …` from the
`genie-dev` root.

## Scripts

### `run_gmkspl.py` — run `gmkspl`

Generates GENIE cross-section splines. **Backgrounded by default**: prints a
`jobid` and returns immediately; the GENIE binary runs in a detached
supervisor.

```
pixi run python genie-agent/scripts/run_gmkspl.py \
    --probes numu --targets H1 \
    --tune G18_02a_00_000 --genlist CCQE \
    -n 30 -e 5
```

Required: `--probes`, `--targets` (comma-separated PDGs or aliases:
`numu,numubar`, `eminus`, `Ar40,C12`, …).

Common options:

| Flag                       | Purpose                                                 |
|----------------------------|---------------------------------------------------------|
| `--tune NAME`              | GENIE tune (default: `config.default_tune`).            |
| `--genlist NAME`           | Event-generator list (default: `config.default_generator_list`). |
| `-n / --n-knots N`         | Knots per spline (GENIE default ~200).                  |
| `-e / --max-energy GEV`    | Maximum spline energy (GENIE default 10 GeV).           |
| `--seed N`                 | RNG seed.                                               |
| `--input-cross-sections F` | Pre-existing XML to extend.                             |
| `--output-file F`          | Override output XML path.                               |
| `--installation NAME`      | Override active installation (else env / config).       |
| `--foreground`             | Block until done instead of detaching.                  |
| `--label STR`              | Free-text label saved into the runlog.                  |

Probe ↔ tune compatibility is checked before launch:

- Neutrino probes (`numu`, `nue`, …) require a neutrino tune (e.g. `G18_*`).
- Charged-lepton probes (`eminus`, `eplus`, `muminus`, …) require a `GEM21_*`
  tune and an EM generator list (`EM`, `EMQE`, `EMMEC`).

Artefacts per run, under `genie-runs/<tune>-YYYY-MM-DD/`:

```
<probes>_<targets>_<YYYYMMDD-HHMMSS>.log      # mutable job-state JSON
<probes>_<targets>_<YYYYMMDD-HHMMSS>.stdout   # gmkspl stdout
<probes>_<targets>_<YYYYMMDD-HHMMSS>.stderr   # gmkspl stderr
<probes>_<targets>_<YYYYMMDD-HHMMSS>.xml      # the spline XML
```

Hidden flag `--supervise --log-path … --env-path …` is the supervisor entry
point invoked by the detach mechanism — don't call directly.

### `job.py` — track and control background jobs

```
pixi run python genie-agent/scripts/job.py status <jobid>     # show + reconcile
pixi run python genie-agent/scripts/job.py cancel <jobid>     # SIGTERM, then SIGKILL
pixi run python genie-agent/scripts/job.py list [--active]    # table of all jobs
pixi run python genie-agent/scripts/job.py status <jobid> --json  # also dump full log
```

A **jobid** is `<runtype>-<stem>-<6hex>`, e.g.
`gmkspl-numu_H1_20260528-133027-471ff1`. The jobid alone is enough to find the
log file — no registry. `find_log_for_jobid` (`lib/jobs.py`) globs
`genie-runs/*/<stem>.log` and matches the jobid in the file.

`status` reconciles lost supervisors: if the log says `running:true` but the
pid is gone, it rewrites the file as `running:false, failed:true,
returncode:-1`.

`cancel` sends `SIGTERM` to the entire process group of the recorded pid,
waits 2 s, then escalates to `SIGKILL`. The supervisor's signal handler
writes `canceled:true, running:false` into the log; if the supervisor itself
is gone, `job.py` writes those fields directly.

`list` walks every `genie-runs/*/*.log` carrying a `jobid` and prints state,
jobid, pid, start time, and returncode. STATE is derived:

- `canceled` → `canceled:true`
- `failed` → `failed:true`
- `running` → `running:true`
- `done` → `running:false` and not canceled/failed
- `pending` → all three booleans still `null`

### `refresh_genie_env.py` — snapshot a spack env

Captures an installation's `setup_env.sh` into `config/env/<name>.json` so
runs don't pay the spack-load cost every time, and pixi's parent env can't
pollute the GENIE child.

```
pixi run python genie-agent/scripts/refresh_genie_env.py --installation genie_rc
pixi run python genie-agent/scripts/refresh_genie_env.py --all
pixi run python genie-agent/scripts/refresh_genie_env.py             # active install
```

The snapshot runs in a parent-env-stripped shell
(`env -i HOME=… USER=… TERM=… bash --noprofile --norc -c "source <script> &&
env -0"`) and drops `PIXI_*`, `CONDA_*`, `MAMBA_*`, `_CE_*`, `VIRTUAL_ENV*`,
`PYTHONHOME`, `PYTHONPATH`, and `BASH_FUNC_*` before persisting. Run it once
per installation, and again whenever the installation's `setup_env.sh`
changes — `lib/genie_env.py::load_genie_env` warns if the cache file is older
than the script.

## `<stem>.log` schema

One mutable JSON file per run. Initial state at launch, updated in place by
the supervisor (running → finished) and by `job.py status` / `cancel`.

```json
{
  "jobid":         "gmkspl-numu_H1_20260528-133027-471ff1",
  "runtype":       "gmkspl",
  "script":        "scripts/run_gmkspl.py",
  "script_path":   "/…/scripts/run_gmkspl.py",
  "script_sha256": "f84253ee2ae017a3",
  "git_sha":       "7c24103…",
  "cwd":           "/…/genie-runs/G18_02a_00_000-2026-05-28",
  "command":       ["…/gmkspl", "-p", "14", "-t", "1000010010", …],
  "description":   "gmkspl numu on H1 [G18_02a_00_000/CCQE]",
  "inputs":        { "probes": "numu", "targets": "H1", … },
  "outputs":       { "output_xml": "…", "stdout_log": "…",
                     "stderr_log": "…", "run_dir": "…",
                     "stem": "numu_H1_20260528-133027",
                     "genie_command": "…", "warnings": [] },
  "timestamp":     "2026-05-28T18:30:27Z",
  "started":       "2026-05-28T18:30:27Z",
  "finished":      "2026-05-28T18:30:28Z",
  "duration_s":    1.041,
  "pid":           1059479,
  "running":       false,
  "failed":        false,
  "canceled":      null,
  "returncode":    0,
  "output_xml_sha256": "…"
}
```

`running` / `failed` / `canceled` start as `null` and transition to
`true`/`false` as the run progresses. `returncode` is `null` until the
process exits.

## Config

`config/genie_env.json` holds installations and defaults:

```json
{
  "active_installation": "genie_rc",
  "default_tune":           "G18_02a_00_000",
  "default_generator_list": "CCQE",
  "installations": {
    "genie_rc": {
      "genie_bin_dir":      "/…/GENIE_RC/Generator/bin",
      "genie_lib_dir":      "/…/GENIE_RC/Generator/lib",
      "genie_setup_script": "/…/GENIE_RC/setup_env.sh"
    },
    …
  }
}
```

Override the active installation with `--installation NAME` on any runner, or
with `$GENIE_AGENT_INSTALLATION` in the environment.

`config/env/<installation>.json` is the cached spack env produced by
`refresh_genie_env.py`. `lib/genie_env.py::load_genie_env` prefers this file;
if it's missing, it warns and falls back to a live snapshot of
`genie_setup_script` (without writing the cache).

## Quick walkthrough

```bash
# one-time: cache the spack env so runs start fast
pixi run python genie-agent/scripts/refresh_genie_env.py --installation genie_rc

# kick off a background spline run
pixi run python genie-agent/scripts/run_gmkspl.py \
    --probes eminus --targets C12 \
    --tune GEM21_11a_00_000 --genlist EMQE -n 30 -e 10
# -> jobid: gmkspl-eminus_C12_20260528-131038-ab12cd

# check status (running / done / failed / canceled)
pixi run python genie-agent/scripts/job.py status \
    gmkspl-eminus_C12_20260528-131038-ab12cd

# cancel if needed
pixi run python genie-agent/scripts/job.py cancel \
    gmkspl-eminus_C12_20260528-131038-ab12cd

# see everything
pixi run python genie-agent/scripts/job.py list
```

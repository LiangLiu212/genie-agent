# genie-agent

CLI runners for GENIE binaries (`gmkspl`, `gevgen`, `gntpc`). Runs under
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
│   ├── run_gevgen.py           # generate neutrino events (mono-energetic)
│   ├── run_gntpc.py            # convert GHEP events to gst / other formats
│   ├── refresh_genie_env.py    # snapshot a setup_env.sh to config/env/
│   └── job.py                  # status / cancel / list background jobs
├── tunes/                      # custom tune families (pass via --gxmlpath)
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

### `run_gevgen.py` — run `gevgen`

Generates GENIE neutrino events at a **single, fixed energy** (mono-energetic;
flux / energy-range mode is not wired up yet). Same background-by-default model
as `run_gmkspl.py`.

```
pixi run python genie-agent/scripts/run_gevgen.py \
    --probe numu --target C12 -n 100 -e 3.0 \
    --cross-sections /abs/path/to/spline.xml \
    --tune G18_02a_00_000 --genlist CCQE
```

Required: `--probe`, `--target` (single PDG/alias each), `-n / --n-events`,
`-e / --energy` (GeV), and `--cross-sections` (a spline XML — usually the
output of a prior `run_gmkspl.py`). The cross-sections path is resolved to
absolute before launch, since the binary runs with `cwd` set to the run folder.

Common options:

| Flag                    | Purpose                                                 |
|-------------------------|---------------------------------------------------------|
| `--tune NAME`           | GENIE tune (default: `config.default_tune`).            |
| `--genlist NAME`        | Event-generator list (default: `config.default_generator_list`). |
| `-r / --run-number N`   | MC run number (`-r`).                                   |
| `--seed N`              | RNG seed.                                               |
| `--output-file F`       | Override output GHEP path.                              |
| `--installation NAME`   | Override active installation (else env / config).       |
| `--foreground`          | Block until done instead of detaching.                  |
| `--label STR`           | Free-text label saved into the runlog.                  |

The spline must cover the requested probe/target/genlist. Note that neutrino
CCQE needs a bound neutron, so e.g. `numu` CCQE on free `H1` yields no
cross-section and gevgen will have nothing to generate — use a target with
neutrons (`C12`, `Ar40`, …) or `H2`.

Artefacts per run, under `genie-runs/<tune>-YYYY-MM-DD/`:

```
<probe>_<target>_<YYYYMMDD-HHMMSS>.log         # mutable job-state JSON
<probe>_<target>_<YYYYMMDD-HHMMSS>.stdout      # gevgen stdout
<probe>_<target>_<YYYYMMDD-HHMMSS>.stderr      # gevgen stderr
<probe>_<target>_<YYYYMMDD-HHMMSS>.ghep.root   # the event file
```

### `run_gntpc.py` — run `gntpc`

Converts a GENIE GHEP event file (gevgen output) into a flat analysis format —
`gst` by default. Same background-by-default model as the other runners.

```
pixi run python genie-agent/scripts/run_gntpc.py \
    -i genie-runs/G18_02a_00_000-2026-05-28/numu_C12_20260528-140326.ghep.root \
    -f gst
```

Required: `-i / --input` (the GHEP file). There is **no `--tune/--probe/--target`**
— the output filename is derived from the input filename, and tune / probe /
target / source-jobid are inherited from the input's sibling `<stem>.log` when
it exists (recorded under `inputs.source_log`, etc.). If the sibling log is
missing, gntpc still runs; only the inherited metadata is omitted.

Common options:

| Flag                  | Purpose                                                  |
|-----------------------|----------------------------------------------------------|
| `-f / --format FMT`   | Output format (default `gst`). One of: `gst`, `gxml`, `rootracker`, `rootracker_mock_data`, `t2k_rootracker`, `numi_rootracker`, `t2k_tracker`, `nuance_tracker`, `ghad`, `ginuke`. |
| `-o / --output-file F`| Override output path (else derived from input + format). |
| `-n / --n-events N`   | Convert only the first N events (default: all).          |
| `--seed N`            | RNG seed.                                                |
| `--installation NAME` | Override active installation (else env / config).        |
| `--foreground`        | Block until done instead of detaching.                   |
| `--label STR`         | Free-text label saved into the runlog.                   |

Output lands in the **same folder as the input GHEP**. Job artefacts carry a
`.<fmt>` infix so they never clobber the source run's `<stem>.log`:

```
<src_stem>.gst.root      # converted output (primary_output)
<src_stem>.gst.log       # gntpc job log (distinct from the source <src_stem>.log)
<src_stem>.gst.stdout    # gntpc stdout
<src_stem>.gst.stderr    # gntpc stderr
```

(gntpc also drops a small transient `<src_stem>.ghep.status` progress file.)

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

## Custom tunes (`--gxmlpath`)

GENIE resolves a tune by **directory name** (`G18_02a` for tune
`G18_02a_00_000`), searching each `GXMLPATH` entry first, then `$GENIE/config`.
The lookup is per-file, so you can override a single XML and inherit the rest.

To use a custom tune: copy a tune family out of `$GENIE/config/` into
`genie-agent/tunes/`, edit the XMLs, then pass the parent dir with
`--gxmlpath` on any runner:

```bash
# clone a family to edit (one-time, do it yourself)
cp -r "$GENIE/config/G18_02a" genie-agent/tunes/G18_02a
$EDITOR genie-agent/tunes/G18_02a/ModelConfiguration.xml

# run against the edited copy — GXMLPATH puts tunes/ ahead of $GENIE/config
pixi run python genie-agent/scripts/run_gmkspl.py \
    --probes numu --targets C12 --tune G18_02a_00_000 \
    --genlist CCQE -n 30 -e 3 --gxmlpath genie-agent/tunes
```

- `--gxmlpath` is repeatable and accepts colon-separated lists; all entries are
  resolved to absolute paths and **prepended** to `GXMLPATH` (earlier =
  higher priority) in the env handed to the binary. The cached env on disk is
  not modified.
- Available on `run_gmkspl.py`, `run_gevgen.py`, and `run_gntpc.py`. The
  resolved dirs are recorded in the run log under `inputs.gxmlpath`.
- Tune validation (gmkspl/gevgen) searches `--gxmlpath` dirs before
  `$GENIE/config`, so a family that exists only under `tunes/` validates fine;
  an unknown family is still rejected.
- Confirm GENIE picked up your copy: gmkspl/gevgen stdout prints
  `Tune directory ....... : …/tunes/G18_02a`.

`tunes/` is tracked in git so tune edits are versioned alongside the code.

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
  "outputs":       { "output_xml": "…", "primary_output": "…",
                     "stdout_log": "…", "stderr_log": "…", "run_dir": "…",
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
  "output_sha256": "…"
}
```

`running` / `failed` / `canceled` start as `null` and transition to
`true`/`false` as the run progresses. `returncode` is `null` until the
process exits.

## Querying run logs with `jq`

Every run is one self-contained JSON file, so `jq` over `genie-runs/*/*.log` is
the discovery story — no database, no index. The examples below assume you run
from the `genie-agent/` directory.

**One line per run** (`-c` keeps each record on its own line; `select` filters):

```bash
# everything, newest fields summarised
jq -r '[.jobid, .runtype, .returncode, .duration_s] | @tsv' genie-runs/*/*.log

# successful runs (exited 0, not still running / failed / canceled)
jq -r 'select(.returncode==0 and .running==false and (.failed|not) and (.canceled|not))
       | [.jobid, .duration_s, .outputs.primary_output] | @tsv' genie-runs/*/*.log

# failed runs (show the reason if present)
jq -r 'select(.failed==true) | [.jobid, .returncode, (.error // "-")] | @tsv' genie-runs/*/*.log

# still running
jq -r 'select(.running==true) | [.jobid, .pid, .started] | @tsv' genie-runs/*/*.log

# pending (launched but supervisor hasn't started the binary yet)
jq -r 'select(.running==null) | .jobid' genie-runs/*/*.log
```

**Filter by metadata** (resolved values live under `.inputs`):

```bash
# by runtype
jq -r 'select(.runtype=="gevgen") | .jobid' genie-runs/*/*.log

# by tune / generator list
jq -r 'select(.inputs.tune_resolved=="G18_02a_00_000") | .jobid' genie-runs/*/*.log
jq -r 'select(.inputs.genlist_resolved=="CCQE")        | .jobid' genie-runs/*/*.log

# by installation or label
jq -r 'select(.inputs.installation=="genie_rc") | .jobid' genie-runs/*/*.log
jq -r 'select(.inputs.label=="myrun")           | .jobid' genie-runs/*/*.log

# by probe/target — runners differ (gmkspl uses arrays, gevgen scalars), so
# match the stem, which always contains <probe>_<target>:
jq -r 'select(.outputs.stem | test("numu_C12")) | .jobid' genie-runs/*/*.log

# by date — the per-day folder name encodes the tune + date; or filter on .timestamp
jq -r 'select(.timestamp | startswith("2026-05-28")) | .jobid' genie-runs/*/*.log
```

**Pull out a single field or the whole record:**

```bash
# the exact GENIE command that ran
jq -r '.outputs.genie_command' genie-runs/G18_02a_00_000-2026-05-28/numu_C12_*.log

# output path + content hash for one run
jq -r '{out: .outputs.primary_output, sha: .output_sha256}' genie-runs/*/numu_C12_20260528-140326.log

# full record for a jobid (across all folders)
jq 'select(.jobid=="gevgen-numu_C12_20260528-140326-c98dcb")' genie-runs/*/*.log
```

**Tip:** pipe `@tsv` output through `column -t` for aligned tables:
`… | @tsv' genie-runs/*/*.log | column -t`.

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
    --probes numu --targets C12 \
    --tune G18_02a_00_000 --genlist CCQE -n 30 -e 5
# -> jobid: gmkspl-numu_C12_20260528-135944-8df18d

# check status (running / done / failed / canceled)
pixi run python genie-agent/scripts/job.py status \
    gmkspl-numu_C12_20260528-135944-8df18d

# once the spline is done, generate events against it
pixi run python genie-agent/scripts/run_gevgen.py \
    --probe numu --target C12 -n 100 -e 3.0 \
    --cross-sections genie-agent/genie-runs/G18_02a_00_000-2026-05-28/numu_C12_20260528-135944.xml \
    --tune G18_02a_00_000 --genlist CCQE

# cancel if needed
pixi run python genie-agent/scripts/job.py cancel \
    gmkspl-numu_C12_20260528-135944-8df18d

# see everything
pixi run python genie-agent/scripts/job.py list
```

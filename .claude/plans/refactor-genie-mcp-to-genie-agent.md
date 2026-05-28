# Refactor genie-mcp → genie-agent (Skills + runlog_tools)

## Context

`/exp/dune/data/users/liangliu/genie-fsi-prd/genie-mcp/` is a 4700-line FastMCP server registering 30 tools. Every tool change requires `pip install -e .` and a Claude Code restart. We will replace it with **Skill markdown + plain Python wrapper scripts** under `/exp/dune/data/users/liangliu/genie-dev/genie-agent/`, with **runlog_tools** capturing every command's inputs/outputs as JSON. Metadata in runlog replaces the deep `<tune>/<probe>/<target>/` tree, so the on-disk layout flattens dramatically.

**Scope this pass: local execution only** (gevgen, gmkspl, gntpc, spline download/plot, flux registry). Grid layer (~1400 lines) is deferred — it will be redesigned later as a separate general-purpose submission tool, not GENIE-specific.

## Target directory layout

```
/exp/dune/data/users/liangliu/genie-dev/genie-agent/
├── config/
│   ├── genie_env.json                   # active_installation + defaults + installations registry
│   └── env/<installation>.json          # per-installation snapshotted spack env (one file each)
├── .claude/
│   ├── skills/{genie-sim,genie-pdg,genie-tunes,genie-generator-lists,
│   │           genie-flux,genie-splines,genie-runlog,genie-jobs}/SKILL.md
│   └── commands/genie-sim.md
├── scripts/                             # one wrapper per GENIE binary + job + env tools
│   ├── run_gmkspl.py  run_gevgen.py  run_gntpc.py
│   ├── download_spline.py  plot_spline.py
│   ├── flux_list.py  flux_register.py
│   ├── refresh_genie_env.py             # rebuild config/env/<install>.json from setup_env.sh
│   ├── job.py                           # status / cancel / list background runs
│   └── query_runlogs.py
├── lib/
│   ├── genie_env.py    # snapshot_setup_script() + load_genie_env(): read JSON cache
│   ├── jobs.py         # launch_background / run_foreground / supervise / cancel_job
│   ├── config.py       # ~30-line JSON loader, merges active install over defaults
│   ├── paths.py        # new_run_dir(), run_stem(), sha256_short()
│   ├── pdg.py          # NUCLEUS_PDG / NEUTRINO_PDG / LEPTON_PDG + resolve_pdg() + canonical_*
│   ├── validation.py   # tune regex + gmkspl/gevgen input checks
│   ├── flux_index.py   # ported flux_tools (CRUD on flux_index.json)
│   └── splines/{downloader,reader,plotter}.py  # ported ~verbatim
├── data/
│   └── flux/flux_index.json
└── genie-runs/                          # all per-run artifacts + JSON logs (flat)
    └── <tune>-YYYY-MM-DD/
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.xml          # gmkspl output
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.ghep.root    # gevgen output
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.gst.root     # gntpc output
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.log          # mutable JSON job log (lib/jobs.py)
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.stdout       # GENIE binary stdout
        ├── <probe>_<target>_<YYYYMMDD-HHMMSS>.stderr       # GENIE binary stderr
        └── <probe>_<target>_<YYYYMMDD-HHMMSS>.env.json     # transient: deleted after supervisor finishes
```

**Layout rationale:**
- One per-day folder per tune (`G18_02a_00_000-2026-05-28/`, `AR23_20i_00_000-2026-05-28/`, …). All artifacts for a given tune on a given day live in one place — easy to delete/archive.
- **Flat** inside the per-day folder. The filename suffix (`.xml`, `.ghep.root`, `.log`, `.stdout`, …) already partitions artifact kinds, and `ls *.log` or `ls *.xml` is the discovery story. No `xml/` / `ghep/` / `log/` subdirs to mkdir or glob through. This matches the current `lib/paths.py:new_run_dir` (no subdir creation) and `lib/jobs.py` (writes `<stem>.log` directly in `cwd`).
- Stem is **`<probe>_<target>_<YYYYMMDD-HHMMSS>`** (e.g. `numu_Ar40_20260528-143012`) shared across the run's artifact + log + stdout + stderr. Probe/target are human-readable at a glance; timestamp guarantees ordering. The sibling `<stem>.log` JSON ties them together via stored paths and adds full metadata (jobid, genlist, n_events, seed, returncode, durations, …).
- **Probe name scheme** (used in filenames AND `lib/pdg.py` aliases) — filename-safe ASCII, no `+`/`-`:

  | Probe | PDG | Alias |
  |---|---|---|
  | electron | 11 | `eminus` |
  | positron | -11 | `eplus` |
  | muon | 13 | `muminus` |
  | antimuon | -13 | `muplus` |
  | tau | 15 | `tauminus` |
  | tau+ | -15 | `tauplus` |
  | ν_e | 12 | `nue` |
  | ν̄_e | -12 | `nuebar` |
  | ν_μ | 14 | `numu` |
  | ν̄_μ | -14 | `numubar` |
  | ν_τ | 16 | `nutau` |
  | ν̄_τ | -16 | `nutaubar` |

  `lib/pdg.py` accepts these aliases AND legacy ones (`e-`, `e+`, `mu-`, `mu+`, `tau-`, `tau+`, `electron`, `muon`, etc., from `gmkspl_tool.py:123-141`) but always **normalises to the canonical alias** above when writing paths. Charged-lepton GEM tunes need `eminus`/`eplus`-style names because `+`/`-` would break filenames on some tools.
- Discovery: `jq genie-runs/*/*.log` — eliminates `_GEVGEN_PATH_RE` (`genie_mcp/tools/gntpc_tool.py:49`).
- Concurrency note: collisions are avoided through the **jobid** (`<runtype>-<stem>-<6hex>`, see `lib/jobs.py:make_jobid`) stored inside the log JSON, not through filename suffixes. If two invocations on the same probe+target genuinely start in the same second we accept that gmkspl overwrites the second `.log`/`.xml` — easier to fix later than to bake hex suffixes into every filename. For gmkspl runs covering **multiple** probes/targets the stem joins the canonical aliases with `-` (see `lib/paths.py:run_stem`), e.g. `numu-numubar_C12-Ar40_20260528-143012`. SciSoft spline downloads are configured separately (path resolved at download time, not bundled into the repo tree).
- Plot outputs are produced separately (manual workflow) — no `png/` subdir in the per-day folder.
- For gntpc converting a GHEP into GST format, the wrapper inherits the source GHEP's tune (read from its sibling `.log`) and writes the GST under the same `<tune>-YYYY-MM-DD/gst/` folder.

## Wrapper template (used by all three GENIE binaries)

The wrapper does **not** call `RunLog` directly. Instead it builds an `inputs` and `outputs` dict, hands them to `lib.jobs.launch_background` (or `run_foreground`), and that helper writes the initial mutable JSON log and either spawns a detached supervisor or runs the binary in-process. The supervisor updates the same log file on completion. See `scripts/run_gmkspl.py` for the canonical implementation.

```python
# scripts/run_<binary>.py — shape mirrors run_gmkspl.py
from runlog_tools import make_parser, args_to_inputs
from lib.config import load_config
from lib.genie_env import load_genie_env                       # NOTE: reads config/env/<install>.json
from lib.jobs   import launch_background, run_foreground, supervise
from lib.paths  import new_run_dir, run_stem, sha256_short
from lib.pdg    import resolve_pdg, canonical_probe, canonical_target
from lib.validation import validate_gmkspl_inputs

RUNTYPE = "gmkspl"

# 1. Argparse pass-through GENIE flags + agent-side flags:
#       --installation     # override active install
#       --label            # free-text, stored in log
#       --foreground       # block instead of detach (default: detach)
#       --supervise / --log-path / --env-path   # SUPPRESS'd, used by the detached child
#
# 2. If args.supervise: hand off to lib.jobs.supervise() and return.
#    (This is how the detached child re-enters the same script.)
#
# 3. cfg = load_config(args.installation)
#    env = load_genie_env(cfg)              # reads config/env/<install>.json (no live source)
#
# 4. Resolve probes/targets via resolve_pdg + canonical_probe/target.
#    Run validate_gmkspl_inputs (or the gevgen equivalent); abort on errors,
#    print warnings.
#
# 5. now     = datetime.now()
#    run_dir = new_run_dir(tune, when=now)                     # genie-runs/<tune>-YYYY-MM-DD/
#    stem    = run_stem(canonical_probes, canonical_targets, when=now)
#
# 6. Build the GENIE command list (binary path = cfg["genie_bin_dir"] + binary name).
#
# 7. inputs  = args_to_inputs(args, exclude=("supervise","log_path","env_path","foreground")) | {
#                 "installation": cfg["installation_name"], "tune_resolved": tune, ...,
#                 "probe_pdgs": [...], "canonical_probes": [...], ...,
#                 "input_cross_sections_sha256": sha256_short(args.input_cross_sections)  # if given
#             }
#    outputs = {"output_xml": str(output_xml), "stdout_log": ..., "stderr_log": ...,
#               "run_dir": str(run_dir), "stem": stem, "warnings": warnings,
#               "genie_command": " ".join(cmd)}
#
# 8. if args.foreground:
#        return run_foreground(runtype=RUNTYPE, script=Path(__file__).resolve(),
#                              command=cmd, env=env, cwd=run_dir, stem=stem,
#                              description=desc, inputs=inputs, outputs=outputs)
#    jobid = launch_background(... same kwargs ...)
#    print(f"jobid: {jobid}"); print(f"log:   {run_dir/f'{stem}.log'}")
#    return 0
```

Per-wrapper argparse surfaces:
- `run_gmkspl.py` *(implemented)*: `--probes` `--targets` `--tune` `--genlist` `-n` (knots) `-e` (max energy) `--seed` `--input-cross-sections` `--output-file` + agent `--installation` `--label` `--foreground` + suppressed `--supervise/--log-path/--env-path` for the detached child.
- `run_gevgen.py`: `--probe` `--target` `-n` `-e` (`emin,emax` if flux) `--cross-sections` `-r` (run number) `--seed` `--tune` `--genlist` + agent `--flux-name` (resolves via `lib/flux_index.py`) `--installation` `--label` `--foreground` + suppressed supervise flags.
- `run_gntpc.py`: `-i` `-f` (default `gst`) `-o` `-n` `--seed` + `--foreground` + suppressed supervise flags. **No** `--tune/--probe/--target` derivation — metadata is read from the input GHEP's sibling `.log` and copied into the new log's `inputs.source_log`. This is the proof the regex crutch is dead.

## Skill markdown files (Claude consults these without invoking Python)

- **genie-sim** — port of `.claude/commands/genie-sim.md`, MCP tool calls swapped for `pixi run python scripts/run_*.py …`. Runs are backgrounded by default and print a `jobid`; monitor via `scripts/job.py status <jobid>` or `tail -f genie-runs/<tune>-<date>/<stem>.stdout`. Mentions `--foreground` for blocking runs.
- **genie-jobs** — the background-job model: how to read a `jobid`, `scripts/job.py status|cancel|list [--active]`, the `running/failed/canceled/returncode` tri-state fields, and the `<stem>.env.json` transient. Pairs with genie-runlog.
- **genie-pdg** — NUCLEUS_PDG / NEUTRINO_PDG / LEPTON_PDG tables from `gmkspl_tool.py:40-141` as markdown, plus the canonical-alias scheme (`eminus`/`numubar`/…) used in filenames.
- **genie-tunes** — 4-part tune regex + common tunes table + GEM-for-charged-leptons rule.
- **genie-generator-lists** — table including the **Default-is-broken-for-PYTHIA6-charm** warning and AR23/SuSAv2 8-min startup lag.
- **genie-flux** — `flux_list.py` / `flux_register.py` usage; `_PDG_TO_FLAVOUR` map; flux requires energy range.
- **genie-splines** — recipes for `download_spline.py` (cached / latest / explicit) and `plot_spline.py` (4 modes).
- **genie-runlog** — `jq` query recipes against `genie-runs/*/*.log` (find by tune, target, label, returncode, jobid, date, `running=true`).

Slash command: `.claude/commands/genie-sim.md` is the same as the skill body so `/genie-sim` works.

## Modules to port (mostly verbatim) from genie-mcp

| Source in `genie_mcp/` | Destination |
|---|---|
| `environment.py` (`build_genie_env`, `_parse_env_dump`) | **Redesigned**, not ported — `lib/genie_env.py` snapshots to `config/env/*.json` via `env -i` (see env section). The original's in-shell `source && env` leaked pixi vars. |
| `splines/downloader.py` | `lib/splines/downloader.py` (take dest_dir as arg) |
| `splines/reader.py`, `splines/plotter.py` | `lib/splines/{reader,plotter}.py` verbatim |
| `tools/flux_tools.py` | `lib/flux_index.py` (drop MCP tool wrappers, keep `resolve_flux`, `_PDG_TO_FLAVOUR`, `_load_index`/`_save_index`) |
| PDG tables + `_TUNE_RE` + `_validate_*` from `tools/gmkspl_tool.py` | `lib/pdg.py` + `lib/validation.py` |
| (none — new) | `lib/jobs.py` is **new code**, not ported. It replaces `jobs/local_manager.py`'s role with a registry-free detached-supervisor model. |

**Do not port:** `server.py`, `jobs/local_manager.py` (its registry + manager class is replaced by `lib/jobs.py`'s detached supervisor + self-describing jobids), `tools/discovery.py` (absorbed into `genie_env.py`), `setup_wizard.py`, the entire grid layer.

## Config

Single file: **`config/genie_env.json`** — multi-installation registry plus global defaults. Same shape as `genie_mcp_config.json` but stripped of grid/jobsub fields. (The snapshotted spack envs live separately, one JSON per install, under `config/env/<install>.json` — see the env section.)

```json
{
  "active_installation":    "genie_rc",
  "default_tune":           "G18_02a_00_000",
  "default_generator_list": "CCQE",
  "installations": {
    "genie_rc": {
      "genie_bin_dir":      "/exp/dune/app/users/liangliu/GENIEINCLXX/GENIE_RC/Generator/bin",
      "genie_lib_dir":      "/exp/dune/app/users/liangliu/GENIEINCLXX/GENIE_RC/Generator/lib",
      "genie_setup_script": "/exp/dune/app/users/liangliu/GENIEINCLXX/GENIE_RC/setup_env.sh"
    },
    "genie_v3_6_0":   { "...": "..." },
    "genie_incl_dev": { "...": "..." },
    "genie_v3_4_2":   { "...": "..." }
  }
}
```

Stripped fields (vs `genie_mcp_config.json`): `jobsub_bin`, `condor_q_bin`, `jobsub_q_bin`, `jobsub_rm_bin`, `jobsub_fetchlog_bin`, `default_output_dir`, `default_log_dir`, `default_group`, `python_exec`, `job_template_dir`, `cli_timeout_seconds`, `gmkspl_timeout_seconds`, `xsec_spline_dir`. Per-installation `default_tune` is dropped (lives once at the top level).

`lib/config.py` is ~30 lines:
```python
# lib/config.py
import json, os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]   # genie-agent/

def load_config(installation: str | None = None) -> dict:
    cfg = json.loads((_ROOT / "config" / "genie_env.json").read_text())

    name = installation or os.environ.get("GENIE_AGENT_INSTALLATION") or cfg["active_installation"]
    if name not in cfg["installations"]:
        raise KeyError(f"installation '{name}' not found in config/genie_env.json")

    # merge: install-specific paths override globals if any keys collide
    merged = {k: v for k, v in cfg.items() if k != "installations"}
    merged.update(cfg["installations"][name])
    merged["installation_name"] = name
    return merged
```

Precedence for `active_installation`: `--installation` flag → `GENIE_AGENT_INSTALLATION` env → top-level `active_installation` in `config/genie_env.json`. (Implemented in `lib/config.py`.)

## Detailed: `lib/genie_env.py` — GENIE environment as a persisted JSON snapshot

**What it does.** GENIE binaries need the spack env from each installation's `setup_env.sh` (which itself sources `nuisance`/`nusystematics`). genie-agent runs inside pixi, so a naïve `bash -c "source setup_env.sh && env"` from within the agent leaks pixi vars (`PIXI_*`, `CONDA_*`, `PYTHONHOME`, `PYTHONPATH`, …) into the GENIE child env and breaks the binaries. We sidestep this with two pieces:

1. **Snapshot once, per installation, to `config/env/<installation_name>.json`** using `snapshot_setup_script()`, which runs the source step in a *parent-env-stripped* shell:
   ```
   env -i HOME=… USER=… TERM=… bash --noprofile --norc -c "source <setup> && env -0"
   ```
   The `env -0` output is parsed with NUL separators, then filtered by `_scrub()` to drop denylisted keys (`PIXI_`, `CONDA_`, `MAMBA_`, `_CE_`, `VIRTUAL_ENV`, `BASH_FUNC_*`, exact `PYTHONHOME`/`PYTHONPATH`) and the three bootstrap vars themselves. The result is sorted, atomically written, and includes `$GENIE` (else the snapshot is refused).
2. **At runtime, `load_genie_env(cfg)` reads the JSON cache file** and returns the dict for the active installation. The JSON file is the source of truth — inspectable with `jq`, version-controllable, and decoupled from whatever pixi/conda state happens to be loaded when the wrapper is invoked. There is also an in-process dict cache (`_CACHE` keyed by installation name) so a single Python process pays one file-read per install.

**Staleness check.** If `config/env/<install>.json` is older than the installation's `setup_env.sh`, `load_genie_env` logs a warning naming the exact refresh command. If the JSON file is missing entirely, `load_genie_env` takes a live snapshot **but does not persist it** — that's deliberate: writing back from inside a pixi shell is exactly what we're avoiding. The wrapper still works; the user gets a loud nudge to run the refresh script.

**Refreshing.** `scripts/refresh_genie_env.py`:
```bash
pixi run python scripts/refresh_genie_env.py --installation genie_rc
pixi run python scripts/refresh_genie_env.py --all
pixi run python scripts/refresh_genie_env.py             # active install
```
This is the *only* path that writes `config/env/*.json`. It also runs inside pixi but uses `env -i` internally, so the snapshot is still clean. Re-run after editing any installation's `setup_env.sh` (or whenever GENIE is rebuilt under a different toolchain).

**Public API**:
- `snapshot_setup_script(setup_script: str, timeout: int = 120) -> dict[str, str]` — pure function; raises on bad setup or missing `$GENIE`.
- `load_genie_env(cfg: dict) -> dict[str, str]` — wrappers call this; signature changed from the original plan (was `build_genie_env(setup_script)`).
- `write_env_file(installation_name, env) -> Path` — atomic write to `config/env/<name>.json`.
- `env_file_for(installation_name) -> Path` — pure path helper.
- `reset_env_cache()` — clear the in-process dict cache (tests only).

**Why this differs from the original plan.** The first plan called `build_genie_env(cfg["genie_setup_script"])` and cached only in memory. That works in isolation but leaks pixi vars whenever the wrapper itself runs under pixi (which is *every* invocation in practice). Snapshotting to JSON with `env -i` is the fix; the in-memory cache survives as a secondary speedup.

**Caller pattern** (matches `scripts/run_gmkspl.py:84-85`):
```python
from lib.config import load_config
from lib.genie_env import load_genie_env

cfg = load_config(args.installation)   # merged dict including installation_name
env = load_genie_env(cfg)              # reads config/env/<install>.json
subprocess.run([cfg["genie_bin_dir"] + "/gmkspl", ...], env=env, ...)
```

**Verification.** Smoke test after `refresh_genie_env.py` runs:
```bash
pixi run python -c "
from lib.config import load_config
from lib.genie_env import load_genie_env
env = load_genie_env(load_config())
print('GENIE         =', env['GENIE'])
print('XSECSPLINEDIR =', env.get('XSECSPLINEDIR', '<unset>'))
print('PATH head     =', env['PATH'].split(':')[0])
print('pixi leaked?  =', any(k.startswith(('PIXI_','CONDA_')) for k in env))
"
```
Expected: `pixi leaked? = False`, `GENIE` matches the install's `genie_bin_dir/..`, `PATH` starts with the GENIE bin dir, `LD_LIBRARY_PATH` contains the GENIE lib dir.

## Run metadata: `<stem>.log` as a mutable JSON job record

`runlog_tools.RunLog` is a *write-once-on-exit* context manager — it only writes the JSON when the `with`-block ends. That model doesn't fit detached background jobs, where the wrapper exits immediately (jobid returned to Claude) and the supervisor finishes minutes later. So genie-agent does **not** use `RunLog` as the log writer. Instead `lib/jobs.py` owns the schema and lifecycle directly, and the wrappers borrow `runlog_tools` only for `make_parser`/`args_to_inputs`.

**Schema** — fields written by `make_initial_log` in `lib/jobs.py:104-138`, updated by the supervisor on completion:

| Field | Written by | Notes |
|---|---|---|
| `jobid` | launcher | `<runtype>-<stem>-<6hex>`, decodable without a registry |
| `runtype` | launcher | `"gmkspl"`, `"gevgen"`, `"gntpc"`, … |
| `script` | launcher | relative path under genie-agent/, falls back to absolute |
| `script_path` | launcher | absolute |
| `script_sha256` | launcher | first 16 hex chars |
| `git_sha` | launcher | `git -C <agent_root> rev-parse HEAD`, or null |
| `cwd` | launcher | the run_dir |
| `command` | launcher | argv list of the GENIE binary |
| `description` | launcher | human one-liner (e.g. `"gmkspl numu on Ar40 [G18_02a_00_000/CCQE]"`) |
| `inputs` | launcher | argparse pass-through + resolved PDGs/aliases + sha256 of input XML |
| `outputs` | launcher | `output_xml`, `stdout_log`, `stderr_log`, `run_dir`, `stem`, `warnings`, `genie_command` |
| `timestamp` | launcher | UTC ISO, when the log was written (≠ `started`) |
| `started` / `finished` | supervisor | UTC ISO; null until supervisor begins/ends |
| `duration_s` | supervisor | monotonic wall time, 3 decimals |
| `pid` | supervisor | child PID, for cancel/reconcile |
| `running` / `failed` / `canceled` | tri-state | null = not yet started, true/false = decided |
| `returncode` | supervisor | int; -15 on cancel-without-rc, -1 on spawn failure |
| `output_xml_sha256` | supervisor | first 16 hex of the output artifact, when present |
| `error` | on failure | `"failed to spawn child: …"` or `"supervisor lost (pid not alive)"` |

**Why mutable JSON, not RunLog.** The launcher needs to write a complete record (with jobid and resolved inputs) *before* the supervisor has any results, so that Claude/the user immediately has a discoverable artifact: `jq genie-runs/*/*.log` already shows the job exists, what it was about, and that `running=null`. The supervisor then transitions `running: null → true → false` and fills in `started`/`finished`/`returncode`. All updates are atomic via `atomic_write_json` (temp + `os.replace`). The `reconcile_log` helper handles the lost-supervisor case: if `running=true` but the PID is dead, mark failed with `error="supervisor lost"`.

**Inputs/outputs content.** `args_to_inputs(args, exclude=("supervise","log_path","env_path","foreground"))` strips internal flags from the namespace, then the wrapper merges in resolved metadata so the log captures **what was actually run**, not just what was typed: `installation` (post-merge name), `tune_resolved`, `genlist_resolved`, `probe_pdgs`/`canonical_probes`, `target_pdgs`/`canonical_targets`, and `input_cross_sections_sha256` for any pre-existing XML the user fed in. The validation step's `warnings` list also lands in `outputs` so the log records the advisories the run was launched despite.

**gntpc reads the previous log instead of regex'ing the path.** When `run_gntpc.py -i some.ghep.root` runs, it loads the sibling `some.ghep.root`'s `.log` (same stem), reads `inputs.tune_resolved` / `inputs.canonical_probes` / `inputs.canonical_targets`, and stores them under `inputs.source_log = "<path>"` plus the inherited fields. This is the concrete proof that the metadata-driven approach kills `_GEVGEN_PATH_RE`.

## Background jobs: detached supervisor + foreground opt-in

GENIE binaries can take minutes (gmkspl) to hours (gevgen with large `-n`). The MCP server used a `local_manager.py` with a registry file; we replace it with a much simpler **detached supervisor** pattern in `lib/jobs.py` — no registry, jobids decode themselves, status lives entirely in the per-job `<stem>.log`.

**Default = background.** Every wrapper calls `launch_background(...)` by default. The launcher:
1. Writes the initial `<stem>.log` (synchronous, atomic).
2. Writes `<stem>.env.json` next to it (the snapshotted env dict, so the child doesn't need to re-source).
3. Spawns the same wrapper script with `--supervise --log-path … --env-path …` via `subprocess.Popen(start_new_session=True, stdin/out/err = DEVNULL, close_fds=True)`. This is the standard double-fork-via-setsid approach: the supervisor survives the parent exiting, its own stdio is detached.
4. Returns the jobid to stdout. Claude/the user picks it up and uses `scripts/job.py status <jobid>` / `cancel <jobid>` / `list`.

**Foreground opt-in.** `--foreground` skips the Popen+detach step and calls `_supervise_impl` in-process, blocking until completion. Useful for tests, smoke runs, and CI. Both paths write the **same** schema, so consumers don't branch.

**Supervisor lifecycle** (`_supervise_impl` at `lib/jobs.py:220-304`):
1. Read the initial log, open `stdout_log`/`stderr_log` files (or DEVNULL).
2. `Popen(command, env=env, cwd=run_dir, stdout=…, stderr=…)`.
3. Atomic-update the log: `running=true, pid=child.pid, started=<utc>`.
4. Install `SIGTERM`/`SIGINT` handlers that set `canceled=True` and `child.terminate()`.
5. `child.wait()`. On cancel, escalate to `kill()` after 2 s.
6. Atomic-update the log: `running=false, failed=(rc!=0 and not canceled), canceled=…, returncode=rc, finished=<utc>, duration_s=…, output_xml_sha256=…`.

**Why ship the env as `<stem>.env.json`.** The detached child cannot inherit the parent's env (we want pixi vars *out*, and even if we passed them via env=, the supervisor would need to know which env to pass to the *grandchild* GENIE binary). The cleanest answer is: the launcher already has the right dict (from `load_genie_env`), so it dumps it to JSON next to the log and the supervisor reads it back. The supervisor deletes this file in `supervise()`'s `finally`, so it's transient — never accumulates in the run dir.

**Jobid format.** `<runtype>-<stem>-<6hex>` (`make_jobid`). `parse_jobid` splits on `-` from both ends. `find_log_for_jobid` globs `genie-runs/*/<stem>.log` and matches the embedded `jobid` field — no registry file, no race. The 6 hex characters disambiguate the case where the same stem appears in two folders (e.g. same probe+target+second across two tunes on different days, or rerun within a second).

**`scripts/job.py` surface** (already implemented):
- `status <jobid>` — calls `reconcile_log` (detects lost supervisors) and prints the summary fields.
- `cancel <jobid>` — sends SIGTERM to the supervisor's process group, escalates to SIGKILL after 2 s, marks `canceled=True, returncode=-15`.
- `list [--active]` — walks `genie-runs/*/*.log`, prints a state/jobid/pid/started/rc table.

## runlog_tools — minimal patches

The original plan called for adding a `log_basename=` kwarg to `RunLog`. With the mutable-log design above, the wrappers no longer use `RunLog` as the log writer, so that change is no longer needed. The remaining patch is just hygiene:

1. **Fix stale `feanor_tools` docstring** in `runlog_tools/runlog_tools/__init__.py:2` and `runlog_tools/runlog_tools/run_log.py:15` (the example still imports `from feanor_tools import RunLog`).

`runlog_tools` is still pulled in by every wrapper for `make_parser` and `args_to_inputs` (sensible argparse defaults + namespace-to-dict conversion).

## Migration order (smallest vertical slice first)

**Status:** steps 1–4 are **done** — `config/genie_env.json`, `lib/{config,genie_env,paths,pdg,validation,jobs}.py`, `scripts/{run_gmkspl,refresh_genie_env,job}.py` exist. Remaining: steps 5–9.

1. ✅ Scaffold directory tree; copy + strip `genie_mcp/config/genie_mcp_config.json` into `config/genie_env.json`.
2. ✅ `lib/config.py`, `lib/paths.py`, `lib/pdg.py`, `lib/validation.py`, plus the **redesigned** `lib/genie_env.py` (snapshot-to-JSON) and **new** `lib/jobs.py` (detached supervisor). Snapshot the active env first: `pixi run python scripts/refresh_genie_env.py --all`, then smoke-test `print(load_genie_env(load_config())["GENIE"])`.
3. ✅ **`scripts/run_gmkspl.py`** first (slowest binary → timing field meaningful, richest validation, output feeds next two). Background path: `--probes numu --targets H1 --tune G18_02a_00_000 --genlist CCQE -n 30 -e 5` prints a jobid; poll `scripts/job.py status <jobid>`. Add `--foreground` to block.
4. ✅ `scripts/job.py` (`status`/`cancel`/`list`) — the read/control surface for backgrounded runs.
5. `.claude/skills/{genie-runlog,genie-jobs}/SKILL.md` — `jq` recipes + the job-control workflow so Claude can query and steer the first wrapper's outputs.
6. `scripts/run_gevgen.py` (uses #3's XML; same launch_background/run_foreground shape).
7. `scripts/run_gntpc.py` — reads the input GHEP's sibling `.log` for tune/probe/target; proves the metadata-driven approach kills `_GEVGEN_PATH_RE`.
8. `scripts/download_spline.py`, `scripts/plot_spline.py`.
9. `scripts/flux_list.py`, `scripts/flux_register.py`; copy `flux_index.json` verbatim.
10. Remaining `SKILL.md` files + `commands/genie-sim.md`; fix the stale `feanor_tools` docstring in `runlog_tools`.

## Verification — end-to-end test after step 9

```bash
pixi run python scripts/refresh_genie_env.py --all          # snapshot every install's env first
pixi run python scripts/download_spline.py --tune G18_02a_00_000 --version latest
# gevgen + gntpc are backgrounded by default; --foreground here so the test blocks:
pixi run python scripts/run_gevgen.py --probe numu --target C12 -n 100 -e 3.0 \
    --cross-sections <downloaded-spline-xml-path> \
    --tune G18_02a_00_000 --genlist CCQE --foreground
pixi run python scripts/run_gntpc.py -i <ghep_path> -f gst --foreground   # no --tune / --probe / --target
pixi run python scripts/plot_spline.py --plot-mode channels --neutrino numu --target C12
pixi run python scripts/job.py list                          # all runs, with state + returncode
jq -r '[.runtype, .outputs.stem, .returncode, .duration_s] | @tsv' genie-runs/*/*.log
```

Expect `.log` files (flat, not under `log/`) plus matching ghep + gst artifacts under `genie-runs/<tune>-<date>/`, each independently `jq`-queryable, each with `running=false` and a real `returncode`. Background-path check: launch a gmkspl run *without* `--foreground`, confirm the wrapper returns a jobid immediately, then `scripts/job.py status <jobid>` shows `running=true → false`. Parity check vs MCP: pick a past gmkspl/gevgen/gntpc invocation, re-run via the new wrapper, `diff` event counts and ROOT file sizes — should match bit-for-bit.

## Critical files

- `lib/genie_env.py` — redesigned (not ported from `environment.py`); reference only: `genie-fsi-prd/genie-mcp/genie_mcp/environment.py`
- `lib/jobs.py` — new code (no MCP source); replaces `genie_mcp/jobs/local_manager.py`'s role
- PDG + validation + arg shape: `genie-fsi-prd/genie-mcp/genie_mcp/tools/gmkspl_tool.py`, `gevgen_tool.py`, `gntpc_tool.py`
- Spline modules: `genie-fsi-prd/genie-mcp/genie_mcp/splines/{downloader,reader,plotter}.py`
- Flux registry: `genie-fsi-prd/genie-mcp/genie_mcp/tools/flux_tools.py`
- runlog_tools docstring fix target: `genie-dev/runlog_tools/runlog_tools/{run_log.py,__init__.py}`
- Workflow narrative source: `genie-fsi-prd/genie-mcp/.claude/commands/genie-sim.md`

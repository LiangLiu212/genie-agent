# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`genie-agent/` holds plain-Python CLI runners for GENIE neutrino-MC binaries
(`gmkspl`, `gevgen`, `gntpc`). It is a refactor of a 4700-line FastMCP server
(`genie-mcp`, in the sibling repo `../genie-fsi-prd/`) into Skill markdown +
wrapper scripts. The migration plan lives at
`.claude/plans/refactor-genie-mcp-to-genie-agent.md` and is the source of truth
for intent; update it when the design changes. `runlog_tools/` is a vendored
helper package (only `make_parser` / `args_to_inputs` are used here).

## Running things

**Always invoke through pixi** — `pixi run python …`. Bare `python3` on this host
is too old (3.9-mixed) and crashes importing `runlog_tools` (`str | None` is
evaluated at import time). The pixi env pins Python 3.14 + `jq`.

```bash
# one-time per installation: snapshot its spack env (see "Two environments")
pixi run python genie-agent/scripts/refresh_genie_env.py --all

# runners — backgrounded by default (print a jobid), --foreground to block
pixi run python genie-agent/scripts/run_gmkspl.py --probes numu --targets C12 \
    --tune G18_02a_00_000 --genlist CCQE -n 30 -e 5
pixi run python genie-agent/scripts/run_gevgen.py --probe numu --target C12 \
    -n 100 -e 3.0 --cross-sections <abs/spline.xml> --tune G18_02a_00_000 --genlist CCQE
pixi run python genie-agent/scripts/run_gntpc.py -i <abs/events.ghep.root> -f gst

# job control + log queries
pixi run python genie-agent/scripts/job.py status|cancel|list [--active] <jobid>
jq -r '[.jobid,.runtype,.returncode,.duration_s]|@tsv' genie-agent/genie-runs/*/*.log
```

There is **no test suite, linter, or build step**. "Verification" means a real
foreground run that exits 0 and produces the expected artefact — e.g. gmkspl on
`C12` (not free `H1`, which has no bound neutron and writes an empty spline list
despite `returncode==0`; the launcher warns and `outputs.spline_count==0` flags
it). gevgen needs an existing spline XML; gntpc needs a GHEP.

## Architecture

### Two environments, deliberately separated
The agent runs under **pixi**; the GENIE binaries need a **spack** env from each
installation's `setup_env.sh`. Sourcing that script from inside pixi leaks
`PIXI_*`/`CONDA_*`/`PYTHONHOME`/… into the GENIE child and breaks it. So
`scripts/refresh_genie_env.py` snapshots each install's env **once** in a
parent-stripped shell (`env -i … bash --noprofile --norc -c "source <script> && env -0"`),
scrubs the leaked vars, and writes `config/env/<installation>.json`. At runtime
`lib/genie_env.py::load_genie_env(cfg)` just reads that JSON and hands the dict
to the binary as `env=`. If the snapshot is missing it warns and takes a live
(non-persisted) snapshot; if stale (older than `setup_env.sh`) it warns. **Edit
the env contract only in `lib/genie_env.py`, and re-run `refresh_genie_env.py`
after any `setup_env.sh` change.**

### The three runners share one shape
`run_gmkspl.py`, `run_gevgen.py`, `run_gntpc.py` are near-identical:
parse args → `load_config(args.installation)` → `load_genie_env(cfg)` →
resolve PDGs/aliases (`lib/pdg.py`) → validate (`lib/validation.py`) →
build the GENIE argv → `run_foreground(...)` if `--foreground` else
`launch_background(...)`. When adding a runner, copy this skeleton; don't invent
a new control flow. Each also carries hidden `--supervise/--log-path/--env-path`
flags — that's the detached child re-entering the same script (see below); never
call them by hand.

### Background jobs (`lib/jobs.py`) — no registry, mutable log
Default is background. `launch_background` writes the initial `<stem>.log`,
dumps the env to a transient `<stem>.env.json`, then `Popen`s the *same script*
with `--supervise` under `start_new_session=True`. The detached supervisor execs
the binary, then atomically rewrites the log (`running: null→true→false`,
`returncode`, `duration_s`, `output_sha256`). A **jobid** is
`<runtype>-<stem>-<6hex>` and decodes itself — `find_log_for_jobid` globs
`genie-runs/*/<stem>.log` and matches the embedded jobid, so there is no registry
file. `reconcile_log` recovers lost supervisors (pid dead but `running:true`).
`run_foreground` runs the same supervisor logic in-process; both paths write the
identical schema.

### Metadata lives in the log, not in paths
The on-disk layout is flat: `genie-runs/<tune>-YYYY-MM-DD/<stem>.{xml,ghep.root,gst.root,log,stdout,stderr}`,
stem = `<probe>_<target>_<YYYYMMDD-HHMMSS>-<3hex>` (the 3-hex uniquifier keeps
same-second runs from clobbering each other; nothing parses the stem back).
Discovery is `jq` over `*.log` (see the `genie-runlog` skill). Resolved facts
(tune, genlist, canonical probe/target, installation, gxmlpath, input hashes)
go in `inputs`, plus the **reproducibility fingerprints**: a materialized
`seed` (never null), `tune_xml_sha256` (per-file hashes of the resolved tune
family), `env_sha256`, `genie_bin_sha256`, `genie_install_git`
({sha,branch,dirty} of the install checkout — captures install-level
config+data like SpectralFunc param_sets); top level carries `git_sha` +
`git_dirty`. Paths + `genie_command` go in `outputs`; `outputs.primary_output`
is the one file the supervisor hashes into `output_sha256`, and successful
gmkspl runs also record `outputs.spline_count` (0 = empty spline list).
Replay-without-the-LLM: re-running the logged command with the logged seed
reproduces the events exactly (compare gst content, not .ghep.root bytes —
ROOT headers embed timestamps). `scripts/build_run_manifest.py` projects all
local+grid records into the git-tracked `run-manifest.jsonl`. Crucially,
**gntpc reads the input GHEP's sibling `.log`** for tune/probe/target instead
of parsing the path — this killed the old `_GEVGEN_PATH_RE` regex. gntpc's job
artefacts use a `.<fmt>` infix (`<stem>.gst.log`) so they never clobber the
source run's `<stem>.log`.

### Paths handed to GENIE must be absolute
The supervisor runs the binary with `cwd=run_dir`, so any user-supplied path
(`--cross-sections`, `--input-cross-sections`, gntpc `-i`) is `Path(...).resolve()`d
before going into the argv — a relative path would resolve against the wrong dir
and GENIE would report "file does not exist".

### Custom tunes via `--gxmlpath`
GENIE resolves a tune by directory name (`G18_02a` ← `G18_02a_00_000`), searching
each `GXMLPATH` entry before `$GENIE/config`. Copy a family into
`genie-agent/tunes/` (git-tracked), edit, and pass `--gxmlpath genie-agent/tunes`.
`lib/genie_env.py::with_gxmlpath` prepends the resolved dirs to `GXMLPATH` in a
**copy** of the env (never mutate the process-cached dict), and
`lib/validation.py::_tune_family_dir` searches those dirs before `$GENIE/config`
so a family present only under `tunes/` still validates.

### Config (`lib/config.py`)
`config/genie_env.json` = top-level defaults (`active_installation`,
`default_tune`, `default_generator_list`) + an `installations` registry. `load_config`
merges the chosen install over the defaults; precedence is `--installation` flag →
`$GENIE_AGENT_INSTALLATION` → `active_installation`.

### Shared PDG data (`../shared/pdg.json`)
`lib/pdg.py` does **not** hardcode tables — it reads the repo-shared
`shared/pdg.json` (one dir up from `genie-agent/`), so a future sibling
`jobsub-agent/` resolves PDGs from the same source. The JSON is generated by
`shared/build_pdg.py` (build-time only; needs the `pdg` PyPI dep in `pixi.toml`),
which **combines** GENIE's `genie_pdg_table*.txt` (names+codes GENIE uses) with
the PDG API (`pdg.connect()` — validates codes, adds canonical name/mass).
Nuclei aren't enumerated by either source: `lib/pdg.py` resolves any `<Sym><A>`
(e.g. `Ar40`) at runtime by formula `1000000000+Z*10000+A*10` from the embedded
element→Z table. Runtime reads only the JSON (no `pdg` import). Regenerate after
a GENIE table change: `pixi run python shared/build_pdg.py`.

## Repo conventions
- `config/` and `genie-runs/` are gitignored (machine-specific paths, snapshotted
  envs, generated artefacts). `genie-agent/tunes/` **is** tracked.
- Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
  Branch + commit/push only when asked.
- Skills under `.claude/skills/` (e.g. `genie-runlog`) document workflows for
  future sessions; keep them in sync when behaviour changes.

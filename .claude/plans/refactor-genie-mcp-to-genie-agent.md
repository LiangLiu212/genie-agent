# Refactor genie-mcp → genie-agent (Skills + runlog_tools)

## Context

`/exp/dune/data/users/liangliu/genie-fsi-prd/genie-mcp/` is a 4700-line FastMCP server registering 30 tools. Every tool change requires `pip install -e .` and a Claude Code restart. We will replace it with **Skill markdown + plain Python wrapper scripts** under `/exp/dune/data/users/liangliu/genie-dev/genie-agent/`, with **runlog_tools** capturing every command's inputs/outputs as JSON. Metadata in runlog replaces the deep `<tune>/<probe>/<target>/` tree, so the on-disk layout flattens dramatically.

**Scope this pass: local execution only** (gevgen, gmkspl, gntpc, spline download/plot, flux registry). Grid layer (~1400 lines) is deferred — it will be redesigned later as a separate general-purpose submission tool, not GENIE-specific.

## Target directory layout

```
/exp/dune/data/users/liangliu/genie-dev/genie-agent/
├── config.json                          # active_installation + installations
├── .claude/
│   ├── skills/{genie-sim,genie-pdg,genie-tunes,genie-generator-lists,
│   │           genie-flux,genie-splines,genie-runlog}/SKILL.md
│   └── commands/genie-sim.md
├── scripts/                             # one wrapper per GENIE binary
│   ├── run_gmkspl.py  run_gevgen.py  run_gntpc.py
│   ├── download_spline.py  plot_spline.py
│   ├── flux_list.py  flux_register.py
│   └── query_runlogs.py
├── lib/
│   ├── genie_env.py    # bash -c "source setup-env.sh && env" → dict, cached
│   ├── config.py       # ~30-line JSON loader, merges active install over defaults
│   ├── paths.py        # new_run_dir(), next_run_id(), sha256_short()
│   ├── pdg.py          # NUCLEUS_PDG / NEUTRINO_PDG / LEPTON_PDG + resolve_pdg()
│   ├── validation.py   # tune regex + gmkspl/gevgen input checks
│   ├── flux_index.py   # ported flux_tools (CRUD on flux_index.json)
│   └── splines/{downloader,reader,plotter}.py  # ported ~verbatim
├── data/
│   └── flux/flux_index.json
└── genie-runs/                          # all per-run artifacts + JSON logs
    └── <run-type>-YYYY-MM-DD/
        ├── xml/<tune>-<YYYYMMDD-HHMMSS>.xml          # gmkspl output
        ├── ghep/<tune>-<YYYYMMDD-HHMMSS>.ghep.root   # gevgen output
        ├── gst/<tune>-<YYYYMMDD-HHMMSS>.gst.root     # gntpc output (or rootracker/, etc.)
        ├── log/<tune>-<YYYYMMDD-HHMMSS>.log          # RunLog JSON (metadata)
        ├── stdout/<tune>-<YYYYMMDD-HHMMSS>.stdout
        └── stderr/<tune>-<YYYYMMDD-HHMMSS>.stderr
```

**Layout rationale:**
- One per-day folder per run-type (`gmkspl-2026-05-28/`, `gevgen-2026-05-28/`, …).
- Inside, type subdirs (`xml/`, `ghep/`, `gst/`, `log/`, `stdout/`, `stderr/`) keep one `ls` per artifact kind.
- Stem is **`<full-tune-name>-<YYYYMMDD-HHMMSS>`** (e.g. `G18_02a_00_000-20260528-143012`) shared across the run's artifact + log + stdout + stderr. Tune name is human-readable at a glance; timestamp guarantees ordering. The `log/<stem>.log` JSON ties them together via stored paths.
- Discovery: `jq genie-runs/*/log/*.log` — eliminates `_GEVGEN_PATH_RE` (`genie_mcp/tools/gntpc_tool.py:49`).
- Concurrency note: if two invocations of the same binary + tune start in the same second, append `-<2hex>` to the stem to disambiguate. SciSoft spline downloads are configured separately (path resolved at download time, not bundled into the repo tree).
- Plot outputs are produced separately (manual workflow) — no `png/` subdir in the per-day folder.

## Wrapper template (used by all three GENIE binaries)

```python
# scripts/run_<binary>.py
from runlog_tools import RunLog, make_parser, args_to_inputs
from lib.config import load_config
from lib.genie_env import build_genie_env
from lib.paths import new_run_dir, sha256_short
from lib.pdg import resolve_pdg

# 1. parse args (pass-through GENIE flags + agent-side: --installation, --label)
# 2. cfg = load_config(args.installation); env = build_genie_env(cfg["genie_setup_script"])
# 3. run_dir, rid = new_run_dir("gmkspl");  stem = f"gmkspl-{rid}-{secrets.token_hex(4)}"
# 4. os.environ["RUNLOG_LOG_ROOT"] = str(run_dir)
# 5. with RunLog(__file__, "...", inputs=args_to_inputs(args) | {...resolved PDGs, sha256s...}) as log:
#       log.out("genie_command", " ".join(cmd))
#       rc = subprocess.run(cmd, env=env,
#                           stdout=open(stem+".stdout","wb"),
#                           stderr=open(stem+".stderr","wb")).returncode
#       log.out({"returncode": rc, "run_id": rid, "output_xml": ..., "stdout_log": ...})
```

Per-wrapper argparse surfaces:
- `run_gmkspl.py`: `--probes` `--targets` `--tune` `--genlist` `-n` (knots) `-e` (max energy) `--seed` `--input-cross-sections` `--output-file` + agent `--installation` `--label`.
- `run_gevgen.py`: `--probe` `--target` `-n` `-e` (`emin,emax` if flux) `--cross-sections` `-r` (run number) `--seed` `--tune` `--genlist` + agent `--flux-name` (resolves via `lib/flux_index.py`) `--installation` `--label`.
- `run_gntpc.py`: `-i` `-f` (default `gst`) `-o` `-n` `--seed`. **No** `--tune/--probe/--target` derivation — metadata is in the input's sibling `.log` file. This is the proof the regex crutch is dead.

## Skill markdown files (Claude consults these without invoking Python)

- **genie-sim** — port of `.claude/commands/genie-sim.md`, MCP tool calls swapped for `pixi run python scripts/run_*.py …`, monitor via `tail -f genie-runs/.../*.stdout`.
- **genie-pdg** — NUCLEUS_PDG / NEUTRINO_PDG / LEPTON_PDG tables from `gmkspl_tool.py:40-141` as markdown.
- **genie-tunes** — 4-part tune regex + common tunes table + GEM-for-charged-leptons rule.
- **genie-generator-lists** — table including the **Default-is-broken-for-PYTHIA6-charm** warning and AR23/SuSAv2 8-min startup lag.
- **genie-flux** — `flux_list.py` / `flux_register.py` usage; `_PDG_TO_FLAVOUR` map; flux requires energy range.
- **genie-splines** — recipes for `download_spline.py` (cached / latest / explicit) and `plot_spline.py` (4 modes).
- **genie-runlog** — `jq` query recipes against `genie-runs/*/*.log` (find by tune, target, label, returncode, date).

Slash command: `.claude/commands/genie-sim.md` is the same as the skill body so `/genie-sim` works.

## Modules to port (mostly verbatim) from genie-mcp

| Source in `genie_mcp/` | Destination |
|---|---|
| `environment.py` (`build_genie_env`, `_parse_env_dump`) | `lib/genie_env.py` (drop dataclass dep) |
| `splines/downloader.py` | `lib/splines/downloader.py` (take dest_dir as arg) |
| `splines/reader.py`, `splines/plotter.py` | `lib/splines/{reader,plotter}.py` verbatim |
| `tools/flux_tools.py` | `lib/flux_index.py` (drop MCP tool wrappers, keep `resolve_flux`, `_PDG_TO_FLAVOUR`, `_load_index`/`_save_index`) |
| PDG tables + `_TUNE_RE` + `_validate_*` from `tools/gmkspl_tool.py` | `lib/pdg.py` + `lib/validation.py` |

**Do not port:** `server.py`, `jobs/local_manager.py` (replaced by foreground subprocess + RunLog), `tools/discovery.py` (absorbed into `genie_env.py`), `setup_wizard.py`, the entire grid layer.

## Config

`genie-agent/config.json` — multi-installation shape from `genie_mcp_config.json`, stripped of `jobsub_*`, `condor_*`, `default_output_dir`, `default_log_dir`, `cli_timeout_seconds`, `gmkspl_timeout_seconds`, `job_template_dir`, `python_exec`, `default_group`. Each installation entry keeps `genie_bin_dir`, `genie_setup_script`, `default_tune`. Top-level keeps `active_installation`, `default_tune`, `default_generator_list`. `lib/config.py` resolves `--installation` flag → `GENIE_AGENT_INSTALLATION` env → `active_installation`.

## runlog_tools — minimal patches

1. **Add `log_basename=` kwarg** to `RunLog.__init__` (3-line change in `__exit__`) so the wrapper can name the log `<stem>.log` alongside the artifact. Without this we'd have to rename post-write, which races on concurrent invocations.
2. **Fix stale `feanor_tools` docstring** in `runlog_tools/__init__.py:2` and `runlog_tools/run_log.py`.

**Not adding:** `runlog run` CLI (user declined), built-in subprocess capture, built-in input-file hashing — all five lines in the wrapper.

## Migration order (smallest vertical slice first)

1. Scaffold directory tree; copy + strip `config.json` from `genie_mcp/config/genie_mcp_config.json`.
2. Port `lib/genie_env.py`, `lib/config.py`, `lib/paths.py`, `lib/pdg.py`, `lib/validation.py`. Smoke-test: `print(build_genie_env(load_config()["genie_setup_script"])["GENIE"])`.
3. **`scripts/run_gmkspl.py`** first (slowest binary → timing field meaningful, richest validation, output feeds next two). Verify with `--probes numu --targets H1 --tune G18_02a_00_000 --genlist CCQE -n 30 -e 5`.
4. `.claude/skills/genie-runlog/SKILL.md` — `jq` recipes so Claude can query the first wrapper's outputs.
5. `scripts/run_gevgen.py` (uses #3's XML).
6. `scripts/run_gntpc.py` — proves the metadata-driven approach kills `_GEVGEN_PATH_RE`.
7. `scripts/download_spline.py`, `scripts/plot_spline.py`.
8. `scripts/flux_list.py`, `scripts/flux_register.py`; copy `flux_index.json` verbatim.
9. All seven `SKILL.md` files + `commands/genie-sim.md`.
10. Patch `runlog_tools` (`log_basename=` kwarg + docstring).

## Verification — end-to-end test after step 8

```bash
pixi run python scripts/download_spline.py --tune G18_02a_00_000 --version latest
pixi run python scripts/run_gevgen.py --probe numu --target C12 -n 100 -e 3.0 \
    --cross-sections <downloaded-spline-xml-path> \
    --tune G18_02a_00_000 --genlist CCQE
pixi run python scripts/run_gntpc.py -i <ghep_path> -f gst        # no --tune / --probe / --target
pixi run python scripts/plot_spline.py --plot-mode channels --neutrino numu --target C12
jq -r '[.script, .outputs.returncode, .duration_s] | @tsv' genie-runs/*/log/*.log
```

Expect four `.log` files plus matching ghep + gst artifacts under `genie-runs/`, each independently `jq`-queryable. Parity check vs MCP: pick a past gmkspl/gevgen/gntpc invocation, re-run via the new wrapper, `diff` event counts and ROOT file sizes — should match bit-for-bit.

## Critical files

- Source for `lib/genie_env.py`: `genie-fsi-prd/genie-mcp/genie_mcp/environment.py`
- PDG + validation + arg shape: `genie-fsi-prd/genie-mcp/genie_mcp/tools/gmkspl_tool.py`, `gevgen_tool.py`, `gntpc_tool.py`
- Spline modules: `genie-fsi-prd/genie-mcp/genie_mcp/splines/{downloader,reader,plotter}.py`
- Flux registry: `genie-fsi-prd/genie-mcp/genie_mcp/tools/flux_tools.py`
- runlog_tools patch target: `genie-dev/runlog_tools/runlog_tools/{run_log.py,__init__.py}`
- Workflow narrative source: `genie-fsi-prd/genie-mcp/.claude/commands/genie-sim.md`

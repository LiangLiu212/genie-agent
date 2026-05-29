# jobsub-agent — a general-purpose grid submission tool (with a GENIE adapter)

## Context

The refactor plan (`refactor-genie-mcp-to-genie-agent.md`) deferred the grid
layer (~1400 lines across `genie-mcp/genie_mcp/jobs/{grid_manager,grid_tarball}.py`
and `tools/{gevgen_grid,gmkspl_grid,grid_admin}_tool.py`) with the note:

> Grid layer is deferred — it will be redesigned later as a **separate
> general-purpose submission tool, not GENIE-specific**.

This is that redesign. `jobsub-agent/` becomes a **sibling** of `genie-agent/`:
a generic `jobsub_lite` submission core (`lib/`) plus a thin **GENIE adapter**
(`adapters/genie/`). genie-agent produces local artefacts (splines, GHEPs);
jobsub-agent submits the *grid-scale* versions of the same work and pulls the
outputs back. The two stay decoupled — jobsub-agent has zero GENIE knowledge in
its core; the adapter is the only place PDGs / worker scripts / PNFS schemes
live.

**Decisions locked in (this pass):**
1. **Placement** — new sibling dir `jobsub-agent/`, mirroring genie-agent's
   shape (`scripts/` + core lib + `.claude/skills/`).
2. **Generality** — generic core + GENIE adapter (not a GENIE-specific port).
3. **Scope** — full parity in one pass: submit + monitor **and** tarball
   build + RCDS publish + CVMFS catalog.

Source of truth for grid behaviour to port/redesign:
`/exp/dune/data/users/liangliu/genie-fsi-prd/genie-mcp/genie_mcp/`.

---

## Headline design changes vs the genie-mcp grid layer

| genie-mcp (old) | jobsub-agent (new) | Why |
|---|---|---|
| Single central registry `~/.genie_mcp_grid_jobs.json` | **Registry-free** per-job JSON record under `jobsub-runs/`, discovered by glob, jq-queryable | Matches genie-agent's "metadata lives in the log, no registry" model |
| GENIE baked into submit/status/tarball | **Generic `lib/` core** + `adapters/genie/` | The deferred-grid mandate: reusable for any worker script |
| Inherited ambient shell env for `jobsub_*` | **Scrubbed submit env** (`lib/submit_env.py`) | Under pixi, `PYTHONHOME`/`PYTHONPATH`/`PIXI_*` poison jobsub_lite's own python — the grid analog of genie-agent's two-environments problem |
| `GridJob` dataclass + `asdict` into registry | per-job record dict written via `atomic_write_json` (same helper shape as `genie-agent/lib/jobs.py`) | One serialization story across both agents |
| status only via `update_grid_status(job_id, cfg)` | `status`/`list` re-query `jobsub_q` on demand and persist into the record | No supervisor exists for grid jobs (work runs remotely) — polling is the only truth |

Kept as-is (these were already good): ClassAd block parsing + HTCondor
`JobStatus` map; the **`DONE` sentinel** authoritative-completion check from
fetched worker logs (ifdh PNFS count is fallback only); RCDS publish via a
sentinel grid job that echoes `PUBLISH_SENTINEL_CVMFS_DIR=`; tarball mtime-hash
cache key; the `dropbox://` vs `/cvmfs/` `-R` override branch.

---

## Target directory layout

```
jobsub-agent/
├── config/
│   └── jobsub.json                 # jobsub_lite bins + group/role + pnfs scratch base + defaults
├── lib/                           # GENERIC core — NO genie imports
│   ├── __init__.py
│   ├── config.py                   # load config/jobsub.json (precedence like genie-agent/lib/config.py)
│   ├── submit_env.py               # scrubbed env for jobsub_* (auth pass-through, pixi strip)
│   ├── records.py                  # registry-free per-job record: jobid, glob discovery, atomic_write_json
│   ├── submit.py                   # build+run jobsub_submit, parse cluster id, write record + submit.log
│   ├── monitor.py                  # jobsub_q --long ClassAd parse + status aggregation + reconcile
│   ├── control.py                  # cancel (jobsub_rm) + fetchlog (jobsub_fetchlog) + DONE-sentinel count
│   ├── outputs.py                  # ifdh ls/cp pull (suffix/pattern is a parameter, not hardcoded)
│   ├── tarball.py                  # build tarball from a dir (generic include/exclude/mtime-hash cache)
│   ├── publish.py                  # RCDS publish via sentinel job + CVMFS catalog + verify/staleness
│   └── templates/
│       └── publish_only.sh         # generic sentinel worker (echoes PUBLISH_SENTINEL_CVMFS_DIR=)
├── scripts/                        # generic CLI surface (pixi run python jobsub-agent/scripts/…)
│   ├── submit.py                   # generic: submit an arbitrary worker script + inputs
│   ├── job.py                      # status / list / cancel / fetchlog / pull
│   └── tarball.py                  # build / publish / list / verify / label-from-job
├── adapters/
│   └── genie/                      # GENIE-specific layer (the ONLY place GENIE lives)
│       ├── __init__.py
│       ├── pnfs.py                 # PNFS path scheme + channel-from-genlist
│       ├── run_gmkspl_grid.py      # resolve PDGs/validate → build worker args → lib.submit
│       ├── run_gevgen_grid.py
│       └── templates/
│           ├── gmkspl_grid.sh      # ported worker scripts
│           └── gevgen_grid.sh
└── jobsub-runs/                    # gitignored; per-job artefacts (flat per-day, like genie-runs/)
    └── <runtype>-YYYY-MM-DD/
        ├── <stem>.gridlog          # mutable JSON record (registry-free; jq-queryable)
        ├── <stem>.submit.log       # combined jobsub_submit stdout+stderr
        ├── <stem>.command.json     # resolved submit argv + metadata
        └── <stem>.fetched/         # jobsub_fetchlog --unzipdir target

# Plus, at repo root (where genie-runlog already lives):
.claude/skills/{jobsub-submit,jobsub-jobs,jobsub-tarball,genie-grid}/SKILL.md
.claude/plans/jobsub-agent.md       # this file
```

**No cross-import into genie-agent.** Earlier drafts had the adapter
`sys.path.insert(genie-agent root)` + `from lib.pdg import …`, which forced a
`jlib`-vs-`lib` rename to avoid package shadowing. That coupling is gone: PDG
data now lives in the repo-shared **`shared/pdg.json`** (see "Shared PDG data"),
which the adapter reads via its **own** thin `pdg.py` loader — identical to
`genie-agent/lib/pdg.py`. So jobsub-agent's core is plainly `lib/`, no sys.path
juggling, and the agents resolve PDGs from one source without importing each
other.

---

## Generic core (`lib/`) — what each module owns

### `lib/config.py`
Loads `config/jobsub.json`; precedence `--installation`/explicit → env →
top-level default, same 30-line shape as `genie-agent/lib/config.py`. Config
holds the **stripped grid fields** the refactor removed from genie_env.json:
```json
{
  "jobsub_bin":          "/opt/jobsub_lite/bin/jobsub_submit",
  "jobsub_q_bin":        "/opt/jobsub_lite/bin/jobsub_q",
  "jobsub_rm_bin":       "/opt/jobsub_lite/bin/jobsub_rm",
  "jobsub_fetchlog_bin": "/opt/jobsub_lite/bin/jobsub_fetchlog",
  "default_group":       "dune",
  "default_role":        "Analysis",
  "default_disk":        "20GB",
  "pnfs_scratch_base":   "/pnfs/dune/scratch/users",
  "append_condor_requirements": "(TARGET.Microarch>=\"x86_64-v3\")"
}
```
`jobsub_rm` is derived from `jobsub_q_bin`'s parent at call time (genie-mcp's
`_resolve_jobsub_rm` trick) to avoid a stale config entry.

### `lib/submit_env.py`  ← **new, the likely first failure point**
jobsub_lite is its own python venv invoked by absolute path; but
`PYTHONHOME`/`PYTHONPATH`/`PIXI_*`/`CONDA_*` leaking from the pixi shell can
still break it (exactly the bug genie-agent's `env -i` snapshot solved for
GENIE). `build_submit_env()` returns a **copy** of `os.environ` that:
- **keeps** auth/runtime vars: `HOME USER LOGNAME TERM PATH KRB5CCNAME
  BEARER_TOKEN_FILE XDG_RUNTIME_DIR X509_USER_PROXY GROUP` and `_condor_*`;
- **drops** `PIXI_* CONDA_* MAMBA_* VIRTUAL_ENV PYTHONHOME PYTHONPATH` and any
  `BASH_FUNC_*`.
Every `subprocess.run([cfg.jobsub_*…])` passes `env=build_submit_env()`.
Unlike GENIE we do **not** snapshot to JSON — auth (kerberos/token) is live and
per-session, so we scrub at call time instead of caching.

### `lib/records.py`  ← replaces the central registry
Registry-free, mirroring `genie-agent/lib/jobs.py`:
- `make_jobid(runtype, stem) -> "<runtype>-<stem>-<6hex>"`; `parse_jobid`.
- record dir/stem helpers → `jobsub-runs/<runtype>-YYYY-MM-DD/<stem>.gridlog`.
- `atomic_write_json` / `update_record` (temp + `os.replace`).
- `find_record_for_jobid` globs `jobsub-runs/*/<stem>.gridlog`, matches embedded
  `jobid`. `iter_records()` for `list`.
- Record schema (superset of genie-mcp's `GridJob`, jq-friendly):
  `jobid, runtype, cluster_id, status, n_jobs, submitted, finished,
  processes_done, processes_done_source, outputs_pulled, submit_log_file,
  command_file, command_str, tarball_path, worker_script, inputs[], outputs{},
  pnfs_output_dir, local_output_dir, submit_user, fetchlog_error, extra{}`.
  `status` ∈ `pending|submitted|running|held|done|partial|failed|cancelled`
  (same model as `grid_manager.py` header).

### `lib/submit.py`
`submit(cfg, *, runtype, stem, submit_cmd, n_jobs, worker_script, inputs,
outputs, extra, dry_run=False) -> record`. Writes `<stem>.command.json` first,
runs `jobsub_submit` (`+ --no_submit` if `dry_run`) with the scrubbed env,
writes combined stdout+stderr to `<stem>.submit.log`, parses the **last**
`\d+\.\d+@\S+\.fnal\.gov` as `cluster_id` (port `parse_jobsub_cluster_id`),
sets `status` (`pending`/`submitted`/`failed`), writes the `.gridlog`. **Knows
nothing about GENIE** — the caller hands it a finished `submit_cmd` and the
worker-args.

### `lib/monitor.py`
Port `_parse_classad_blocks`, `_HTC_STATE_MAP`, `query_jobsub_status`,
`update_grid_status` → `refresh_status(record_path, cfg)`. Reads the `.gridlog`,
re-queries `jobsub_q --long`, aggregates per-process states, applies the
empty-queue → DONE-sentinel/PNFS-count → `done`/`partial`/`failed` logic, and
persists. Terminal states short-circuit. `list_jobs(active_only)` refreshes
non-terminal records.

### `lib/control.py`
`cancel(record, cfg)` → `jobsub_rm --jobid <cluster> -G <group>`, mark
`cancelled`. `fetch_log(record, cfg, dest_dir=None)` → `jobsub_fetchlog
--unzipdir <stem>.fetched/`. `count_done_sentinel(dest_dir)` → number of
`*.out` whose body contains a standalone `DONE` line (authoritative completion).

### `lib/outputs.py`
`pull(record, cfg, *, suffix, name_template, overwrite=False)` — the genie-mcp
`grid_outputs_pull` generalized: `suffix` (`.ghep.root` / `.xml` / anything) and
the local filename template are **parameters**, not a `job_kind` switch. Walks
`ifdh ls` of `pnfs_output_dir`, copies matching files into `local_output_dir`,
updates `processes_done` + `status`.

### `lib/tarball.py`
Port `grid_tarball.py`'s build half, generalized: `build_tarball(*, build_dir,
toplevel_candidates, exclude_components, exclude_prefixes, exclude_suffixes,
output_path=None, force=False, background=False)`. Keeps the sha1(build_dir +
sorted top-level mtimes) cache key, the `_exclude_filter`, the background
detached-`Popen` rebuild, and the >8 GB warning. GENIE's specific
`_TOPLEVEL_CANDIDATES` / `_EXCLUDE_*` move to the adapter and are passed in.
Tune-tarball build (`build_tune_tarball`, xml/md-only) stays generic too:
`build_overlay_tarball(*, source_dir, members, label)`.

### `lib/publish.py`
Port `_publish_to_cvmfs`, `parse_rcds_hash`, the CVMFS catalog
(`load_catalog`/`save_catalog`/`add_to_catalog`/`lookup_catalog`),
`verify_cvmfs` (staleness 21d warn / 28d fail), `label_from_job`. Catalog moves
from genie-mcp's `genie-data/grid/tarballs/catalog.json` to
`jobsub-agent/config/catalog.json` (committed? no — gitignore it; it stores
machine/CVMFS state). The sentinel worker is `lib/templates/publish_only.sh`.

---

## GENIE adapter (`adapters/genie/`) — the only GENIE-aware code

PDG resolution comes from `adapters/genie/pdg.py` — a thin loader of the
repo-shared `shared/pdg.json` (same code as `genie-agent/lib/pdg.py`); the
one-line tune regex + tune-family dir check are restated locally (trivial), so
the adapter does **not** import genie-agent. Adds the **grid-specific**
validation the local validators lack (ported from
`gevgen_grid_tool._validate` / `gmkspl_grid_tool`):
- `generator_list == "Default"` is rejected (PYTHIA6 charm).
- cross-sections must be **absolute**; if `/pnfs/...`, assert via `ifdh ls`;
  if local, warn "stage to /pnfs scratch first" (file-transfer host can't read
  `/exp/dune/data`).
- charged-lepton probe ⇒ `GEM*` tune + `EM*` generator list.
- energy-range (flux) mode rejected — no flux delivery (same MVP limit).
- `n_jobs > 0`.

`adapters/genie/pnfs.py` — `channel_from_genlist` + the PNFS scheme
`{pnfs_scratch_base}/{user}/jobsub-agent/{project}/{channel}/{installation}/
{tune}/{jobid}_{spl|gev}/{probe}_{target}_{tune}`.

`run_gmkspl_grid.py` / `run_gevgen_grid.py` — argparse CLIs mirroring
genie-agent's runner shape (reuse `runlog_tools.make_parser` /
`args_to_inputs`). Each: resolve PDGs → validate → look up + `verify_cvmfs` the
tarball label (and optional tune-tarball label) → build the `jobsub_submit`
argv (`-G/--role/--disk/-N/--append_condor_requirements`, `--tar_file_name
dropbox://` **or** `-R /cvmfs/...` override, `-f file://<spline>` or schemeless
`/pnfs/...`) → build the worker args (`file://<worker.sh> -p -t -e -n -T -L -S
-j -P -O [-R] [-X]`) → `lib.submit(...)`. The adapter resolves the GENIE
**build_dir** (for tarball builds) by **reading genie-agent's
`config/genie_env.json`** (a plain JSON file read, not a python import) for the
active install's `genie_setup_script`, then using its parent — no code coupling.

## Shared PDG data (`shared/pdg.json`) — already implemented

Both agents resolve PDGs from one repo-shared file so probe/target codes never
diverge. `shared/build_pdg.py` (build-time; needs the `pdg` PyPI package, added
to `pixi.toml` under `[pypi-dependencies]`) **combines** two authorities and
snapshots them to JSON, mirroring the `refresh_genie_env.py → config/env/*.json`
pattern:
- **GENIE's `genie_pdg_table*.txt`** → the names + codes GENIE itself uses
  (`nu_mu`, `mu-`, `proton`).
- **the PDG Python API** (`pdg.connect()`) → validates each code and supplies
  the canonical particle name + mass (neutrinos: null).
- **nuclei by formula** — neither source enumerates ions, so nuclei resolve at
  runtime from the embedded element→Z table via `1000000000+Z*10000+A*10`
  (any `<Sym><A>` like `Ar40`; reverse for `canonical_target`).

Runtime loaders read **only** the JSON (no `pdg` dependency). `genie-agent/lib/pdg.py`
already does this; the jobsub-agent adapter ships the same ~60-line loader.
This is what retires the cross-import entirely.

Worker scripts `gmkspl_grid.sh` / `gevgen_grid.sh` ported verbatim (they
already inline the spack env and skip nusystematics) into
`adapters/genie/templates/`. `publish_only.sh` is generic → `lib/templates/`.

---

## CLI surface

```bash
# generic submit (any worker script)
pixi run python jobsub-agent/scripts/submit.py \
    --worker <abs/worker.sh> --tarball-label <label> -N 100 [--dry-run] -- <worker args…>

# job control
pixi run python jobsub-agent/scripts/job.py status  <jobid>
pixi run python jobsub-agent/scripts/job.py list    [--active]
pixi run python jobsub-agent/scripts/job.py cancel  <jobid>
pixi run python jobsub-agent/scripts/job.py fetchlog <jobid>
pixi run python jobsub-agent/scripts/job.py pull    <jobid> [--overwrite]

# tarballs
pixi run python jobsub-agent/scripts/tarball.py build   [--force] [--background]
pixi run python jobsub-agent/scripts/tarball.py publish --label <label> [--overwrite]
pixi run python jobsub-agent/scripts/tarball.py list    [--verify]
pixi run python jobsub-agent/scripts/tarball.py verify  --label <label>

# GENIE grid runs (adapter)
pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
    --probes numu --targets C12 --tune G18_02a_00_000 --genlist CCQE \
    --tarball-label <label> -N 1 [--dry-run]
pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
    --probe numu --target C12 -n 100 -e 3.0 --cross-sections /pnfs/.../spline.xml \
    --tune G18_02a_00_000 --genlist CCQE --tarball-label <label> -N 100 [--dry-run]

# discovery (consistent with genie-runlog)
jq -r '[.jobid,.runtype,.status,.cluster_id,.processes_done]|@tsv' jobsub-agent/jobsub-runs/*/*.gridlog
```

---

## Skills (repo-root `.claude/skills/`, alongside genie-runlog)

- **jobsub-submit** — generic submit + the auth preflight (kerberos token,
  `jobsub_lite` on PATH, why the env is scrubbed); dry-run first.
- **jobsub-jobs** — status/list/cancel/fetchlog/pull workflow; the
  pending/submitted/running/held/done/partial/failed/cancelled model; the
  DONE-sentinel vs PNFS-count distinction; jq recipes over `*.gridlog`.
- **jobsub-tarball** — build → publish (sentinel job, ~minutes) → catalog →
  verify/staleness (republish at ~30d RCDS GC); tune-overlay tarballs + GXMLPATH.
- **genie-grid** — the GENIE adapter recipes: gmkspl/gevgen on the grid,
  staging splines to /pnfs, GEM-tune + EM-list rule, pulling outputs back into a
  genie-agent-style layout.

---

## Migration order (smallest vertical slice first)

**Status:** steps **1–8 are done** and on `main` (commits 28ad4c5, f1ee7c1,
5cde10b, eef7f23, f5ce977, e05d0f3, fbbde19, 12854d2). Everything verifiable
without a live grid was verified deterministically (env scrub, records, submit
dry-run, ClassAd aggregation, status short-circuits, pull walk/filter, tarball
build+cache, catalog/verify, adapter dry-runs + GEM/EM validation). **Step 9
(live end-to-end on a dunegpvm) is the only remaining item** — it needs
jobsub_lite + a valid token, so it runs on a grid node, not from the agent host.
First-contact watch items: whether the scrubbed submit env suffices for a real
`jobsub_submit` (token/dropbox), and the worker scripts' hardcoded spack hashes
matching the published tarball's toolchain.

1. Scaffold `jobsub-agent/`; write `config/jobsub.json`; add gitignore lines
   (`jobsub-agent/config/catalog.json`, `jobsub-agent/jobsub-runs/`). Decide
   whether `config/jobsub.json` is tracked (paths are machine-specific → likely
   gitignore the whole `jobsub-agent/config/`, like genie-agent).
2. `lib/{config,submit_env,records}.py` — the registry-free + scrubbed-env
   foundation. Smoke: `build_submit_env()` shows no `PIXI_*`/`PYTHONHOME`;
   `jobsub_q --help` runs under it.
3. `lib/submit.py` + `scripts/submit.py`. **Verify with `--dry-run`**
   (`--no_submit`): a `.command.json` + `.gridlog` (`status=pending`) appear and
   the printed argv is correct — no real submission, no auth needed.
4. `lib/monitor.py` + `lib/control.py` + `scripts/job.py`
   (status/list/cancel/fetchlog). Verify against a real 1-job submit on a
   grid-capable node.
5. `lib/outputs.py` (ifdh pull).
6. `lib/tarball.py` + `lib/publish.py` + `scripts/tarball.py` +
   `templates/publish_only.sh`. Verify build (cache hit/miss), then publish
   (sentinel job → catalog entry with `cvmfs_dir`).
7. GENIE adapter: `pnfs.py`, worker scripts, `run_gmkspl_grid.py`,
   `run_gevgen_grid.py`. Verify each with `--dry-run` first.
8. Four `SKILL.md` files.
9. End-to-end on a dunegpvm: build+publish a tarball, gmkspl-grid `-N 1`,
   poll to `done`, fetchlog (DONE sentinel), pull the `.xml`; then gevgen-grid
   against a /pnfs spline, pull `.ghep.root` + `.gst.root`.

---

## Open risks / things to confirm during build

- **Auth under pixi.** Step 2/3 prove whether the scrubbed env is sufficient
  for `jobsub_lite` (token via `htgettoken`/`BEARER_TOKEN_FILE`, kerberos via
  `KRB5CCNAME`). If pixi's python still leaks in, may need a tiny
  `env -i`-style wrapper for the jobsub calls (heavier; avoid unless forced).
- **Host requirement.** jobsub/ifdh only work on a node with jobsub_lite + a
  valid token; all non-dry-run verification must happen there. Dry-run +
  command-shape checks are CI-able anywhere.
- **Two PDG loaders in sync.** The cross-import is retired (shared
  `shared/pdg.json`), but the adapter duplicates the ~60-line loader. Risk is
  low (same data file; loader rarely changes) — revisit a shared package only
  if a third consumer appears. Re-run `shared/build_pdg.py` after any GENIE
  table change.
- **Catalog location & tracking.** genie-mcp kept it under `genie-data/`; here
  it holds CVMFS hashes + publish timestamps (machine state) → gitignore.

## Reference files (genie-mcp, to port/redesign from)

- `genie_mcp/jobs/grid_manager.py` — submit/status/list/cancel/fetchlog +
  ClassAd parse + DONE sentinel + PNFS count.
- `genie_mcp/jobs/grid_tarball.py` — build/publish/catalog/verify/tune-tarball.
- `genie_mcp/tools/gevgen_grid_tool.py`, `gmkspl_grid_tool.py` — validation +
  argv shape + worker-args (→ `adapters/genie/`).
- `genie_mcp/tools/grid_admin_tools.py` — outputs pull + lifecycle wrappers.
- `genie_mcp/jobs/templates/{gevgen_grid,gmkspl_grid,publish_only}.sh` — workers.
- genie-agent parallels to imitate: `lib/jobs.py` (records/atomic-write/jobid),
  `lib/config.py` (loader), `scripts/run_gevgen.py` (runner shape),
  `.claude/skills/genie-runlog` (jq-discovery skill style).
```

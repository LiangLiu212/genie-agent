# Plan: runlog-reproducibility fixes (sequential, one branch)

## Context
Make the core invariant **true**: *the LLM may choose the commands, but the runlog must
let a human replay the artifacts without the LLM.* The 2026-06-04 adversarial review found
the runlog records the gxmlpath DIR (not tune-XML bytes), logs `seed: null` for local
gevgen, pins the env by NAME only, and that `jobsub` mislabels RUNNING jobs `failed`. This
PR closes those gaps on branch **`fix/runlog-reproducibility`** (off `main`), sequentially,
one PR, verified by a real GENIE run. Backlog: `notes/reproducibility-backlog.md`. Paper
direction lives in the project-goal memory + notes (deprioritized per user).

Scope = the user-chosen sequence (tune-XML → seed → env/binary → drain gate → manifest)
plus three near-free same-file companions (git_dirty, spline_count+free-nucleon warn,
stem uniqueness). Deferred: `parent_jobid` (#16, often null for grid-pulled splines),
wiki/cleanup tiers.

## Implementation (in order)

### A. #12 Hash resolved tune-XML contents — `lib/validation.py` + both runners
- Add `tune_xml_hashes(tune, genie_bin_dir, gxmlpath_dirs) -> dict` in `lib/validation.py`,
  reusing `_tune_family_dir` (validation.py:19) to locate the family dir (gxmlpath first,
  then `$GENIE/config`). Return `{relpath: sha256_short(file)}` for every `*.xml` under it
  (recursive, sorted) — captures CommonParam/ModelConfiguration/EventGenerator + the
  PP-variant subdir, i.e. the bytes that actually set the physics.
- In `run_gmkspl.py` / `run_gevgen.py`, add `inputs["tune_xml_sha256"] = tune_xml_hashes(...)`
  in the manual inputs dict (gmkspl.py:156, gevgen analog). Reuse `sha256_short` (paths.py:39).

### B. #10 Materialize the gevgen RNG seed — `run_gevgen.py` (+ gmkspl optional)
- Before building `cmd`/`inputs`: `if args.seed is None: args.seed = secrets.randbelow(2**31)`.
  Then the existing `if args.seed is not None: cmd += ["--seed", str(args.seed)]` adds it to
  the argv, and `args_to_inputs` records the concrete integer in `inputs.seed` (no more null).
  Scope to gevgen (gmkspl QE-EM splines are seed-insensitive; do gmkspl too for consistency,
  harmless). Add `import secrets`.

### C. #11 Hash env + GENIE binary — `lib/genie_env.py` + both runners
- Add `env_sha256(env: dict) -> str` in `lib/genie_env.py`: `sha256(json.dumps(env,
  sort_keys=True))[:16]`. Hash the **base** snapshot (the `load_genie_env(cfg)` result,
  BEFORE `with_gxmlpath`) so it fingerprints the installation; gxmlpath is already in
  `inputs.gxmlpath` and the tune XMLs in (A).
- In both runners: capture `base_env = load_genie_env(cfg)` then `env = with_gxmlpath(...)`,
  and add `inputs["env_sha256"] = env_sha256(base_env)` and
  `inputs["genie_bin_sha256"] = sha256_short(binary)` (binary already built before inputs).

### D. #17 Flag a dirty git tree — `lib/jobs.py`
- Add `_git_dirty() -> Optional[bool]` next to `_git_sha` (jobs.py:42): run
  `git -C _AGENT_ROOT status --porcelain`; True if any output, False if clean, None on error.
- Add `"git_dirty": _git_dirty()` to the `make_initial_log` record (jobs.py:123 area).

### E. #13 Free-nucleon warn + spline_count — `lib/validation.py` + `lib/jobs.py`
- `validate_gmkspl_inputs`: add a WARNING (not error) when any target is a free/single-nucleon
  (`2212`, `2112`, or H1 `1000010010`) — "free/single-nucleon target may yield an empty spline
  for nuclear channels; check outputs.spline_count". Advisory only.
- `_supervise_impl` (jobs.py:294 area): for `record["runtype"]=="gmkspl"` and rc==0, parse the
  primary_output XML and record `spline_count` = number of `<spline ` entries (add a tiny
  `_count_splines(xml_path)` helper; count via a cheap text scan, not full XML parse). Surface
  `outputs.spline_count` (and it being 0 is the robust empty-spline signal). This is the
  always-correct detector behind the advisory warn.

### F. #18 Stem uniqueness — `lib/paths.py`
- `run_stem` (paths.py:29): append a short token so two same-probe/target/tune runs in the
  same second don't clobber one log: `..._<YYYYMMDD-HHMMSS>-<3hex>` via `secrets.token_hex(2)`
  (or `%f` microseconds). Verify nothing parses a fixed stem format (the old `_GEVGEN_PATH_RE`
  was already removed; gntpc reads the sibling log, not the stem — confirm during impl).

### G. #9 Drain gate (CRITICAL) — `jobsub-agent/lib/monitor.py`
- In `refresh_status` (monitor.py:131-147), add a branch BEFORE the `elif q["empty"]` drain:
  `elif q["empty"] and q.get("raw_returncode", 0) != 0: pass` (transient — jobsub_q itself
  failed, e.g. the OTEL crash; do NOT stamp a terminal state). Surface it (e.g.
  keep status; optionally set a transient `last_poll_error`). Only drain when `q["empty"]`
  AND `raw_returncode == 0`. Optional hardening: require the cluster to have been seen
  non-empty once before draining (mirror `publish.py:223-237`).

### H. #15 Portable run-manifest + example env registry — new files
- New `genie-agent/scripts/build_run_manifest.py`: glob `genie-runs/*/*.log`
  (+ `jobsub-agent/jobsub-runs/*/*.gridlog`), emit a sorted, regenerable, git-tracked
  `genie-agent/run-manifest.jsonl` (one line/run: jobid, runtype, timestamp, git_sha,
  git_dirty, script_sha256, tune/genlist, canonical probe/target, installation, env_sha256,
  genie_bin_sha256, tune_xml_sha256, seed, input/output sha, returncode, spline_count).
  Reuses the genie-runlog jq discovery model; pure read + write, no schema change.
- New `genie-agent/genie_env.example.json` (tracked; `config/` is gitignored): the registry
  SCHEMA + installation NAMES only — no host paths, no env snapshots.

## Out of scope / deferred
#14, #16, #19, #20, #22-#26 (separate follow-ups). No edits to the runlog wire format beyond
additive `inputs`/`outputs` fields (jq-compatible, back-compatible).

## Verification (real runs, no test suite)
1. **gmkspl C12 foreground** (`--targets C12 --tune <gem> --gxmlpath genie-agent/tunes
   --genlist EMQE -n 30 -e 5 --foreground`): `jq` the runlog → assert `inputs.tune_xml_sha256`
   (dict, non-empty), `inputs.env_sha256`, `inputs.genie_bin_sha256`, `git_dirty` present, and
   after completion `outputs.spline_count > 0`.
2. **gmkspl free H1**: assert the free-nucleon WARNING fires and `outputs.spline_count == 0`.
3. **gevgen C12 ×2 without `--seed`** (reuse an existing spline): assert each runlog has a
   concrete integer `inputs.seed` (not null) that also appears in `outputs.genie_command`; the
   two runs get DIFFERENT seeds and DIFFERENT `output_sha256`. Then re-run gevgen passing one
   logged seed → identical `output_sha256` (proves replay-without-LLM).
4. **#9 drain gate**: synthetic check — feed `refresh_status` a record + monkeypatched
   `query_jobsub_status` returning `{empty:True, raw_returncode:1, ...}`; assert status is
   unchanged (NOT `failed`). And `{empty:True, raw_returncode:0}` with n_jobs outputs → drains.
5. **manifest**: run `build_run_manifest.py`; assert `run-manifest.jsonl` is produced, valid
   JSONL, git-trackable; spot-check a row matches its source log.
6. Commit incrementally (one commit per item A-H), push, open PR to `main`. Do NOT merge until
   checks 1-5 pass.

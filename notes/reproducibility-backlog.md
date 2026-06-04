# Reproducibility backlog — agentic GENIE workflow

Durable copy of the fix backlog (the session todo list is ephemeral). Goal &
invariant: **the LLM may choose the commands, but the runlog must let a human
replay the artifacts without the LLM.** Every item was verified against the code
during the 2026-06-04 adversarial design review. See
[[project-goal-reproducible-agentic-workflow]] and `.claude/plans/lucky-painting-nova.md`.

Status legend: `[ ]` pending · `[x]` done.

## Tier 1 — Critical (safety; invariant currently false)
- [ ] **Gate jobsub drain verdict on returncode (OTEL false-failure).**
  `jobsub-agent/lib/monitor.py` captures `raw_returncode` (~L80) but never reads it;
  an empty `jobsub_q` poll (OTEL import crash) stamps a RUNNING job `failed`,
  persisted to a terminal state that never self-corrects. *Fired this session.*
  Fix: gate the empty-drain branch on `raw_returncode==0`; write NO terminal state
  on a suspicious empty poll (reuse the seen-before-drained pattern in
  `publish.py:223-237`). (Real cause = jobsub_lite traced-import path, not env leak.)

## Tier 2 — High (make the invariant true / kill silent dead-ends)
- [ ] **Hash resolved tune-XML contents into the runlog.** *(highest-value)* Runlog
  records the gxmlpath DIR string, not the bytes; editing `EM-MinQ2Limit` changes
  output but leaves an identical runlog. Fix: hash the resolved tune-XML set into `inputs`.
- [ ] **Materialize local gevgen RNG seed into argv + runlog.** `run_gevgen.py:62,157`
  — `--seed` defaults None, omission logged as `inputs.seed=null`. Fix: synthesize a
  seed when omitted, write it into BOTH argv and `inputs.seed`. gevgen only (gmkspl
  QE-EM splines seed-insensitive). Caveat: GENIE default seed is fixed (65539) → the
  defect is replayability/audit, not run-to-run chaos.
- [ ] **Hash environment + GENIE binary into the runlog.** Env pinned by NAME only;
  `config/env/*.json` gitignored + re-snapshotted; per-run `env.json` deleted by
  supervisor; only warns on stale. Fix: add `env_sha256` (exclude volatile keys e.g.
  `SPACK_LOADED_HASHES`) + `genie_bin_sha256`.
- [ ] **Warn on free-nucleon gmkspl + record `spline_count`.** gmkspl on free H1
  writes an EMPTY spline at rc 0; `validation.py:64` permits it; the runner's own
  docstring uses `--targets H1` as its smoke test. Fix: WARN in
  `validate_gmkspl_inputs` keyed on a genlist requiring a bound nucleon (not target
  alone); record `outputs.spline_count` after rc==0.
- [ ] **Fire the wiki `comparison/` back-filing loop.** `comparison/` is empty; 0
  query/lint ops in `log.md`. Fix: make back-filing the mandatory close-out of any
  >=2-source query; seed by promoting the FSI synthesis in `concept/fsi.md`.

## Tier 3 — Medium (portability, completeness, drift)
- [ ] **Commit a portable run-manifest + example env registry.** Ledger
  (genie-runs/, jobsub-runs/, config/) gitignored + machine-local. Fix: jq-dump
  `*.log`/`*.gridlog` metadata to a committed append-only `runs-manifest.jsonl` +
  an `.example.json` env registry (schema + names, not host paths).
- [ ] **Add `parent_jobid`/`derived_from` dependency edge to runlog.** gevgen logs
  `cross_sections_sha256` but not the producing gmkspl jobid. Additive. (Often null
  for grid-pulled splines — sha256 stays the durable link.)
- [ ] **Flag dirty/untracked git tree in the runlog.** `jobs.py:42-52` records HEAD
  SHA but never checks `git status --porcelain`. Fix: add a `git_dirty` bool.
- [ ] **Fix sub-second stem collision.** `paths.py:35` stem has 1-second
  granularity + unconditional `os.replace` → two runs in one second overwrite a log.
  Fix: put the 6-hex (or counter) in the filename.
- [ ] **Add a wiki citation/slug lint.** ~30-line block-level lint: cite-every-number
  + sources-field membership + slug existence. Also fixes the
  `nucl-ex/0303011` vs `nucl-ex_0303011` slug mismatch (Dataview joins).

## Tier 4 — Lower / hygiene
- [ ] **Capture LLM decision-chain provenance.** Runlog records WHAT, not WHY.
  Optional: adopt the klieo `Step`/`StepKind` stream + per-step `LlmIo` sidecar
  (`notes/klieo-runlog-prior-art.md`).
- [x] **Commit the uncommitted 3rd wiki ingest (2301.02272).** Done — commit `05bca01`, PR #8.
- [ ] **De-duplicate target-validation + the two `pdg.py` copies.** Nuclear-target
  check copy-pasted 3x (`validation.py:64,142` + `common.py:140`); two `pdg.py`
  claimed byte-identical but drifted. Fix: shared helper + parity test.
- [ ] **Harden grid-worker spack version specs (prose→code).** Templates hand-sync
  `setup_env.sh` specs, prose-guarded; drift caused real SIGABRT. Fix: single source
  or a match-check.
- [ ] **Make grid gntpc/GST conversion non-fatal.** Under `set -e` a GST hiccup
  discards a good `ghep.root`. Fix: guard so ghep is still saved/transferred.
- [ ] **Clean up `runlog_tools`.** Still named `feanor_tools`, 2 funcs used, parallel
  drifting RunLog schema. Fix: inline the used functions / trim.

## Meta
- [ ] **Formalize + apply the prose→code guardrail migration policy.** Once a gotcha
  is proven and mechanical, promote it from skill-prose to an enforced code check;
  reserve the LLM for judgment. First candidates: T1 drain gate, T2 free-nucleon
  guard + tune/env/seed hashing, T3 dirty-tree flag.

## Suggested order
Hash tune-XML + seed + env/binary (make replay true) → drain gate (stop acting on
false status) → portable manifest (make the invariant testable off-host) → build
the blind replay audit as the regression test.

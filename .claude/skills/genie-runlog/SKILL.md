---
name: genie-runlog
description: Search genie-agent run metadata with jq. Use when the user wants to find, list, or filter past GENIE runs (gmkspl/gevgen jobs, splines, event files) by status, tune, generator list, probe/target, label, installation, jobid, or date — e.g. "which splines succeeded?", "show failed gevgen runs", "find the C12 run", "what command did job X run?".
---

# Searching genie-agent run metadata with `jq`

Every genie-agent run writes one self-contained JSON log next to its artefacts:
`genie-agent/genie-runs/<tune>-YYYY-MM-DD/<stem>.log`. There is no database or
index — `jq` over these files IS the query layer.

Glob from the repo root (genie-dev): **`genie-agent/genie-runs/*/*.log`**.
(From inside `genie-agent/`, use `genie-runs/*/*.log`.)

## Fields you can filter on

Top-level (uniform across all runners):
`jobid`, `runtype` (`gmkspl`|`gevgen`), `returncode`, `running`, `failed`,
`canceled`, `duration_s`, `pid`, `started`, `finished`, `timestamp`,
`description`, `output_sha256`, `error`, `git_sha`, `git_dirty` (tracked-file
modifications only), `script_sha256`.

Under `.inputs` (resolved values, uniform): `tune_resolved`,
`genlist_resolved`, `installation`, `label`, `gxmlpath`, and the
**reproducibility fingerprints** (runs after 2026-06-09; older logs lack them):
- `seed` — always a **concrete int** (the runner draws one when `--seed` is
  omitted; it also appears in `.outputs.genie_command`). Older logs: `null`.
- `tune_xml_sha256` — `{relpath: sha}` of every XML in the resolved tune
  family dir (knot subdirs included).
- `env_sha256` — hash of the base installation env snapshot.
- `genie_bin_sha256` — hash of the gmkspl/gevgen binary that ran.
- `genie_install_git` — `{sha, branch, dirty}` of the GENIE install checkout
  (captures install-level config+data, e.g. SpectralFunc param_sets).

Probe/target differ by runner: gmkspl stores arrays
(`.inputs.canonical_probes`, `.inputs.canonical_targets`), gevgen stores scalars
(`.inputs.canonical_probe`, `.inputs.canonical_target`). To match either, test
`.outputs.stem` (`<probe>_<target>_<YYYYMMDD-HHMMSS>-<3hex>`; the trailing
3-hex uniquifier — runs before 2026-06-09 lack it — keeps same-second runs
from clobbering each other, so prefix-match with `test("numu_C12")`).

Under `.outputs`: `primary_output` (the spline `.xml` or event `.ghep.root`),
`stdout_log`, `stderr_log`, `run_dir`, `stem`, `genie_command`, `warnings`,
and for successful gmkspl runs `spline_count` (number of `<spline>` entries —
**0 = empty spline list despite returncode 0**, e.g. free-nucleon targets).

`running`/`failed`/`canceled` start `null` and become `true`/`false`;
`returncode` is `null` until the process exits.

## Status filters

```bash
# summary table of every run
jq -r '[.jobid, .runtype, .returncode, .duration_s] | @tsv' genie-agent/genie-runs/*/*.log | column -t

# successful runs (exited 0, not still running / failed / canceled)
jq -r 'select(.returncode==0 and .running==false and (.failed|not) and (.canceled|not))
       | [.jobid, .duration_s, .outputs.primary_output] | @tsv' genie-agent/genie-runs/*/*.log

# failed runs (with reason if the supervisor recorded one)
jq -r 'select(.failed==true) | [.jobid, .returncode, (.error // "-")] | @tsv' genie-agent/genie-runs/*/*.log

# still running / pending (launched but binary not started yet)
jq -r 'select(.running==true) | [.jobid, .pid, .started] | @tsv' genie-agent/genie-runs/*/*.log
jq -r 'select(.running==null) | .jobid' genie-agent/genie-runs/*/*.log
```

## Metadata filters

```bash
jq -r 'select(.runtype=="gevgen") | .jobid' genie-agent/genie-runs/*/*.log
jq -r 'select(.inputs.tune_resolved=="G18_02a_00_000") | .jobid' genie-agent/genie-runs/*/*.log
jq -r 'select(.inputs.genlist_resolved=="CCQE")        | .jobid' genie-agent/genie-runs/*/*.log
jq -r 'select(.inputs.installation=="genie_rc")        | .jobid' genie-agent/genie-runs/*/*.log
jq -r 'select(.inputs.label=="myrun")                  | .jobid' genie-agent/genie-runs/*/*.log

# by probe/target — match the stem (works for both gmkspl arrays and gevgen scalars)
jq -r 'select(.outputs.stem | test("numu_C12")) | .jobid' genie-agent/genie-runs/*/*.log

# by date
jq -r 'select(.timestamp | startswith("2026-05-28")) | .jobid' genie-agent/genie-runs/*/*.log
```

## Extract a field or the full record

```bash
# the exact GENIE command that ran
jq -r '.outputs.genie_command' genie-agent/genie-runs/*/numu_C12_*.log

# output path + content hash
jq -r '{out: .outputs.primary_output, sha: .output_sha256}' genie-agent/genie-runs/*/*.log

# whole record for one jobid (search across all folders)
jq 'select(.jobid=="gevgen-numu_C12_20260528-140326-c98dcb")' genie-agent/genie-runs/*/*.log
```

## Reproducibility queries & replay

```bash
# empty-spline detector: gmkspl runs that "succeeded" but produced no splines
jq -r 'select(.runtype=="gmkspl" and .returncode==0 and .outputs.spline_count==0)
       | .jobid' genie-agent/genie-runs/*/*.log

# everything needed to replay a gevgen run without the LLM
jq '{cmd: .outputs.genie_command, seed: .inputs.seed,
     spline: .inputs.cross_sections_sha256, tune_xml: .inputs.tune_xml_sha256,
     env: .inputs.env_sha256, bin: .inputs.genie_bin_sha256,
     install: .inputs.genie_install_git}' genie-agent/genie-runs/*/<stem>.log
# re-running with the logged seed reproduces the events EXACTLY (verified:
# all gst branches identical); the .ghep.root bytes differ only in ROOT
# header timestamps, so compare gst content, not file sha.

# runs whose code or install was dirty / different
jq -r 'select(.git_dirty==true) | .jobid' genie-agent/genie-runs/*/*.log
jq -r 'select(.inputs.genie_install_git.dirty==true) | .jobid' genie-agent/genie-runs/*/*.log
```

For a flat cross-run view (local **and** grid in one place), build the manifest:
`pixi run python genie-agent/scripts/build_run_manifest.py` →
`genie-agent/run-manifest.jsonl`, one sorted JSON line per run with the
fingerprint fields (grid rows carry `cluster_id`, so per-process grid seeds
`CLUSTER+PROCESS` stay derivable). Regenerate + commit at milestones.

## Notes

- "Success" = the binary exited 0. It does not guarantee a useful result: e.g.
  `numu` CCQE on free `H1` exits 0 but writes an empty spline list (no bound
  neutron). The launcher now warns on free-nucleon targets and the runlog
  records `.outputs.spline_count` (0 = empty) — the robust detector.
- For live job control (cancel, reconcile lost supervisors), prefer
  `scripts/job.py status|cancel|list` over raw `jq` — see the genie-agent README.
- Pipe `@tsv` output through `column -t` for aligned tables.

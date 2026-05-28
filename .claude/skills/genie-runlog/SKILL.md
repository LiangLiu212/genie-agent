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
`description`, `output_sha256`, `error`.

Under `.inputs` (resolved values, uniform): `tune_resolved`,
`genlist_resolved`, `installation`, `label`.
Probe/target differ by runner: gmkspl stores arrays
(`.inputs.canonical_probes`, `.inputs.canonical_targets`), gevgen stores scalars
(`.inputs.canonical_probe`, `.inputs.canonical_target`). To match either, test
`.outputs.stem` (always `<probe>_<target>_<timestamp>`).

Under `.outputs`: `primary_output` (the spline `.xml` or event `.ghep.root`),
`stdout_log`, `stderr_log`, `run_dir`, `stem`, `genie_command`, `warnings`.

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

## Notes

- "Success" = the binary exited 0. It does not guarantee a useful result: e.g.
  `numu` CCQE on free `H1` exits 0 but writes an empty spline list (no bound
  neutron). Cross-check `output_sha256`/file size or open the artefact when it
  matters.
- For live job control (cancel, reconcile lost supervisors), prefer
  `scripts/job.py status|cancel|list` over raw `jq` — see the genie-agent README.
- Pipe `@tsv` output through `column -t` for aligned tables.

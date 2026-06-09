#!/usr/bin/env python3
"""Project every runlog into one portable, git-trackable JSONL manifest.

Globs the mutable per-run records — genie-agent local runs
(`genie-runs/*/*.log`) and jobsub-agent grid runs
(`jobsub-agent/jobsub-runs/*/*.gridlog`) — and emits one sorted JSON line per
run with the reproducibility fields: who ran what (jobid, runtype, script,
git state), with which physics inputs (tune, genlist, probe/target,
installation, tune-XML/env/binary fingerprints, seed, input hashes), and what
came out (returncode, output sha, spline_count; cluster_id for grid rows so
per-process grid seeds CLUSTER+PROCESS stay derivable).

Pure read + write: no runlog is modified and the wire format is untouched.
The manifest is REGENERABLE — rebuild it any time; regenerate + commit at
milestones (e.g. when cutting results), not after every run.

Usage:
    pixi run python genie-agent/scripts/build_run_manifest.py
    # writes genie-agent/run-manifest.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
_DEV_ROOT   = _AGENT_ROOT.parent

LOCAL_GLOB = _AGENT_ROOT / "genie-runs"
GRID_GLOB  = _DEV_ROOT / "jobsub-agent" / "jobsub-runs"
OUT_PATH   = _AGENT_ROOT / "run-manifest.jsonl"


def _local_row(record: dict) -> dict:
    inputs  = record.get("inputs", {}) or {}
    outputs = record.get("outputs", {}) or {}
    return {
        "kind":              "local",
        "jobid":             record.get("jobid"),
        "runtype":           record.get("runtype"),
        "timestamp":         record.get("timestamp"),
        "git_sha":           record.get("git_sha"),
        "git_dirty":         record.get("git_dirty"),
        "script_sha256":     record.get("script_sha256"),
        "installation":      inputs.get("installation"),
        "tune":              inputs.get("tune_resolved"),
        "genlist":           inputs.get("genlist_resolved"),
        "probes":            inputs.get("canonical_probes")
                             or ([inputs["canonical_probe"]] if inputs.get("canonical_probe") else None),
        "targets":           inputs.get("canonical_targets")
                             or ([inputs["canonical_target"]] if inputs.get("canonical_target") else None),
        "seed":              inputs.get("seed"),
        "gxmlpath":          inputs.get("gxmlpath"),
        "tune_xml_sha256":   inputs.get("tune_xml_sha256"),
        "env_sha256":        inputs.get("env_sha256"),
        "genie_bin_sha256":  inputs.get("genie_bin_sha256"),
        "genie_install_git": inputs.get("genie_install_git"),
        "input_sha256":      inputs.get("cross_sections_sha256")
                             or inputs.get("input_cross_sections_sha256")
                             or inputs.get("input_sha256"),
        "primary_output":    outputs.get("primary_output"),
        "output_sha256":     record.get("output_sha256"),
        "spline_count":      outputs.get("spline_count"),
        "returncode":        record.get("returncode"),
    }


def _grid_row(record: dict) -> dict:
    # GENIE-adapter gridlogs: `extra` is the flat summary (adapter, probe,
    # target, tune, genlist, installation); `inputs` is a LIST of per-spec
    # dicts (one per probe/target combination). Fall back gracefully for
    # generic submit.py records where neither exists.
    extra = record.get("extra") or {}
    inputs = record.get("inputs")
    first = (inputs[0] if isinstance(inputs, list) and inputs
             else inputs if isinstance(inputs, dict) else {})
    return {
        "kind":              "grid",
        "jobid":             record.get("jobid"),
        "runtype":           record.get("runtype"),
        "timestamp":         record.get("submitted"),
        "git_sha":           record.get("git_sha"),
        # cluster_id makes per-process grid seeds (CLUSTER+PROCESS) derivable
        "cluster_id":        record.get("cluster_id"),
        "status":            record.get("status"),
        "n_jobs":            record.get("n_jobs"),
        "processes_done":    record.get("processes_done"),
        "installation":      extra.get("installation") or first.get("installation"),
        "tune":              extra.get("tune") or first.get("tune"),
        "genlist":           extra.get("genlist") or first.get("genlist"),
        "probes":            first.get("probes") or ([extra["probe"]] if extra.get("probe") else None),
        "targets":           first.get("targets") or ([extra["target"]] if extra.get("target") else None),
        "tarball_path":      record.get("tarball_path"),
        "pnfs_output_dir":   record.get("pnfs_output_dir"),
    }


def build_manifest() -> list[dict]:
    rows: list[dict] = []
    for p in sorted(LOCAL_GLOB.glob("*/*.log")):
        try:
            rows.append(_local_row(json.loads(p.read_text())))
        except Exception as exc:
            sys.stderr.write(f"warning: skipping unreadable {p}: {exc}\n")
    for p in sorted(GRID_GLOB.glob("*/*.gridlog")):
        try:
            rows.append(_grid_row(json.loads(p.read_text())))
        except Exception as exc:
            sys.stderr.write(f"warning: skipping unreadable {p}: {exc}\n")
    # deterministic order -> reviewable diffs
    rows.sort(key=lambda r: ((r.get("timestamp") or ""), (r.get("jobid") or "")))
    return rows


def main() -> int:
    rows = build_manifest()
    with OUT_PATH.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    n_local = sum(1 for r in rows if r["kind"] == "local")
    n_grid  = len(rows) - n_local
    print(f"wrote {OUT_PATH} ({len(rows)} runs: {n_local} local, {n_grid} grid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

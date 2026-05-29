#!/usr/bin/env python3
"""Generic jobsub_lite submission CLI (GENIE-agnostic).

Builds a `jobsub_submit` command from flags + a worker script and hands it to
`lib.submit`. Everything after `--` is passed through to the worker script.

    pixi run python jobsub-agent/scripts/submit.py \
        --worker /abs/worker.sh -N 100 \
        [--tar-file-name dropbox:///abs/install.tar] [-f /pnfs/.../in.xml] \
        [--memory 2000MB] [--dry-run] -- <worker args...>

`--dry-run` appends `--no_submit`: the record is written as `pending` and no job
is actually submitted. Track/steer via scripts/job.py.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_ROOT))

from lib.config import load_config        # noqa: E402
from lib.submit import submit             # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit a worker script to the grid via jobsub_lite.")
    ap.add_argument("--worker", required=True, help="worker script path (resolved to absolute)")
    ap.add_argument("-N", "--n-jobs", type=int, default=1, help="number of grid processes (-N)")
    ap.add_argument("--runtype", default="jobsub", help="record/runtype label (default: jobsub)")
    ap.add_argument("--stem", default=None, help="record stem (default: <worker>_<timestamp>)")
    ap.add_argument("-G", "--group", default=None, help="jobsub group (default: config default_group)")
    ap.add_argument("--role", default=None, help="VOMS role (default: config default_role)")
    ap.add_argument("--disk", default=None, help="--disk (default: config default_disk)")
    ap.add_argument("--tar-file-name", default=None,
                    help="value for --tar_file_name, e.g. dropbox:///abs/install.tar")
    ap.add_argument("-f", "--input-file", action="append", default=None, metavar="PATH",
                    help="repeatable; passed as `-f <PATH>` (server-side ifdh) or use file://...")
    ap.add_argument("--append-condor-requirements", default=None,
                    help="(default: config append_condor_requirements)")
    ap.add_argument("--memory", default=None, help="--memory, e.g. 2000MB")
    ap.add_argument("--expected-lifetime", default=None, help="--expected-lifetime, e.g. 8h")
    ap.add_argument("--config", default=None, help="path to jobsub.json ($JOBSUB_AGENT_CONFIG)")
    ap.add_argument("--dry-run", action="store_true", help="append --no_submit; record as pending")
    ap.add_argument("worker_args", nargs=argparse.REMAINDER,
                    help="args after `--` forwarded to the worker script")
    args = ap.parse_args()

    cfg = load_config(args.config)

    worker = Path(args.worker).resolve()
    if not worker.exists():
        sys.stderr.write(f"error: worker script not found: {worker}\n")
        return 2

    group = args.group or cfg["default_group"]
    role  = args.role  or cfg.get("default_role", "Analysis")
    disk  = args.disk  or cfg.get("default_disk", "20GB")
    req   = args.append_condor_requirements or cfg.get("append_condor_requirements")

    cmd: list[str] = [cfg["jobsub_bin"], "-G", group, "--role", role,
                      "--disk", disk, "-N", str(args.n_jobs)]
    if req:
        cmd += ["--append_condor_requirements", req]
    for f in (args.input_file or []):
        cmd += ["-f", f]
    if args.tar_file_name:
        cmd += ["--tar_file_name", args.tar_file_name]
    if args.memory:
        cmd += ["--memory", args.memory]
    if args.expected_lifetime:
        cmd += ["--expected-lifetime", args.expected_lifetime]

    worker_args = args.worker_args
    if worker_args and worker_args[0] == "--":   # argparse keeps the separator
        worker_args = worker_args[1:]
    cmd += [f"file://{worker}", *worker_args]

    now = datetime.now()
    stem = args.stem or f"{worker.stem}_{now.strftime('%Y%m%d-%H%M%S')}"

    record, gridlog = submit(
        runtype=args.runtype, stem=stem, submit_cmd=cmd, n_jobs=args.n_jobs,
        submit_user=os.environ.get("USER", ""),
        worker_script=str(worker), tarball_path=args.tar_file_name or "",
        dry_run=args.dry_run, when=now,
    )

    print(f"jobid:  {record['jobid']}")
    line = f"status: {record['status']}"
    if record["cluster_id"]:
        line += f"  cluster: {record['cluster_id']}"
    print(line)
    print(f"record: {gridlog}")
    if record.get("error"):
        sys.stderr.write(f"error:  {record['error']}\n")
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())

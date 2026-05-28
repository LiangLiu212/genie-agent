#!/usr/bin/env python3
"""Inspect and control genie-agent background jobs.

Usage:
    pixi run python scripts/job.py status <jobid>
    pixi run python scripts/job.py cancel <jobid>
    pixi run python scripts/job.py list [--active]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_ROOT))

from lib.jobs import (                                            # noqa: E402
    cancel_job, find_log_for_jobid, reconcile_log,
)
from lib.paths import RUNS_ROOT                                   # noqa: E402


def _print_record(record: dict) -> None:
    summary = {
        k: record.get(k)
        for k in ("jobid", "runtype", "running", "failed", "canceled",
                  "returncode", "pid", "started", "finished", "duration_s")
    }
    for k, v in summary.items():
        print(f"  {k:<11} {v}")


def cmd_status(args: argparse.Namespace) -> int:
    log_path = find_log_for_jobid(args.jobid)
    record   = reconcile_log(log_path)
    print(f"log: {log_path}")
    _print_record(record)
    if args.json:
        print()
        print(json.dumps(record, indent=2))
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    log_path = find_log_for_jobid(args.jobid)
    record   = cancel_job(log_path)
    print(f"log: {log_path}")
    _print_record(record)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows: list[dict] = []
    for log_path in sorted(RUNS_ROOT.glob("*/*.log")):
        try:
            record = json.loads(log_path.read_text())
        except Exception:
            continue
        if "jobid" not in record:
            continue
        rows.append(record)

    if args.active:
        rows = [r for r in rows if r.get("running") is True]

    if not rows:
        print("(no jobs)")
        return 0

    header = f"{'STATE':<10} {'JOBID':<55} {'PID':<8} {'STARTED':<22} RC"
    print(header)
    print("-" * len(header))
    for r in rows:
        state = (
            "canceled" if r.get("canceled") else
            "failed"   if r.get("failed") else
            "running"  if r.get("running") else
            "done"     if r.get("running") is False else
            "pending"
        )
        print(f"{state:<10} {str(r.get('jobid','?')):<55} "
              f"{str(r.get('pid') or '-'):<8} "
              f"{str(r.get('started') or '-'):<22} "
              f"{r.get('returncode') if r.get('returncode') is not None else '-'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="show status of a jobid")
    p_status.add_argument("jobid")
    p_status.add_argument("--json", action="store_true", help="also print full log JSON")
    p_status.set_defaults(func=cmd_status)

    p_cancel = sub.add_parser("cancel", help="cancel a running job")
    p_cancel.add_argument("jobid")
    p_cancel.set_defaults(func=cmd_cancel)

    p_list = sub.add_parser("list", help="list all known jobs")
    p_list.add_argument("--active", action="store_true",
                        help="show only running jobs")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

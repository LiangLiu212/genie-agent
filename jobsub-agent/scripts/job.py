#!/usr/bin/env python3
"""Grid job control surface: status / list / cancel / fetchlog.

    pixi run python jobsub-agent/scripts/job.py status   <jobid>
    pixi run python jobsub-agent/scripts/job.py list      [--active]
    pixi run python jobsub-agent/scripts/job.py cancel    <jobid>
    pixi run python jobsub-agent/scripts/job.py fetchlog  <jobid>

`status`/`list` re-poll `jobsub_q` for non-terminal jobs and persist the result
into the per-job `.gridlog`. (`pull` is added with lib/outputs.py.)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_ROOT))

from lib import control, monitor, outputs, records   # noqa: E402
from lib.config import load_config                    # noqa: E402


def _fmt(rec: dict) -> str:
    return (f"{rec.get('jobid',''):<46} {rec.get('status',''):<10} "
            f"n={rec.get('n_jobs',0):<5} done={rec.get('processes_done',0):<5} "
            f"{rec.get('cluster_id','') or '-'}")


def cmd_status(args, cfg) -> int:
    path = records.find_record_for_jobid(args.jobid)
    rec = monitor.refresh_status(path, cfg)
    print(f"jobid:      {rec['jobid']}")
    print(f"status:     {rec['status']}")
    print(f"cluster:    {rec.get('cluster_id') or '-'}")
    print(f"n_jobs:     {rec['n_jobs']}   processes_done: {rec.get('processes_done',0)}"
          f" ({rec.get('processes_done_source') or '-'})")
    print(f"submitted:  {rec.get('submitted')}   finished: {rec.get('finished') or '-'}")
    print(f"record:     {path}")
    if rec.get("fetchlog_error"):
        print(f"fetchlog_error: {rec['fetchlog_error']}")
    cs = rec.get("cluster_state")
    if cs:
        print(f"queue:      total={cs.get('n_total',0)} idle={cs.get('n_idle',0)} "
              f"running={cs.get('n_running',0)} held={cs.get('n_held',0)} "
              f"done={cs.get('n_done',0)}" + (f"  ({cs['error']})" if cs.get("error") else ""))
    return 0


def cmd_list(args, cfg) -> int:
    jobs = monitor.list_jobs(cfg, active_only=args.active)
    if not jobs:
        print("(no jobs)")
        return 0
    for rec in jobs:
        print(_fmt(rec))
    print(f"\n{len(jobs)} job(s)" + (" (active)" if args.active else ""))
    return 0


def cmd_cancel(args, cfg) -> int:
    path = records.find_record_for_jobid(args.jobid)
    rec = control.cancel(path, cfg)
    print(f"{rec['jobid']}: {rec['status']}  ({rec.get('_cancel_detail','')})")
    return 0


def cmd_fetchlog(args, cfg) -> int:
    path = records.find_record_for_jobid(args.jobid)
    res = control.fetch_log(path, cfg)
    if "error" in res:
        sys.stderr.write(f"error: {res['error']}\n")
        return 1
    print(f"fetched {res['n_files']} file(s) -> {res['dest_dir']} (rc={res['returncode']})")
    return 0


def cmd_pull(args, cfg) -> int:
    path = records.find_record_for_jobid(args.jobid)
    res = outputs.pull(path, cfg, suffix=args.suffix, overwrite=args.overwrite)
    if "error" in res:
        sys.stderr.write(f"error: {res['error']}\n")
        return 1
    print(res["message"])
    for f in res.get("failures", [])[:10]:
        sys.stderr.write(f"  FAIL: {f}\n")
    return 1 if res.get("status") == "failed" else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="jobsub-agent grid job control")
    ap.add_argument("--config", default=None, help="path to jobsub.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="re-poll + show one job"); p.add_argument("jobid")
    p = sub.add_parser("list", help="list jobs"); p.add_argument("--active", action="store_true")
    p = sub.add_parser("cancel", help="jobsub_rm a job"); p.add_argument("jobid")
    p = sub.add_parser("fetchlog", help="jobsub_fetchlog a job"); p.add_argument("jobid")
    p = sub.add_parser("pull", help="ifdh-pull outputs to local disk")
    p.add_argument("jobid"); p.add_argument("--suffix", default=None,
                   help="only pull files ending with this (e.g. .ghep.root)")
    p.add_argument("--overwrite", action="store_true")

    args = ap.parse_args()
    cfg = load_config(args.config)
    return {"status": cmd_status, "list": cmd_list, "cancel": cmd_cancel,
            "fetchlog": cmd_fetchlog, "pull": cmd_pull}[args.cmd](args, cfg)


if __name__ == "__main__":
    sys.exit(main())

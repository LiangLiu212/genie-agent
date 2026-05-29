#!/usr/bin/env python3
"""Tarball build + CVMFS publish/catalog CLI (GENIE-agnostic).

    # build a generic tarball of selected top-level trees under a dir
    pixi run python jobsub-agent/scripts/tarball.py build --build-dir /abs/install \
        --toplevel Generator --toplevel data [--exclude-component src] [--force]

    # publish an existing local tarball to RCDS/CVMFS under a label (sentinel job)
    pixi run python jobsub-agent/scripts/tarball.py publish --tarball /abs/x.tar --label main

    pixi run python jobsub-agent/scripts/tarball.py list [--verify]
    pixi run python jobsub-agent/scripts/tarball.py verify --label main
    pixi run python jobsub-agent/scripts/tarball.py label-from-job --label main --jobid <jobid>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_ROOT))

from lib import publish, tarball       # noqa: E402
from lib.config import load_config     # noqa: E402


def cmd_build(args, _cfg) -> int:
    res = tarball.build_tarball(
        build_dir=args.build_dir, toplevel_candidates=args.toplevel or [],
        exclude_components=args.exclude_component or (),
        exclude_prefixes=args.exclude_prefix or (),
        exclude_suffixes=tuple(args.exclude_suffix or ()),
        name_prefix=args.name_prefix, output_path=args.output,
        force=args.force, background=args.background,
    )
    if "error" in res:
        sys.stderr.write(f"error: {res['error']}\n")
        return 2
    print(res["message"])
    print(f"  tarball: {res['tarball_path']}")
    print(f"  included: {res['files_included']}")
    return 0


def cmd_publish(args, cfg) -> int:
    res = publish.publish_and_catalog(
        cfg, tarball_path=str(Path(args.tarball).resolve()), label=args.label,
        overwrite=args.overwrite, description=args.description or "",
    )
    if "error" in res:
        sys.stderr.write(f"error: {res['error']}\n")
        return 1
    print(f"published '{args.label}' -> {res['cvmfs_tar_file']}")
    return 0


def cmd_list(args, _cfg) -> int:
    catalog = publish.load_catalog()
    entries = list(catalog["entries"].values())
    entries.sort(key=lambda e: e.get("published", ""), reverse=True)
    if not entries:
        print("(catalog empty)")
        return 0
    for e in entries:
        line = f"{e['label']:<28} {e.get('published','')[:19]:<20} {e.get('cvmfs_tar_file','')}"
        if args.verify:
            v = publish.verify_cvmfs(e)
            line += f"   [{v['status']}/{v['recommendation']} age={v['age_days']}d]"
        print(line)
    if args.verify:
        publish.save_catalog(catalog)
    return 0


def cmd_verify(args, _cfg) -> int:
    entry = publish.lookup_catalog(args.label)
    if entry is None:
        sys.stderr.write(f"error: label '{args.label}' not in catalog\n")
        return 1
    v = publish.verify_cvmfs(entry)
    catalog = publish.load_catalog()
    catalog["entries"][args.label] = entry
    publish.save_catalog(catalog)
    print(f"{args.label}: {v['status']} / {v['recommendation']} (age {v['age_days']}d) — {v['reason']}")
    return 0


def cmd_label_from_job(args, cfg) -> int:
    res = publish.label_from_job(cfg, label=args.label, jobid=args.jobid,
                                 description=args.description or "", overwrite=args.overwrite)
    if "error" in res:
        sys.stderr.write(f"error: {res['error']}\n")
        return 1
    print(f"adopted '{args.label}' -> {res['cvmfs_tar_file']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="jobsub-agent tarball build/publish/catalog")
    ap.add_argument("--config", default=None, help="path to jobsub.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build", help="build (or reuse cached) a tarball")
    p.add_argument("--build-dir", required=True)
    p.add_argument("--toplevel", action="append", help="top-level tree to include (repeatable)")
    p.add_argument("--exclude-component", action="append", help="drop any path with this component")
    p.add_argument("--exclude-prefix", action="append", help="drop paths starting with this")
    p.add_argument("--exclude-suffix", action="append", help="drop paths ending with this")
    p.add_argument("--name-prefix", default="tarball")
    p.add_argument("--output", default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--background", action="store_true")

    p = sub.add_parser("publish", help="publish a local tarball to CVMFS under a label")
    p.add_argument("--tarball", required=True); p.add_argument("--label", required=True)
    p.add_argument("--description", default=None); p.add_argument("--overwrite", action="store_true")

    p = sub.add_parser("list", help="list catalog entries"); p.add_argument("--verify", action="store_true")
    p = sub.add_parser("verify", help="verify one catalog entry"); p.add_argument("--label", required=True)
    p = sub.add_parser("label-from-job", help="adopt a published tarball from a job's submit log")
    p.add_argument("--label", required=True); p.add_argument("--jobid", required=True)
    p.add_argument("--description", default=None); p.add_argument("--overwrite", action="store_true")

    args = ap.parse_args()
    # `build`/`list` don't need jobsub bins; load config lazily for the rest.
    cfg = {} if args.cmd in ("build", "list", "verify") else load_config(args.config)
    return {"build": cmd_build, "publish": cmd_publish, "list": cmd_list,
            "verify": cmd_verify, "label-from-job": cmd_label_from_job}[args.cmd](args, cfg)


if __name__ == "__main__":
    sys.exit(main())

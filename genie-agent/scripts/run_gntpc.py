#!/usr/bin/env python3
"""Convert a GENIE GHEP event file to a flat analysis format via `gntpc`.

Backgrounded by default: writes `<stem>.log` immediately and returns a jobid;
a detached supervisor runs gntpc and updates the log. Use `--foreground` to
block until completion.

No `--tune/--probe/--target`: the output path is derived from the input's
filename, and metadata (tune, probe, target, source jobid) is inherited from
the input GHEP's sibling `.log` when present. This is the replacement for the
old path-regex crutch.

Smoke test (against a gevgen .ghep.root):
    pixi run python scripts/run_gntpc.py -i <events.ghep.root> -f gst --foreground

Track and cancel via `scripts/job.py status <jobid>` / `cancel <jobid>`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
_DEV_ROOT   = _AGENT_ROOT.parent
sys.path.insert(0, str(_AGENT_ROOT))
sys.path.insert(0, str(_DEV_ROOT / "runlog_tools"))

from runlog_tools import make_parser, args_to_inputs              # noqa: E402

from lib.config import load_config                                # noqa: E402
from lib.genie_env import (load_genie_env, resolve_gxmlpath,      # noqa: E402
                           with_gxmlpath)
from lib.jobs import launch_background, run_foreground, supervise # noqa: E402
from lib.paths import sha256_short                                # noqa: E402


RUNTYPE = "gntpc"

# Output file extension per gntpc format (from genie-mcp gntpc_tool.py).
_FORMAT_EXT: dict[str, str] = {
    "gst":                  ".gst.root",
    "gxml":                 ".gxml",
    "rootracker":           ".gtrac.root",
    "rootracker_mock_data": ".mockd.gtrac.root",
    "t2k_rootracker":       ".gtrac.root",
    "numi_rootracker":      ".gtrac.root",
    "t2k_tracker":          ".gtrac.dat",
    "nuance_tracker":       ".gtrac_legacy.dat",
    "ghad":                 ".ghad.dat",
    "ginuke":               ".ginuke.root",
}


def _source_stem(input_path: Path) -> str:
    """Strip `.ghep.root` (or `.root`) to get the source stem."""
    name = input_path.name
    for suffix in (".ghep.root", ".root"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _read_source_meta(input_path: Path, source_stem: str) -> dict:
    """Inherit metadata from the input GHEP's sibling `<stem>.log`, if present."""
    log_path = input_path.parent / f"{source_stem}.log"
    meta: dict = {"source_log": None}
    if log_path.is_file():
        try:
            rec = json.loads(log_path.read_text())
            ins = rec.get("inputs", {})
            meta = {
                "source_log":       str(log_path),
                "source_jobid":     rec.get("jobid"),
                "tune_resolved":    ins.get("tune_resolved"),
                "genlist_resolved": ins.get("genlist_resolved"),
                "canonical_probe":  ins.get("canonical_probe")  or ins.get("canonical_probes"),
                "canonical_target": ins.get("canonical_target") or ins.get("canonical_targets"),
                "source_installation": ins.get("installation"),
            }
        except Exception:
            pass
    return meta


def main() -> int:
    parser = make_parser("Convert a GENIE GHEP file to a flat format via gntpc.")
    parser.add_argument("-i", "--input", default=None,
                        help="Input GHEP ROOT file (gevgen output)")
    parser.add_argument("-f", "--format", default="gst",
                        choices=sorted(_FORMAT_EXT),
                        help="Output format (default: gst)")
    parser.add_argument("-o", "--output-file", default=None,
                        help="Output path; derived from input filename if omitted")
    parser.add_argument("-n", "--n-events", type=int, default=None,
                        help="Number of events to convert (default: all)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--installation", default=None,
                        help="Override active installation (else env / config)")
    parser.add_argument("--gxmlpath", action="append", default=None,
                        metavar="DIR",
                        help="Custom-tune dir prepended to GXMLPATH (repeatable "
                             "or colon-separated). GENIE searches it before "
                             "$GENIE/config.")
    parser.add_argument("--label", default=None,
                        help="Free-text label saved into the runlog")
    parser.add_argument("--foreground", action="store_true",
                        help="Block until the GENIE binary finishes (default: detach)")
    parser.add_argument("--supervise", action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument("--log-path", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--env-path", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.supervise:
        if not args.log_path or not args.env_path:
            sys.stderr.write("error: --supervise requires --log-path and --env-path\n")
            return 2
        return supervise(
            log_path=Path(args.log_path),
            env_path=Path(args.env_path),
        )

    if not args.input:
        sys.stderr.write("error: -i/--input is required\n")
        return 2

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        sys.stderr.write(f"error: input GHEP file not found: {input_path}\n")
        return 2
    if args.n_events is not None and args.n_events <= 0:
        sys.stderr.write(f"error: n_events must be > 0, got {args.n_events}\n")
        return 2

    cfg = load_config(args.installation)
    env = load_genie_env(cfg)

    gxmlpath_dirs = resolve_gxmlpath(args.gxmlpath)
    for d in gxmlpath_dirs:
        if not Path(d).is_dir():
            sys.stderr.write(f"error: --gxmlpath dir not found: {d}\n")
            return 2
    env = with_gxmlpath(env, gxmlpath_dirs)

    source_stem = _source_stem(input_path)
    src_meta    = _read_source_meta(input_path, source_stem)

    # Output lands next to the source GHEP. Job artefacts (log/stdout/stderr)
    # carry a `.<fmt>` infix so they never clobber the source's `<stem>.log`.
    run_dir   = input_path.parent
    job_stem  = f"{source_stem}.{args.format}"
    output    = (Path(args.output_file).resolve() if args.output_file
                 else run_dir / f"{source_stem}{_FORMAT_EXT[args.format]}")
    stdout_log = run_dir / f"{job_stem}.stdout"
    stderr_log = run_dir / f"{job_stem}.stderr"

    binary = Path(cfg["genie_bin_dir"]) / "gntpc"
    cmd: list[str] = [
        str(binary),
        "-i", str(input_path),
        "-f", args.format,
        "-o", str(output),
    ]
    if args.n_events is not None:    cmd += ["-n", str(args.n_events)]
    if args.seed is not None:        cmd += ["--seed", str(args.seed)]

    inputs = args_to_inputs(args, exclude=("supervise", "log_path",
                                          "env_path", "foreground")) | {
        "installation":  cfg["installation_name"],
        "gxmlpath":      gxmlpath_dirs,
        "input":         str(input_path),
        "input_sha256":  sha256_short(input_path),
        "source_stem":   source_stem,
        **src_meta,
    }

    outputs = {
        "output_file":    str(output),
        "primary_output": str(output),
        "stdout_log":     str(stdout_log),
        "stderr_log":     str(stderr_log),
        "run_dir":        str(run_dir),
        "stem":           job_stem,
        "warnings":       [],
        "genie_command":  " ".join(cmd),
    }

    tgt = src_meta.get("canonical_target")
    prb = src_meta.get("canonical_probe")
    who = f"{prb} on {tgt} " if (prb and tgt) else ""
    desc = f"gntpc {who}-> {args.format} from {input_path.name}"

    if args.foreground:
        return run_foreground(
            runtype=RUNTYPE, script=Path(__file__).resolve(),
            command=cmd, env=env, cwd=run_dir, stem=job_stem,
            description=desc, inputs=inputs, outputs=outputs,
        )

    jobid = launch_background(
        runtype=RUNTYPE, script=Path(__file__).resolve(),
        command=cmd, env=env, cwd=run_dir, stem=job_stem,
        description=desc, inputs=inputs, outputs=outputs,
    )
    print(f"jobid: {jobid}")
    print(f"log:   {run_dir / f'{job_stem}.log'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

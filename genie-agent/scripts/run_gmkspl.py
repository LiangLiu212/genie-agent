#!/usr/bin/env python3
"""Generate GENIE cross-section splines via `gmkspl`.

Backgrounded by default: writes `<stem>.log` immediately and returns a jobid;
a detached supervisor runs gmkspl and updates the log. Use `--foreground` to
block until completion.

Smoke test:
    pixi run python scripts/run_gmkspl.py \
        --probes numu --targets H1 --tune G18_02a_00_000 \
        --genlist CCQE -n 30 -e 5

Track and cancel via `scripts/job.py status <jobid>` / `cancel <jobid>`.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
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
from lib.paths import new_run_dir, run_stem, sha256_short         # noqa: E402
from lib.pdg import resolve_pdg, canonical_probe, canonical_target  # noqa: E402
from lib.validation import validate_gmkspl_inputs                 # noqa: E402


RUNTYPE = "gmkspl"


def main() -> int:
    parser = make_parser("Generate GENIE cross-section splines via gmkspl.")
    parser.add_argument("--probes",
                        help="Comma-separated probe PDGs/aliases (e.g. 'numu,numubar', 'eminus')")
    parser.add_argument("--targets",
                        help="Comma-separated target PDGs/aliases (e.g. 'Ar40,C12')")
    parser.add_argument("--tune", default=None,
                        help="GENIE tune (defaults to config default_tune)")
    parser.add_argument("--genlist", default=None,
                        help="Event generator list (defaults to config default_generator_list)")
    parser.add_argument("-n", "--n-knots", type=int, default=None,
                        help="Knots per spline (GENIE default ~200)")
    parser.add_argument("-e", "--max-energy", type=float, default=None,
                        help="Maximum spline energy in GeV (GENIE default 10)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--input-cross-sections", default=None,
                        help="Pre-existing XML to supplement (--input-cross-sections)")
    parser.add_argument("--output-file", default=None,
                        help="Output XML path; auto-generated under genie-runs/ if omitted")
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

    if not args.probes or not args.targets:
        sys.stderr.write("error: --probes and --targets are required\n")
        return 2

    cfg = load_config(args.installation)
    env = load_genie_env(cfg)

    gxmlpath_dirs = resolve_gxmlpath(args.gxmlpath)
    for d in gxmlpath_dirs:
        if not Path(d).is_dir():
            sys.stderr.write(f"error: --gxmlpath dir not found: {d}\n")
            return 2
    env = with_gxmlpath(env, gxmlpath_dirs)

    tune    = args.tune    or cfg["default_tune"]
    genlist = args.genlist or cfg["default_generator_list"]

    probe_aliases  = [p.strip() for p in args.probes.split(",")  if p.strip()]
    target_aliases = [t.strip() for t in args.targets.split(",") if t.strip()]

    try:
        probe_pdgs  = [resolve_pdg(p) for p in probe_aliases]
        target_pdgs = [resolve_pdg(t) for t in target_aliases]
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    canonical_probes  = [canonical_probe(p) for p in probe_pdgs]
    canonical_targets = [canonical_target(t) for t in target_pdgs]

    errors, warnings = validate_gmkspl_inputs(
        probe_pdgs, target_pdgs, tune, genlist,
        args.max_energy, args.n_knots, cfg["genie_bin_dir"],
        gxmlpath_dirs=gxmlpath_dirs,
    )
    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    if errors:
        for e in errors:
            sys.stderr.write(f"error: {e}\n")
        return 2

    now     = datetime.now()
    run_dir = new_run_dir(tune, when=now)
    stem    = run_stem(canonical_probes, canonical_targets, when=now)

    output_xml = (Path(args.output_file).resolve() if args.output_file
                  else run_dir / f"{stem}.xml")
    stdout_log = run_dir / f"{stem}.stdout"
    stderr_log = run_dir / f"{stem}.stderr"

    # Resolve to absolute: the supervisor runs gmkspl with cwd=run_dir, so a
    # relative --input-cross-sections would be looked up against the wrong dir.
    input_xsec = (str(Path(args.input_cross_sections).resolve())
                  if args.input_cross_sections else None)

    binary = Path(cfg["genie_bin_dir"]) / "gmkspl"
    cmd: list[str] = [
        str(binary),
        "-p", ",".join(str(p) for p in probe_pdgs),
        "-t", ",".join(str(t) for t in target_pdgs),
        "-o", str(output_xml),
    ]
    if args.n_knots is not None:        cmd += ["-n", str(args.n_knots)]
    if args.max_energy is not None:     cmd += ["-e", str(args.max_energy)]
    if args.seed is not None:           cmd += ["--seed", str(args.seed)]
    if input_xsec:
        cmd += ["--input-cross-sections", input_xsec]
    cmd += ["--tune", tune, "--event-generator-list", genlist]

    inputs = args_to_inputs(args, exclude=("supervise", "log_path",
                                          "env_path", "foreground")) | {
        "installation":       cfg["installation_name"],
        "tune_resolved":      tune,
        "genlist_resolved":   genlist,
        "probe_pdgs":         probe_pdgs,
        "target_pdgs":        target_pdgs,
        "canonical_probes":   canonical_probes,
        "canonical_targets":  canonical_targets,
        "gxmlpath":           gxmlpath_dirs,
    }
    if input_xsec:
        inputs["input_cross_sections"]        = input_xsec
        inputs["input_cross_sections_sha256"] = sha256_short(input_xsec)

    outputs = {
        "output_xml":     str(output_xml),
        "primary_output": str(output_xml),
        "stdout_log":     str(stdout_log),
        "stderr_log":     str(stderr_log),
        "run_dir":        str(run_dir),
        "stem":           stem,
        "warnings":       warnings,
        "genie_command":  " ".join(cmd),
    }

    desc = f"gmkspl {','.join(canonical_probes)} on {','.join(canonical_targets)} [{tune}/{genlist}]"

    if args.foreground:
        return run_foreground(
            runtype=RUNTYPE, script=Path(__file__).resolve(),
            command=cmd, env=env, cwd=run_dir, stem=stem,
            description=desc, inputs=inputs, outputs=outputs,
        )

    jobid = launch_background(
        runtype=RUNTYPE, script=Path(__file__).resolve(),
        command=cmd, env=env, cwd=run_dir, stem=stem,
        description=desc, inputs=inputs, outputs=outputs,
    )
    print(f"jobid: {jobid}")
    print(f"log:   {run_dir / f'{stem}.log'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

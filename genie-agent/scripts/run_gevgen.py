#!/usr/bin/env python3
"""Generate GENIE neutrino events via `gevgen` (mono-energetic).

Backgrounded by default: writes `<stem>.log` immediately and returns a jobid;
a detached supervisor runs gevgen and updates the log. Use `--foreground` to
block until completion.

Mono-energetic only for now — `--energy` is a scalar in GeV. Flux / energy-range
mode is not wired up yet.

Smoke test:
    pixi run python scripts/run_gevgen.py \
        --probe numu --target C12 -n 100 -e 3.0 \
        --cross-sections <spline.xml> --tune G18_02a_00_000 --genlist CCQE

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
from lib.genie_env import load_genie_env                          # noqa: E402
from lib.jobs import launch_background, run_foreground, supervise # noqa: E402
from lib.paths import new_run_dir, run_stem, sha256_short         # noqa: E402
from lib.pdg import resolve_pdg, canonical_probe, canonical_target  # noqa: E402
from lib.validation import validate_gevgen_inputs                 # noqa: E402


RUNTYPE = "gevgen"


def main() -> int:
    parser = make_parser("Generate GENIE neutrino events via gevgen (mono-energetic).")
    parser.add_argument("--probe",
                        help="Neutrino probe PDG/alias (e.g. 'numu', 14)")
    parser.add_argument("--target",
                        help="Target nucleus PDG/alias (e.g. 'Ar40', 'C12')")
    parser.add_argument("-n", "--n-events", type=int, default=None,
                        help="Number of events to generate")
    parser.add_argument("-e", "--energy", type=float, default=None,
                        help="Mono-energetic neutrino energy in GeV")
    parser.add_argument("--cross-sections", default=None,
                        help="Pre-computed spline XML (--cross-sections); required")
    parser.add_argument("--tune", default=None,
                        help="GENIE tune (defaults to config default_tune)")
    parser.add_argument("--genlist", default=None,
                        help="Event generator list (defaults to config default_generator_list)")
    parser.add_argument("-r", "--run-number", type=int, default=None,
                        help="MC run number (-r)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output-file", default=None,
                        help="Output GHEP path; auto-generated under genie-runs/ if omitted")
    parser.add_argument("--installation", default=None,
                        help="Override active installation (else env / config)")
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

    if not args.probe or not args.target:
        sys.stderr.write("error: --probe and --target are required\n")
        return 2
    if not args.cross_sections:
        sys.stderr.write("error: --cross-sections is required\n")
        return 2

    cfg = load_config(args.installation)
    env = load_genie_env(cfg)

    tune    = args.tune    or cfg["default_tune"]
    genlist = args.genlist or cfg["default_generator_list"]

    try:
        probe_pdg  = resolve_pdg(args.probe.strip())
        target_pdg = resolve_pdg(args.target.strip())
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    canon_probe  = canonical_probe(probe_pdg)
    canon_target = canonical_target(target_pdg)

    # Resolve to absolute: the supervisor runs gevgen with cwd=run_dir, so a
    # relative --cross-sections would be looked up against the wrong directory.
    cross_sections = str(Path(args.cross_sections).resolve())

    errors, warnings = validate_gevgen_inputs(
        probe_pdg, target_pdg, args.n_events, args.energy,
        cross_sections, tune, cfg["genie_bin_dir"],
    )
    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    if errors:
        for e in errors:
            sys.stderr.write(f"error: {e}\n")
        return 2

    now     = datetime.now()
    run_dir = new_run_dir(tune, when=now)
    stem    = run_stem([canon_probe], [canon_target], when=now)

    output_ghep = (Path(args.output_file).resolve() if args.output_file
                   else run_dir / f"{stem}.ghep.root")
    stdout_log = run_dir / f"{stem}.stdout"
    stderr_log = run_dir / f"{stem}.stderr"

    binary = Path(cfg["genie_bin_dir"]) / "gevgen"
    cmd: list[str] = [
        str(binary),
        "-p", str(probe_pdg),
        "-t", str(target_pdg),
        "-n", str(args.n_events),
        "-e", str(args.energy),
        "--cross-sections", cross_sections,
        "-o", str(output_ghep),
    ]
    if args.run_number is not None:    cmd += ["-r", str(args.run_number)]
    if args.seed is not None:          cmd += ["--seed", str(args.seed)]
    cmd += ["--tune", tune, "--event-generator-list", genlist]

    inputs = args_to_inputs(args, exclude=("supervise", "log_path",
                                          "env_path", "foreground")) | {
        "installation":      cfg["installation_name"],
        "tune_resolved":     tune,
        "genlist_resolved":  genlist,
        "probe_pdg":         probe_pdg,
        "target_pdg":        target_pdg,
        "canonical_probe":   canon_probe,
        "canonical_target":  canon_target,
        "cross_sections":        cross_sections,
        "cross_sections_sha256": sha256_short(cross_sections),
    }

    outputs = {
        "output_ghep":    str(output_ghep),
        "primary_output": str(output_ghep),
        "stdout_log":     str(stdout_log),
        "stderr_log":     str(stderr_log),
        "run_dir":        str(run_dir),
        "stem":           stem,
        "warnings":       warnings,
        "genie_command":  " ".join(cmd),
    }

    desc = (f"gevgen {canon_probe} on {canon_target} "
            f"@ {args.energy} GeV, n={args.n_events} [{tune}/{genlist}]")

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

#!/usr/bin/env python3
"""Generate GENIE boosted-dark-matter cross-section splines via `gmkspl_dm`.

Same shape as run_gmkspl.py (parse -> config -> env -> validate -> argv ->
background/foreground), but for the BDM app: the probe is implicit
(kPdgDarkMatter = 2000010000, canonical alias `dm`) and the model parameters
are `--mass` (DM mass, GeV), `--med-ratio` (mediator/DM mass ratio, GENIE
default 0.5) and `--zp-coupling` (Z' coupling, GENIE default 1.0 from
CommonParam BoostedDarkMatter). Needs an installation built with
`--enable-boosted-dark-matter` and a GDM* tune (e.g. GDM18_00a_00_000).

Spline keys carry only `dm;tgt:<pdg>;...` — NOT the mass / ratio / coupling —
so one XML per (mass, z, g); the values live in `inputs` of the runlog and
should go into the merged product's filename.

Backgrounded by default: writes `<stem>.log` immediately and returns a jobid;
a detached supervisor runs gmkspl_dm and updates the log. Use `--foreground`
to block until completion.

Smoke test:
    pixi run python scripts/run_gmkspl_dm.py \
        --targets Ar40 --mass <GeV> --tune GDM18_00a_00_000 \
        --genlist DMEL -n 10 -e 10 --foreground

Track and cancel via `scripts/job.py status <jobid>` / `cancel <jobid>`.
"""
from __future__ import annotations

import argparse
import secrets
import sys
from datetime import datetime
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
_DEV_ROOT   = _AGENT_ROOT.parent
sys.path.insert(0, str(_AGENT_ROOT))
sys.path.insert(0, str(_DEV_ROOT / "runlog_tools"))

from runlog_tools import make_parser, args_to_inputs              # noqa: E402

from lib.config import load_config                                # noqa: E402
from lib.genie_env import (env_sha256, genie_install_git,         # noqa: E402
                           load_genie_env, resolve_gxmlpath, with_gxmlpath)
from lib.jobs import launch_background, run_foreground, supervise # noqa: E402
from lib.paths import new_run_dir, run_stem, sha256_short         # noqa: E402
from lib.pdg import resolve_pdg, canonical_probe, canonical_target  # noqa: E402
from lib.validation import tune_xml_hashes, validate_gmkspl_dm_inputs  # noqa: E402


RUNTYPE = "gmkspl_dm"
DM_PROBE_ALIAS = "dm"          # -> 2000010000 via shared/pdg.json
DEFAULT_GENLIST = "Default"    # GDM18_00a: DMEL + DMDIS + DME + DMRES


def main() -> int:
    parser = make_parser("Generate GENIE boosted-dark-matter splines via gmkspl_dm.")
    parser.add_argument("--targets",
                        help="Comma-separated target PDGs/aliases (e.g. 'Ar40,C12')")
    parser.add_argument("--mass", dest="dm_mass", type=float, default=None,
                        help="Dark-matter mass in GeV (gmkspl_dm -m); required")
    parser.add_argument("--med-ratio", dest="med_ratio", type=float, default=0.5,
                        help="Mediator-to-DM mass ratio (gmkspl_dm -z; GENIE default 0.5)")
    parser.add_argument("--zp-coupling", dest="zp_coupling", type=float, default=1.0,
                        help="Z' coupling (gmkspl_dm -g; GENIE default 1.0)")
    parser.add_argument("--tune", default=None,
                        help="GENIE DM tune, e.g. GDM18_00a_00_000; required "
                             "(the config default_tune is a neutrino tune)")
    parser.add_argument("--genlist", default=DEFAULT_GENLIST,
                        help=f"Event generator list (default '{DEFAULT_GENLIST}'; "
                             "per-process: DMEL, DMDIS, DME, DMRES)")
    parser.add_argument("-n", "--n-knots", type=int, default=None,
                        help="Knots per spline (GENIE default: 15/decade, min 30)")
    parser.add_argument("-e", "--max-energy", type=float, default=None,
                        help="Maximum spline energy in GeV (DM total energy)")
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

    if not args.targets:
        sys.stderr.write("error: --targets is required\n")
        return 2
    if args.dm_mass is None:
        sys.stderr.write("error: --mass (DM mass in GeV) is required\n")
        return 2
    if not args.tune:
        sys.stderr.write("error: --tune is required (e.g. GDM18_00a_00_000); "
                         "the config default_tune is a neutrino tune\n")
        return 2

    cfg = load_config(args.installation)
    base_env = load_genie_env(cfg)

    gxmlpath_dirs = resolve_gxmlpath(args.gxmlpath)
    for d in gxmlpath_dirs:
        if not Path(d).is_dir():
            sys.stderr.write(f"error: --gxmlpath dir not found: {d}\n")
            return 2
    env = with_gxmlpath(base_env, gxmlpath_dirs)

    tune    = args.tune
    genlist = args.genlist or DEFAULT_GENLIST

    target_aliases = [t.strip() for t in args.targets.split(",") if t.strip()]
    try:
        probe_pdg   = resolve_pdg(DM_PROBE_ALIAS)
        target_pdgs = [resolve_pdg(t) for t in target_aliases]
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    canonical_probes  = [canonical_probe(probe_pdg)]
    canonical_targets = [canonical_target(t) for t in target_pdgs]

    errors, warnings = validate_gmkspl_dm_inputs(
        target_pdgs, tune, genlist,
        args.dm_mass, args.med_ratio, args.zp_coupling,
        args.max_energy, args.n_knots, cfg["genie_bin_dir"],
        gxmlpath_dirs=gxmlpath_dirs,
    )
    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    if errors:
        for e in errors:
            sys.stderr.write(f"error: {e}\n")
        return 2

    binary = Path(cfg["genie_bin_dir"]) / "gmkspl_dm"
    if not binary.is_file():
        sys.stderr.write(
            f"error: {binary} not found; the installation must be built with "
            "./configure --enable-boosted-dark-matter\n"
        )
        return 2

    # Materialize the RNG seed (splines are integrals and effectively
    # seed-insensitive, but a concrete seed keeps the runlog uniform).
    if args.seed is None:
        args.seed = secrets.randbelow(2**31)

    now     = datetime.now()
    run_dir = new_run_dir(tune, when=now)
    stem    = run_stem(canonical_probes, canonical_targets, when=now)

    output_xml = (Path(args.output_file).resolve() if args.output_file
                  else run_dir / f"{stem}.xml")
    stdout_log = run_dir / f"{stem}.stdout"
    stderr_log = run_dir / f"{stem}.stderr"

    # Resolve to absolute: the supervisor runs the binary with cwd=run_dir.
    input_xsec = (str(Path(args.input_cross_sections).resolve())
                  if args.input_cross_sections else None)

    cmd: list[str] = [
        str(binary),
        "-m", str(args.dm_mass),
        "-t", ",".join(str(t) for t in target_pdgs),
        "-o", str(output_xml),
        "-z", str(args.med_ratio),
        "-g", str(args.zp_coupling),
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
        "probe_pdgs":         [probe_pdg],
        "target_pdgs":        target_pdgs,
        "canonical_probes":   canonical_probes,
        "canonical_targets":  canonical_targets,
        "gxmlpath":           gxmlpath_dirs,
        "tune_xml_sha256":    tune_xml_hashes(tune, cfg["genie_bin_dir"],
                                              gxmlpath_dirs=gxmlpath_dirs),
        "env_sha256":         env_sha256(base_env),
        "genie_bin_sha256":   sha256_short(binary),
        "genie_install_git":  genie_install_git(cfg),
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

    desc = (f"gmkspl_dm m={args.dm_mass} z={args.med_ratio} g={args.zp_coupling} "
            f"on {','.join(canonical_targets)} [{tune}/{genlist}]")

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

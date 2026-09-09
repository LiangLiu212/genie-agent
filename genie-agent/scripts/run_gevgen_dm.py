#!/usr/bin/env python3
"""Generate GENIE boosted-dark-matter events via `gevgen_dm`.

Same shape as run_gevgen.py (parse -> config -> env -> validate -> argv ->
background/foreground), but for the BDM app: the probe is implicit
(kPdgDarkMatter = 2000010000, canonical alias `dm`) and the model parameters
are `--mass` (DM mass, GeV), `--med-ratio` (mediator/DM mass ratio, GENIE
default 0.5) and `--zp-coupling` (Z' coupling, GENIE default 1.0).

Energy: `-e 3.0` is fixed-energy mode; `-e 0.1,10` is a range and then needs
`--flux` (`1` = flat, or a TF1 expression, a 2-column file, or
`file.root,hist`). gevgen_dm given a range without a flux silently runs at
fixed E = emin, so the runner rejects that. Flux mode writes `input-flux.root`
into the run dir (recorded as outputs.flux_hist).

Spline provenance: spline keys do not carry the DM mass / ratio / coupling, so
gevgen_dm happily uses splines built for another mass. When the spline XML has
a sibling `<stem>.log` from run_gmkspl_dm.py the runner cross-checks the three
values and refuses on mismatch; for merged products it can only warn.

Smoke test:
    pixi run python scripts/run_gevgen_dm.py \
        --target Ar40 --mass <GeV> -n 200 -e 0.1,10 --flux 1 \
        --cross-sections <spline.xml> --tune GDM18_00a_00_000 --foreground

Track and cancel via `scripts/job.py status <jobid>` / `cancel <jobid>`.
"""
from __future__ import annotations

import argparse
import json
import math
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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
from lib.validation import tune_xml_hashes, validate_gevgen_dm_inputs  # noqa: E402


RUNTYPE = "gevgen_dm"
DM_PROBE_ALIAS = "dm"          # -> 2000010000 via shared/pdg.json
DEFAULT_GENLIST = "Default"    # GDM18_00a: DMEL + DMDIS + DME + DMRES


def _parse_energy(text: str) -> tuple[Optional[float], Optional[float]]:
    """'3.0' -> (3.0, None); '0.1,10' -> (0.1, 10.0). Raises ValueError."""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) == 1:
        return float(parts[0]), None
    if len(parts) == 2:
        return float(parts[0]), float(parts[1])
    raise ValueError(f"energy must be 'E' or 'emin,emax', got {text!r}")


def _spline_provenance_check(cross_sections: str, dm_mass: float,
                             med_ratio: float, zp_coupling: float
                             ) -> tuple[list[str], list[str]]:
    """Compare -m/-z/-g with the spline's sibling gmkspl_dm runlog, if any."""
    errors: list[str] = []
    warnings: list[str] = []
    xml = Path(cross_sections)
    log = xml.with_suffix(".log") if xml.suffix == ".xml" else None
    rec = None
    if log is not None and log.is_file():
        try:
            rec = json.loads(log.read_text())
        except Exception:
            rec = None
    if rec is None or rec.get("runtype") != "gmkspl_dm":
        warnings.append(
            f"cannot verify the DM mass/ratio/coupling of {xml.name}: no sibling "
            "gmkspl_dm runlog (merged product?). Spline keys do not carry them; "
            f"make sure it was built with -m {dm_mass} -z {med_ratio} -g {zp_coupling}"
        )
        return errors, warnings
    ins = rec.get("inputs", {})
    for key, mine in (("dm_mass", dm_mass), ("med_ratio", med_ratio),
                      ("zp_coupling", zp_coupling)):
        theirs = ins.get(key)
        if theirs is None:
            warnings.append(f"spline runlog has no inputs.{key}; cannot cross-check")
        elif not math.isclose(float(theirs), float(mine), rel_tol=1e-9, abs_tol=0.0):
            errors.append(
                f"{key} mismatch: splines {xml.name} were built with {key}={theirs}, "
                f"this run asks for {mine} (spline keys carry no {key}; gevgen_dm "
                "would silently use the wrong cross sections)"
            )
    return errors, warnings


def main() -> int:
    parser = make_parser("Generate GENIE boosted-dark-matter events via gevgen_dm.")
    parser.add_argument("--target",
                        help="Target nucleus PDG/alias (e.g. 'Ar40', 'C12')")
    parser.add_argument("--mass", dest="dm_mass", type=float, default=None,
                        help="Dark-matter mass in GeV (gevgen_dm -m); required")
    parser.add_argument("--med-ratio", dest="med_ratio", type=float, default=0.5,
                        help="Mediator-to-DM mass ratio (gevgen_dm -z; GENIE default 0.5)")
    parser.add_argument("--zp-coupling", dest="zp_coupling", type=float, default=1.0,
                        help="Z' coupling (gevgen_dm -g; GENIE default 1.0)")
    parser.add_argument("-n", "--n-events", type=int, default=None,
                        help="Number of events to generate")
    parser.add_argument("-e", "--energy", default=None,
                        help="DM total energy in GeV: 'E' (fixed) or 'emin,emax' "
                             "(range; needs --flux)")
    parser.add_argument("-f", "--flux", default=None,
                        help="Flux for range mode: '1' (flat), a TF1 expression "
                             "in x, a 2-column text file, or 'file.root,hist'")
    parser.add_argument("--cross-sections", default=None,
                        help="Pre-computed DM spline XML (--cross-sections); required")
    parser.add_argument("--tune", default=None,
                        help="GENIE DM tune, e.g. GDM18_00a_00_000; required "
                             "(the config default_tune is a neutrino tune)")
    parser.add_argument("--genlist", default=DEFAULT_GENLIST,
                        help=f"Event generator list (default '{DEFAULT_GENLIST}')")
    parser.add_argument("-r", "--run-number", type=int, default=None,
                        help="MC run number (-r)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output-file", default=None,
                        help="Output GHEP path; auto-generated under genie-runs/ if omitted")
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

    if not args.target:
        sys.stderr.write("error: --target is required\n")
        return 2
    if args.dm_mass is None:
        sys.stderr.write("error: --mass (DM mass in GeV) is required\n")
        return 2
    if not args.energy:
        sys.stderr.write("error: -e/--energy is required ('E' or 'emin,emax')\n")
        return 2
    if not args.cross_sections:
        sys.stderr.write("error: --cross-sections is required\n")
        return 2
    if not args.tune:
        sys.stderr.write("error: --tune is required (e.g. GDM18_00a_00_000); "
                         "the config default_tune is a neutrino tune\n")
        return 2

    try:
        energy_min, energy_max = _parse_energy(args.energy)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
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

    try:
        probe_pdg  = resolve_pdg(DM_PROBE_ALIAS)
        target_pdg = resolve_pdg(args.target.strip())
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    canon_probe  = canonical_probe(probe_pdg)
    canon_target = canonical_target(target_pdg)

    # Resolve to absolute: the supervisor runs the binary with cwd=run_dir.
    cross_sections = str(Path(args.cross_sections).resolve())

    errors, warnings = validate_gevgen_dm_inputs(
        target_pdg, args.n_events, energy_min, energy_max, args.flux,
        args.dm_mass, args.med_ratio, args.zp_coupling,
        cross_sections, tune, genlist, cfg["genie_bin_dir"],
        gxmlpath_dirs=gxmlpath_dirs,
    )
    if not errors:
        e2, w2 = _spline_provenance_check(cross_sections, args.dm_mass,
                                          args.med_ratio, args.zp_coupling)
        errors += e2
        warnings += w2
    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    if errors:
        for e in errors:
            sys.stderr.write(f"error: {e}\n")
        return 2

    binary = Path(cfg["genie_bin_dir"]) / "gevgen_dm"
    if not binary.is_file():
        sys.stderr.write(
            f"error: {binary} not found; the installation must be built with "
            "./configure --enable-boosted-dark-matter\n"
        )
        return 2

    # Materialize the RNG seed so the runlog never records seed: null.
    if args.seed is None:
        args.seed = secrets.randbelow(2**31)

    now     = datetime.now()
    run_dir = new_run_dir(tune, when=now)
    stem    = run_stem([canon_probe], [canon_target], when=now)

    output_ghep = (Path(args.output_file).resolve() if args.output_file
                   else run_dir / f"{stem}.ghep.root")
    stdout_log = run_dir / f"{stem}.stdout"
    stderr_log = run_dir / f"{stem}.stderr"

    cmd: list[str] = [
        str(binary),
        "-m", str(args.dm_mass),
        "-t", str(target_pdg),
        "-n", str(args.n_events),
        "-e", args.energy.strip(),
        "-z", str(args.med_ratio),
        "-g", str(args.zp_coupling),
        "--cross-sections", cross_sections,
        "-o", str(output_ghep),
    ]
    if args.flux:                      cmd += ["-f", args.flux]
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
        "energy_min":        energy_min,
        "energy_max":        energy_max,
        "gxmlpath":          gxmlpath_dirs,
        "tune_xml_sha256":   tune_xml_hashes(tune, cfg["genie_bin_dir"],
                                             gxmlpath_dirs=gxmlpath_dirs),
        "env_sha256":        env_sha256(base_env),
        "genie_bin_sha256":  sha256_short(binary),
        "genie_install_git": genie_install_git(cfg),
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
    if args.flux:
        # gevgen_dm writes the sampled spectrum to ./input-flux.root (cwd=run_dir)
        outputs["flux_hist"] = str(run_dir / "input-flux.root")

    e_desc = (f"E={energy_min} GeV" if energy_max is None
              else f"E in [{energy_min},{energy_max}] GeV flux={args.flux}")
    desc = (f"gevgen_dm m={args.dm_mass} z={args.med_ratio} g={args.zp_coupling} "
            f"on {canon_target} {e_desc}, n={args.n_events} [{tune}/{genlist}]")

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

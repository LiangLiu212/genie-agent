#!/usr/bin/env python3
"""Submit a gevgen run to the DUNE grid via jobsub_lite (GENIE adapter).

Resolves PDGs from the shared pdg.json, validates the grid-specific rules,
looks up + verifies the published GENIE tarball (a CVMFS label), builds the
jobsub_submit argv + gevgen_grid.sh worker args, and hands them to lib.submit.

    pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
        --probe numu --target C12 -n 1000 -e 3.0 \
        --cross-sections /pnfs/.../spline.xml \
        --tune G18_02a_00_000 --genlist CCQE \
        --tarball-label genie_rc_main -N 100 [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_AGENT_ROOT))

from lib.config import load_config                       # noqa: E402
from lib.submit import submit                            # noqa: E402
from adapters.genie import common, pnfs                  # noqa: E402
from adapters.genie.pdg import (resolve_pdg, canonical_probe,  # noqa: E402
                                canonical_target, NEUTRINO_PDGS, CHARGED_LEPTON_PDGS)

RUNTYPE = "gevgen_grid"
KIND = "gev"


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit a gevgen run to the DUNE grid.")
    ap.add_argument("--probe", required=True, help="neutrino probe (alias/PDG, e.g. numu)")
    ap.add_argument("--target", required=True, help="target nucleus (e.g. C12, Ar40)")
    ap.add_argument("-n", "--n-events", type=int, required=True, help="events per process")
    ap.add_argument("-e", "--energy", required=True, help="mono-energetic neutrino energy (GeV)")
    ap.add_argument("--cross-sections", required=True, help="spline XML (absolute; /pnfs preferred)")
    ap.add_argument("--tarball-label", required=True, help="published GENIE tarball label (catalog)")
    ap.add_argument("--tune", default=None, help="GENIE tune (default: genie-agent default_tune)")
    ap.add_argument("--genlist", default=None, help="generator list (default: genie-agent default)")
    ap.add_argument("--installation", default=None,
                    help="must match genie-agent active_installation (else rejected); "
                         "use --config to point at a different genie-agent config")
    ap.add_argument("-N", "--n-jobs", type=int, default=100, help="number of grid processes")
    ap.add_argument("--tune-tarball-label", default=None, help="optional GXMLPATH overlay tarball label")
    ap.add_argument("--project", default=None, help="PNFS project dir (default: config default_project)")
    ap.add_argument("--project-name", default="JOBSUB_AGENT_GEVGEN")
    ap.add_argument("--disk", default=None)
    ap.add_argument("--role", default=None)
    ap.add_argument("--memory", default=None)
    ap.add_argument("--expected-lifetime", default=None)
    ap.add_argument("--append-condor-requirements", default=None)
    ap.add_argument("--config", default=None, help="path to jobsub.json")
    ap.add_argument("--dry-run", action="store_true", help="append --no_submit; record pending")
    args = ap.parse_args()

    cfg = load_config(args.config)
    tune = args.tune or common.default_tune()
    genlist = args.genlist or common.default_genlist()
    if not tune:
        sys.stderr.write("error: --tune required (no genie-agent default_tune found)\n"); return 2
    if not genlist:
        sys.stderr.write("error: --genlist required (no genie-agent default found)\n"); return 2
    project = args.project or cfg.get("default_project", "prd_paper")
    installation = common.resolve_installation(args.installation)

    try:
        probe_pdg = resolve_pdg(args.probe)
        target_pdg = resolve_pdg(args.target)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n"); return 2

    is_neutrino = probe_pdg in NEUTRINO_PDGS
    is_lepton = probe_pdg in CHARGED_LEPTON_PDGS

    cross_sections = (args.cross_sections if args.cross_sections.startswith("/pnfs/")
                      else str(Path(args.cross_sections).resolve()))

    errors: list[str] = []
    warnings: list[str] = []
    e, w = common.validate_common(is_lepton=is_lepton, is_neutrino=is_neutrino,
                                  tune=tune, genlist=genlist, n_jobs=args.n_jobs)
    errors += e; warnings += w
    errors += common.validate_target(target_pdg)
    if not (is_neutrino or is_lepton):
        warnings.append(f"probe PDG {probe_pdg} is neither neutrino nor charged lepton")
    if args.n_events <= 0:
        errors.append(f"n_events must be > 0, got {args.n_events}")
    if "," in str(args.energy):
        errors.append("energy-range/flux mode is not supported on the grid; pass a scalar energy")
    e, w = common.validate_cross_sections(cross_sections)
    errors += e; warnings += w

    tb = common.resolve_tarball(args.tarball_label)
    if "error" in tb:
        errors.append(tb["error"])
    elif tb.get("warn"):
        warnings.append(tb["warn"])

    tune_cvmfs = None
    if args.tune_tarball_label:
        tt = common.resolve_tarball(args.tune_tarball_label)
        if "error" in tt:
            errors.append(tt["error"])
        else:
            tune_cvmfs = tt["cvmfs_dir"]
            if tt.get("warn"):
                warnings.append(tt["warn"])

    for wmsg in warnings:
        sys.stderr.write(f"warning: {wmsg}\n")
    if errors:
        for emsg in errors:
            sys.stderr.write(f"error: {emsg}\n")
        return 2

    cvmfs_dir = tb["cvmfs_dir"]
    worker = _AGENT_ROOT / "adapters" / "genie" / "templates" / "gevgen_grid.sh"
    if not worker.exists() or not os.access(worker, os.X_OK):
        sys.stderr.write(f"error: worker script missing/not executable: {worker}\n"); return 2

    user = os.environ.get("USER", "")
    if not user:
        sys.stderr.write("error: $USER not set; cannot build PNFS path\n"); return 2

    canon_probe = canonical_probe(probe_pdg)
    canon_target = canonical_target(target_pdg)
    now = datetime.now()
    stem = f"{canon_probe}_{canon_target}_{now.strftime('%Y%m%d-%H%M%S')}"
    pnfs_dir = pnfs.output_dir(scratch_base=cfg["pnfs_scratch_base"], user=user, project=project,
                               installation=installation, tune=tune, genlist=genlist, stem=stem,
                               kind=KIND, probe=str(probe_pdg), target=str(target_pdg))

    spline_arg = cross_sections if cross_sections.startswith("/pnfs/") else f"file://{cross_sections}"
    role = args.role or cfg.get("default_role", "Analysis")
    disk = args.disk or cfg.get("default_disk", "20GB")
    req = args.append_condor_requirements or cfg.get("append_condor_requirements")

    cmd = [cfg["jobsub_bin"], "-G", cfg["default_group"], "--role", role, "--disk", disk,
           "-N", str(args.n_jobs)]
    if req:
        cmd += ["--append_condor_requirements", req]
    cmd += ["-f", spline_arg]
    if args.memory:
        cmd += ["--memory", args.memory]
    if args.expected_lifetime:
        cmd += ["--expected-lifetime", args.expected_lifetime]
    worker_args = [f"file://{worker}", "-p", str(probe_pdg), "-t", str(target_pdg),
                   "-e", str(args.energy), "-n", str(args.n_events), "-T", tune, "-L", genlist,
                   "-S", Path(cross_sections).name, "-j", stem, "-P", args.project_name,
                   "-O", pnfs_dir, "-R", cvmfs_dir]
    if tune_cvmfs:
        worker_args += ["-X", tune_cvmfs]
    cmd += worker_args

    inputs = [{"probe": canon_probe, "probe_pdg": probe_pdg, "target": canon_target,
               "target_pdg": target_pdg, "tune": tune, "genlist": genlist,
               "n_events": args.n_events, "energy": str(args.energy),
               "cross_sections": cross_sections, "tarball_label": args.tarball_label,
               "tune_tarball_label": args.tune_tarball_label, "installation": installation}]
    outputs = {"pnfs_output_dir": pnfs_dir, "genie_command": " ".join(cmd), "warnings": warnings}
    extra = {"adapter": "genie", "kind": KIND, "output_suffix": ".ghep.root",
             "channel": pnfs.channel_from_genlist(genlist), "probe": canon_probe,
             "target": canon_target, "tune": tune, "genlist": genlist, "installation": installation}

    record, gridlog = submit(
        runtype=RUNTYPE, stem=stem, submit_cmd=cmd, n_jobs=args.n_jobs, submit_user=user,
        worker_script=str(worker), tarball_path=cvmfs_dir, pnfs_output_dir=pnfs_dir,
        inputs=inputs, outputs=outputs, extra=extra, dry_run=args.dry_run, when=now,
    )

    print(f"jobid:  {record['jobid']}")
    line = f"status: {record['status']}"
    if record["cluster_id"]:
        line += f"  cluster: {record['cluster_id']}"
    print(line)
    print(f"record: {gridlog}")
    print(f"outputs: {pnfs_dir}  (pull: scripts/job.py pull {record['jobid']} --suffix .ghep.root)")
    if record.get("error"):
        sys.stderr.write(f"error:  {record['error']}\n")
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())

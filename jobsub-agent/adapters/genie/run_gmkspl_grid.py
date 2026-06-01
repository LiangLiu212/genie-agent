#!/usr/bin/env python3
"""Submit a gmkspl (cross-section spline) run to the DUNE grid (GENIE adapter).

Mirrors run_gevgen_grid.py but takes probe/target *lists*, optional n_knots /
max_energy / input-cross-sections, defaults -N to 1, and uses gmkspl_grid.sh.

    pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
        --probes numu,numubar --targets C12,Ar40 \
        --tune G18_02a_00_000 --genlist CCQE -e 10 -n 100 \
        --tarball-label genie_rc_main -N 1 [--dry-run]
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

RUNTYPE = "gmkspl_grid"
KIND = "spl"


def _split(values: list[str]) -> list[str]:
    """Flatten repeatable + comma-separated args into a token list."""
    out: list[str] = []
    for v in values or []:
        out += [t for t in v.split(",") if t]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit a gmkspl run to the DUNE grid.")
    ap.add_argument("--probes", action="append", required=True,
                    help="probe alias/PDG; repeatable or comma-separated")
    ap.add_argument("--targets", action="append", required=True,
                    help="target alias/PDG; repeatable or comma-separated")
    ap.add_argument("--tarball-label", required=True, help="published GENIE tarball label (catalog)")
    ap.add_argument("-n", "--n-knots", type=int, default=None, help="spline knots")
    ap.add_argument("-e", "--max-energy", type=float, default=None, help="max energy (GeV)")
    ap.add_argument("--input-cross-sections", default=None, help="pre-existing spline XML to extend")
    ap.add_argument("--tune", default=None, help="GENIE tune (default: genie-agent default_tune)")
    ap.add_argument("--genlist", default=None, help="generator list (default: genie-agent default)")
    ap.add_argument("--installation", default=None,
                    help="must match genie-agent active_installation (else rejected); "
                         "use --config to point at a different genie-agent config")
    ap.add_argument("-N", "--n-jobs", type=int, default=1, help="number of grid processes")
    ap.add_argument("--tune-tarball-label", default=None, help="optional GXMLPATH overlay tarball label")
    ap.add_argument("--project", default=None)
    ap.add_argument("--project-name", default="JOBSUB_AGENT_GMKSPL")
    ap.add_argument("--disk", default=None)
    ap.add_argument("--role", default=None)
    ap.add_argument("--memory", default=None)
    ap.add_argument("--expected-lifetime", default=None)
    ap.add_argument("--append-condor-requirements", default=None)
    ap.add_argument("--config", default=None, help="path to jobsub.json")
    ap.add_argument("--dry-run", action="store_true")
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
        nu_pdgs = [resolve_pdg(p) for p in _split(args.probes)]
        tgt_pdgs = [resolve_pdg(t) for t in _split(args.targets)]
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n"); return 2
    if not nu_pdgs or not tgt_pdgs:
        sys.stderr.write("error: --probes and --targets must be non-empty\n"); return 2

    is_lepton = any(p in CHARGED_LEPTON_PDGS for p in nu_pdgs)
    is_neutrino = any(p in NEUTRINO_PDGS for p in nu_pdgs)

    errors: list[str] = []
    warnings: list[str] = []
    if is_lepton and is_neutrino:
        errors.append("cannot mix neutrino and charged-lepton probes in one job")
    e, w = common.validate_common(is_lepton=is_lepton, is_neutrino=is_neutrino,
                                  tune=tune, genlist=genlist, n_jobs=args.n_jobs)
    errors += e; warnings += w
    for pdg in tgt_pdgs:
        errors += common.validate_target(pdg)

    input_xsec = None
    if args.input_cross_sections:
        input_xsec = str(Path(args.input_cross_sections).resolve())
        e, w = common.validate_cross_sections(input_xsec)
        errors += e; warnings += w
    if args.n_knots is not None and (args.n_knots < 30 or args.n_knots > 1000):
        warnings.append(f"n_knots={args.n_knots} is outside the recommended [30, 1000]")

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
    worker = _AGENT_ROOT / "adapters" / "genie" / "templates" / "gmkspl_grid.sh"
    if not worker.exists() or not os.access(worker, os.X_OK):
        sys.stderr.write(f"error: worker script missing/not executable: {worker}\n"); return 2

    user = os.environ.get("USER", "")
    if not user:
        sys.stderr.write("error: $USER not set; cannot build PNFS path\n"); return 2

    canon_probes = [canonical_probe(p) for p in nu_pdgs]
    canon_targets = [canonical_target(t) for t in tgt_pdgs]
    probe_label = "-".join(canon_probes)
    target_label = "-".join(canon_targets)
    now = datetime.now()
    stem = f"{probe_label}_{target_label}_{now.strftime('%Y%m%d-%H%M%S')}"
    pnfs_dir = pnfs.output_dir(scratch_base=cfg["pnfs_scratch_base"], user=user, project=project,
                               installation=installation, tune=tune, genlist=genlist, stem=stem,
                               kind=KIND, probe="-".join(str(p) for p in nu_pdgs),
                               target="-".join(str(t) for t in tgt_pdgs))

    role = args.role or cfg.get("default_role", "Analysis")
    disk = args.disk or cfg.get("default_disk", "20GB")
    req = args.append_condor_requirements or cfg.get("append_condor_requirements")

    cmd = [cfg["jobsub_bin"], "-G", cfg["default_group"], "--role", role, "--disk", disk,
           "-N", str(args.n_jobs)]
    if req:
        cmd += ["--append_condor_requirements", req]
    if input_xsec:
        cmd += ["-f", input_xsec if input_xsec.startswith("/pnfs/") else f"file://{input_xsec}"]
    if args.memory:
        cmd += ["--memory", args.memory]
    if args.expected_lifetime:
        cmd += ["--expected-lifetime", args.expected_lifetime]

    worker_args = [f"file://{worker}", "-p", ",".join(str(p) for p in nu_pdgs),
                   "-t", ",".join(str(t) for t in tgt_pdgs), "-T", tune, "-L", genlist,
                   "-j", stem, "-O", pnfs_dir]
    if args.max_energy is not None:
        worker_args += ["-e", str(args.max_energy)]
    if args.n_knots is not None:
        worker_args += ["-n", str(args.n_knots)]
    if input_xsec:
        worker_args += ["-S", Path(input_xsec).name]
    worker_args += ["-R", cvmfs_dir]
    if tune_cvmfs:
        worker_args += ["-X", tune_cvmfs]
    cmd += worker_args

    inputs = [{"probes": canon_probes, "probe_pdgs": nu_pdgs, "targets": canon_targets,
               "target_pdgs": tgt_pdgs, "tune": tune, "genlist": genlist,
               "n_knots": args.n_knots, "max_energy": args.max_energy,
               "input_cross_sections": input_xsec, "tarball_label": args.tarball_label,
               "tune_tarball_label": args.tune_tarball_label, "installation": installation}]
    outputs = {"pnfs_output_dir": pnfs_dir, "genie_command": " ".join(cmd), "warnings": warnings}
    extra = {"adapter": "genie", "kind": KIND, "output_suffix": ".xml",
             "channel": pnfs.channel_from_genlist(genlist), "probe": probe_label,
             "target": target_label, "tune": tune, "genlist": genlist, "installation": installation}

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
    print(f"outputs: {pnfs_dir}  (pull: scripts/job.py pull {record['jobid']} --suffix .xml)")
    if record.get("error"):
        sys.stderr.write(f"error:  {record['error']}\n")
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())

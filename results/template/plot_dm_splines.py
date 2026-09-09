#!/usr/bin/env python3
"""Plot GENIE boosted-dark-matter splines (gmkspl_dm output) per DM mass.

gspl2root cannot read DM splines (no AddDarkMatter), so the XML is parsed here.
Inputs are selected from the genie-agent runlogs (runtype gmkspl_dm, a label,
rc 0, spline_count > 0), one XML per (mass, generator list); every spline in a
list is summed on the union of its knots, so the plotted dots sit on real knots.
XML cross sections are in natural units (GeV^-2); they are shown in 1e-38 cm^2
(1 GeV^-2 = 3.89379e-28 cm^2 = 3.89379e10 x 1e-38 cm^2).

    pixi run python results/template/plot_dm_splines.py --label dm_scan_e1000 --out-dir DM_test
    pixi run python results/template/plot_dm_splines.py --label dm_scan_e1000 --out-dir DM_test --logx --logy
    pixi run python results/template/plot_dm_splines.py --label dm_scan_e1000 --out-dir DM_test --linear
    pixi run python results/template/plot_dm_splines.py --label dm_scan_e1000 --out-dir DM_test \
        --masses 200,300,400 --vlines 499        # subset of masses, DMRES cache edge marked

Default axes: linear x, log y (the look chosen for this scan on 2026-09-09; the cross
sections span 12 decades). --logx --logy gives log-log (stem suffix `_log`), --linear both
linear (suffix `_lin`, independent y ranges), --logx alone (suffix `_logx`).
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_style import (apply_style, new_panels, style_axis, FLOOR,   # noqa: E402
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

REPO = Path(__file__).resolve().parents[2]
GEV2_TO_1E38CM2 = 3.89379e10          # 1 GeV^-2 in units of 1e-38 cm^2
LISTS = ["DMEL", "DMDIS", "DME", "DMRES"]
_SPLINE_RE = re.compile(r'<spline name="([^"]*)" nknots="(\d+)">(.*?)</spline>', re.S)
_KNOT_RE = re.compile(r'<E>\s*([0-9.eE+-]+)\s*</E>\s*<xsec>\s*([0-9.eE+-]+)\s*</xsec>')


def parse_xml(path: str) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """[(name, E[GeV], xsec[1e-38 cm^2]), ...] for every spline in the file."""
    out = []
    for m in _SPLINE_RE.finditer(Path(path).read_text()):
        kn = _KNOT_RE.findall(m.group(3))
        e = np.array([float(a) for a, _ in kn]); x = np.array([float(b) for _, b in kn])
        out.append((m.group(1), e, x * GEV2_TO_1E38CM2))
    return out


def sum_on_union(splines):
    """Sum splines on the union of their knots (linear interpolation, 0 outside)."""
    if not splines:
        return np.array([]), np.array([])
    grid = np.unique(np.concatenate([e for _, e, _ in splines]))
    tot = np.zeros_like(grid)
    for _, e, x in splines:
        tot += np.interp(grid, e, x, left=0.0, right=0.0)
    return grid, tot


def collect(label: str, tune: str, target: str):
    """{mass: {genlist: (xml, jobid, spline_count)}} from the runlogs (newest wins)."""
    found: dict[float, dict[str, tuple]] = defaultdict(dict)
    for lg in glob.glob(str(REPO / "genie-agent/genie-runs" / f"{tune}-*" / "*.log")):
        try:
            r = json.loads(Path(lg).read_text())
        except Exception:
            continue
        ins = r.get("inputs", {}); outs = r.get("outputs", {})
        if (r.get("runtype") != "gmkspl_dm" or ins.get("label") != label
                or ins.get("tune_resolved") != tune or r.get("returncode") != 0
                or not (outs.get("spline_count") or 0)
                or ",".join(ins.get("canonical_targets", [])) != target):
            continue
        key = (ins["dm_mass"], ins["genlist_resolved"])
        prev = found[key[0]].get(key[1])
        if prev is None or (r.get("finished") or "") > prev[3]:
            found[key[0]][key[1]] = (outs["primary_output"], r["jobid"],
                                     outs["spline_count"], r.get("finished") or "")
    return dict(sorted(found.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default="dm_scan_e1000")
    ap.add_argument("--tune", default="GDM18_00a_00_000")
    ap.add_argument("--target", default="Ar40")
    ap.add_argument("--out-dir", default="DM_test")
    ap.add_argument("--stem", default=None, help="output stem (default dm_splines_<label>[_log])")
    ap.add_argument("--logx", action="store_true", help="log x axis (default linear)")
    ap.add_argument("--logy", action="store_true", help="log y axis (the default unless --linear)")
    ap.add_argument("--linear", action="store_true", help="both axes linear (stem suffix _lin)")
    ap.add_argument("--masses", default=None,
                    help="comma list of DM masses [GeV] to plot (default all found); adds _m<..> to the stem")
    ap.add_argument("--vlines", default=None,
                    help="comma list of energies [GeV] to mark with a dashed vertical line, "
                         "e.g. 499 = DMRES cache edge (ESplineMax-1)")
    args = ap.parse_args()
    if not (args.logx or args.logy or args.linear):
        args.logy = True                       # default: linear x, log y
    if args.linear:
        args.logx = args.logy = False
    suffix = ("_log" if (args.logx and args.logy) else "_logx" if args.logx
              else "" if args.logy else "_lin")
    apply_style()

    data = collect(args.label, args.tune, args.target)
    if not data:
        sys.stderr.write("no gmkspl_dm runs found for that label/tune/target\n"); return 2
    masses = list(data)
    if args.masses:
        want = [float(v) for v in args.masses.split(",")]
        masses = [m for m in masses if any(abs(m - w) < 1e-9 for w in want)]
        missing = [w for w in want if not any(abs(m - w) < 1e-9 for m in masses)]
        if missing:
            sys.stderr.write(f"warning: no runs for mass(es) {missing}\n")
        if not masses:
            sys.stderr.write("no requested mass found\n"); return 2
        suffix += "_m" + "-".join(f"{m:g}" for m in masses)
    vlines = [float(v) for v in args.vlines.split(",")] if args.vlines else []
    stem = args.stem or f"dm_splines_{args.label}{suffix}"
    out_dir = REPO / args.out_dir; out_dir.mkdir(parents=True, exist_ok=True)

    # per (mass, list): summed curve; per mass: total on the union grid
    curves: dict[float, dict[str, tuple]] = {}
    for m in masses:
        curves[m] = {}
        for gl in LISTS:
            if gl in data[m]:
                spl = parse_xml(data[m][gl][0])
                curves[m][gl] = sum_on_union(spl)
        parts = [(gl, e, x) for gl, (e, x) in curves[m].items() if len(e)]
        curves[m]["Total"] = sum_on_union(parts)

    series = LISTS + ["Total"]
    colors = {s: f"C{i}" for i, s in enumerate(series)}

    # ---- Figure 1: one panel per mass -------------------------------------
    ncols = min(5, len(masses)); nrows = int(np.ceil(len(masses) / ncols))
    fig, axes = new_panels(ncols=ncols, nrows=nrows, sharey=args.logy)
    for ax, m in zip(axes, masses):
        for s in series:
            if s not in curves[m] or not len(curves[m][s][0]):
                continue
            e, x = curves[m][s]
            ax.plot(e, np.maximum(x, FLOOR) if args.logy else x, "-o", ms=2, color=colors[s],
                    label=s + (" (all 0)" if x.max() <= 0 else ""))
        missing = [gl for gl in LISTS if gl not in curves[m]]
        title = f"m = {m:g} GeV" + (f"  [{','.join(missing)} pending]" if missing else "")
        style_axis(ax, title=title, xlabel="E [GeV]", logx=args.logx, logy=args.logy)
        ax.set_xlim(0.3 if args.logx else 0.0, 1.2e3 if args.logx else 1050.0)
        for v in vlines:
            ax.axvline(v, color="0.4", ls="--", lw=1)
            ax.text(v, 0.98, f" {v:g} GeV", transform=ax.get_xaxis_transform(),
                    ha="left", va="top", fontsize=FS_LEGEND, color="0.3")
    for ax in axes[len(masses):]:
        ax.set_visible(False)
    for r in range(nrows):
        axes[r * ncols].set_ylabel(r"$\sigma$(DM Ar40)  [$10^{-38}$ cm$^2$]", fontsize=FS_LABEL)
    axes[0].legend(title="process", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE,
                   loc="lower right" if args.logy else "upper left")
    floor_note = f"; y floor {FLOOR:g} for zeros" if args.logy else "; independent y ranges"
    sep = "\n" if ncols < 5 else " "      # narrow canvas: wrap the title
    fig.suptitle(f"GENIE rc-v380 {args.tune}: DM-{args.target} splines per DM mass{sep}"
                 f"(z = 0.5, g = 1.0, 100 knots, E$_{{max}}$ = 1000 GeV{floor_note})",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    p1 = out_dir / f"{stem}_per_mass.png"; fig.savefig(p1, dpi=DPI); plt.close(fig)

    # ---- Figure 2: one panel per process, one line per mass ---------------
    fig, axes = new_panels(ncols=len(series), nrows=1, sharey=args.logy)
    for ax, s in zip(axes, series):
        for i, m in enumerate(masses):
            if s not in curves[m] or not len(curves[m][s][0]):
                continue
            e, x = curves[m][s]
            ax.plot(e, np.maximum(x, FLOOR) if args.logy else x, "-o", ms=2, color=f"C{i % 10}", label=f"{m:g}")
        style_axis(ax, title=s, xlabel="E [GeV]", logx=args.logx, logy=args.logy)
        ax.set_xlim(0.3 if args.logx else 0.0, 1.2e3 if args.logx else 1050.0)
        for v in vlines:
            ax.axvline(v, color="0.4", ls="--", lw=1)
    axes[0].set_ylabel(r"$\sigma$(DM Ar40)  [$10^{-38}$ cm$^2$]", fontsize=FS_LABEL)
    axes[0].legend(title="m$_{DM}$ [GeV]", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE,
                   loc="lower right" if args.logy else "upper right", ncol=2)
    fig.suptitle(f"GENIE rc-v380 {args.tune}: DM-{args.target} cross section per process vs DM mass "
                 f"(z = 0.5, g = 1.0{floor_note})", fontsize=FS_SUPTITLE)
    fig.tight_layout()
    p2 = out_dir / f"{stem}_per_process.png"; fig.savefig(p2, dpi=DPI); plt.close(fig)

    # ---- text readout ------------------------------------------------------
    E_PROBE = [10.0, 100.0, 1000.0]
    lines = [f"# DM splines, label={args.label}, tune={args.tune}, target={args.target}",
             f"# sigma in 1e-38 cm^2 (XML GeV^-2 x {GEV2_TO_1E38CM2:.5g}); linear interpolation between knots; 0 = below threshold or empty",
             f"# figures: {p1.name}, {p2.name}",
             "mass_GeV\tprocess\tjobid\tn_splines\tE_first_nonzero_GeV\tsigma_max\tE_at_max\t"
             + "\t".join(f"sigma@{e:g}GeV" for e in E_PROBE)]
    for m in masses:
        for s in series:
            if s not in curves[m] or not len(curves[m][s][0]):
                lines.append(f"{m:g}\t{s}\tPENDING\t-\t-\t-\t-\t" + "\t".join("-" for _ in E_PROBE)); continue
            e, x = curves[m][s]
            nz = np.nonzero(x > 0)[0]
            first = f"{e[nz[0]]:.4g}" if len(nz) else "-"
            imax = int(np.argmax(x))
            jid = data[m][s][1] if s in data[m] else "(sum)"
            nspl = data[m][s][2] if s in data[m] else sum(data[m][g][2] for g in LISTS if g in data[m])
            probes = [f"{np.interp(ep, e, x, left=0.0, right=0.0):.4g}" for ep in E_PROBE]
            lines.append(f"{m:g}\t{s}\t{jid}\t{nspl}\t{first}\t{x[imax]:.4g}\t{e[imax]:.4g}\t" + "\t".join(probes))
    pt = out_dir / f"{stem}.txt"; pt.write_text("\n".join(lines) + "\n")
    print(f"wrote {p1}\n      {p2}\n      {pt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""v0.2 section 5: post-FSI proton choice — leading vs primary-vertex descendant.

For the section-4 post-FSI in-window events (qel && hit p && Q^2 window,
leading-proton reconstruction inside E_m+T_rec in [0,80) MeV && p_m < 300
MeV/c), compare the two candidate post-FSI protons event by event:

  LEADING : highest-|p| final-state proton, any ancestry (the
            spectrometer-like choice used everywhere else in the series)
  VERTEX  : the leading final-state proton DESCENDED from the primary QEL
            proton (GHEP daughter tracing; absent when the primary proton is
            absorbed or charge-exchanges while another proton still leads)

Two panels per tune: the restored axis E_m + T_rec = omega - T_p, and T_p
itself, both reconstructions on the SAME event set (raw events/bin, so the
curves are directly comparable; the VERTEX curve simply lacks the
no-descendant events). Input: the dump_fsiproton.cxx CSVs
(cache/fsiproton_<target>/<tune>.csv; q2/omega/q-vector + both protons'
4-momenta + same-particle flag).

Outputs: results/prd-analyzer-v0.2/fsi_proton_choice_<target>_<tune>.png

Usage:
  pixi run python results/template/make_fsi_proton_choice.py --target Fe56 --all-tunes
  pixi run python results/template/make_fsi_proton_choice.py --target C12 --all-tunes
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"

_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

EDGES_E = np.arange(0.0, 82.0, 2.0)      # restored axis [MeV], 2 MeV bins
PM_MAX = 300.0                           # MeV/c, section-4 window
EM_LO, EM_HI = 0.0, 80.0

TUNE_GS = {
    "GEM26_11a_05_000": "LocalFGM",
    "GEM26_22a_05_000": "SF",
    "GEM26_22b_05_000": "SF",
    "GEM21_11a_05_000": "LocalFGM",
}


def load(target, tune):
    d = np.genfromtxt(CACHE_ROOT / f"fsiproton_{target.lower()}" / f"{tune}.csv",
                      delimiter=",", names=True)
    out = {}
    for tag in ("l", "v"):
        E, px, py, pz = (d[f"{tag}e"], d[f"{tag}px"], d[f"{tag}py"], d[f"{tag}pz"])
        has = E > 0
        Tp = np.where(has, E - M_P, np.nan)
        pm = np.where(has, np.sqrt((px - d["qx"])**2 + (py - d["qy"])**2
                                   + (pz - d["qz"])**2), np.nan)
        out[tag] = dict(Tp=Tp, pm=pm * 1000.0,
                        Er=(d["omega"] - Tp) * 1000.0, has=has)
    out["same"] = d["same"].astype(bool)
    return out


def make_figure(target, tune):
    ev = load(target, tune)
    # section-4 post-FSI in-window set, defined with the LEADING proton
    l = ev["l"]
    win = (l["has"] & (l["pm"] < PM_MAX)
           & (l["Er"] >= EM_LO) & (l["Er"] < EM_HI))
    n = int(win.sum())
    v = ev["v"]
    vhas = win & v["has"]
    same = win & ev["same"]
    n_v, n_same = int(vhas.sum()), int(same.sum())
    diff = win & v["has"] & ~ev["same"]
    print(f"[{tune}] in-window N={n:,}  vertex-descendant exists {n_v:,} "
          f"({100*n_v/n:.1f}%)  same particle {n_same:,} ({100*n_same/n:.1f}%)  "
          f"secondary leads {int(diff.sum()):,} ({100*diff.sum()/n:.1f}%)")

    fig, axes = new_panels(ncols=2, sharey=False)

    ax = axes[0]
    hl, _ = np.histogram(l["Er"][win], bins=EDGES_E)
    hv, _ = np.histogram(v["Er"][vhas], bins=EDGES_E)
    ax.stairs(hl, EDGES_E, color="C3", linewidth=2.0, zorder=5,
              label=f"leading p (N={n:,})")
    ax.stairs(hv, EDGES_E, color="C0", linewidth=1.6, linestyle="--", zorder=6,
              label=f"primary-vertex p (N={n_v:,})")
    style_axis(ax, title=r"restored axis  $\omega-T_p$",
               xlabel=r"$E_m+T_{rec}$  (MeV)", logx=False, logy=True, ymin=None)
    ax.set_xlim(0, 82)
    ax.set_ylabel("events / 2 MeV", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title=f"same particle: {100*n_same/n:.1f}%",
              title_fontsize=FS_LEGEND_TITLE - 3)

    ax = axes[1]
    tp_all = np.concatenate([l["Tp"][win], v["Tp"][vhas]])
    lo, hi = np.percentile(tp_all, [0.2, 99.8])
    bins = np.linspace(np.floor(lo * 10) / 10, np.ceil(hi * 10) / 10, 55)
    ax.hist(l["Tp"][win], bins=bins, histtype="step", linewidth=2.0,
            color="C3", label="leading p", zorder=5)
    ax.hist(v["Tp"][vhas], bins=bins, histtype="step", linewidth=1.6,
            ls="--", color="C0", label="primary-vertex p", zorder=6)
    style_axis(ax, title="proton kinetic energy",
               xlabel=r"$T_p$  (GeV)", logx=False, logy=True, ymin=None)
    ax.set_ylabel("events / bin", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper left")

    fig.suptitle(f"{target} post-FSI proton choice — {tune}  "
                 f"({TUNE_GS[tune]})\n"
                 "section-4 in-window events (qel && hit p && $Q^2$ slice)",
                 fontsize=FS_SUPTITLE - 3)
    fig.tight_layout()
    out = OUT_DIR / f"fsi_proton_choice_{target.lower()}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("  wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=["Fe56", "C12"])
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_GS))
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()

    apply_style()
    for t in (sorted(TUNE_GS) if args.all_tunes else [args.tune]):
        make_figure(args.target, t)

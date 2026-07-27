"""v0.2 section 5: post-FSI leading proton vs the pre-FSI primary proton.

For the section-4 post-FSI in-window events (qel && hit p && Q^2 window,
leading-proton reconstruction inside E_m+T_rec in [0,80) MeV && p_m < 300
MeV/c), compare event-by-event:

  PRE-FSI PRIMARY : the primary QEL proton at the vertex (GHEP status-14
                    hadron-in-the-nucleus), BEFORE INTRANUKE
  POST-FSI LEADING: the highest-|p| final-state proton (the spectrometer-like
                    choice used everywhere in the series)

Two panels per tune, both reconstructions on the SAME event set (raw
events/bin, log-y): the restored axis omega - T_p, and T_p itself. This is
the per-event face of the section-4 stage-3 -> stage-4 transition: the
constant hA2018 Delta T_p shift appears as the displaced delta, and the
rescattered remainder as the low-T_p / high-E_m tail.

The dump (dump_fsiproton.cxx CSVs, cache/fsiproton_<target>/<tune>.csv) also
carries the leading proton AMONG the primary's descendants ("vertex", the
provenance check): in hA2018 leading == vertex in 100% of proton-surviving
events, so the pre/post comparison here is genuinely primary-vs-its-own-fate.

Outputs: results/prd-analyzer-v0.2/fsi_prepost_<target>_<tune>.png

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

PROTON_SEL = "leading"          # or "1p": exactly one FS proton (v0.3)
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
    for tag in ("l", "v", "p"):
        E, px, py, pz = (d[f"{tag}e"], d[f"{tag}px"], d[f"{tag}py"], d[f"{tag}pz"])
        has = E > 0
        Tp = np.where(has, E - M_P, np.nan)
        pm = np.where(has, np.sqrt((px - d["qx"])**2 + (py - d["qy"])**2
                                   + (pz - d["qz"])**2), np.nan)
        out[tag] = dict(Tp=Tp, pm=pm * 1000.0,
                        Er=(d["omega"] - Tp) * 1000.0, has=has)
    out["same"] = d["same"].astype(bool)
    out["np"] = d["np"].astype(int)
    return out


def make_figure(target, tune):
    ev = load(target, tune)
    # section-4 post-FSI in-window set, defined with the LEADING proton
    l, p = ev["l"], ev["p"]
    psel = (ev["np"] == 1) if PROTON_SEL == "1p" else l["has"]
    win = (psel & (l["pm"] < PM_MAX)
           & (l["Er"] >= EM_LO) & (l["Er"] < EM_HI))
    if PROTON_SEL == "1p":
        npc = ev["np"]
        print(f"[{tune}] window multiplicity: 0p={np.mean(npc==0):.3f} "
              f"1p={np.mean(npc==1):.3f} 2p+={np.mean(npc>=2):.3f}")
    n = int(win.sum())
    n_same = int((win & ev["same"]).sum())
    dT = (p["Tp"][win] - l["Tp"][win]) * 1000.0        # pre - post [MeV]
    dT = dT[np.isfinite(dT)]
    hshift, eshift = np.histogram(dT, bins=np.arange(-2.0, 80.0, 1.0))
    mode = eshift[np.argmax(hshift)] + 0.5
    frac_line = float(np.mean(np.abs(dT - mode) <= 1.0))
    print(f"[{tune}] in-window N={n:,} (leading==vertex descendant "
          f"{100*n_same/n:.1f}%)  dT_p = T_p(pre)-T_p(post): "
          f"mode {mode:.1f} MeV, frac within +-1 MeV {frac_line:.3f}, "
          f"median {np.median(dT):.2f} MeV")

    fig, axes = new_panels(ncols=2, sharey=False)

    ax = axes[0]
    hl, _ = np.histogram(l["Er"][win], bins=EDGES_E)
    hp, _ = np.histogram(p["Er"][win & p["has"]], bins=EDGES_E)
    ax.stairs(hp, EDGES_E, color="C0", linewidth=1.6, linestyle="--", zorder=6,
              label="pre-FSI primary p")
    ax.stairs(hl, EDGES_E, color="C3", linewidth=2.0, zorder=5,
              label="post-FSI leading p")
    style_axis(ax, title=r"restored axis  $\omega-T_p$",
               xlabel=r"$E_m+T_{rec}$  (MeV)", logx=False, logy=True, ymin=None)
    ax.set_xlim(0, 82)
    ax.set_ylabel("events / 2 MeV", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title=f"N = {n:,} (post-FSI in-window)",
              title_fontsize=FS_LEGEND_TITLE - 3)

    ax = axes[1]
    tp_all = np.concatenate([l["Tp"][win], p["Tp"][win & p["has"]]])
    tp_all = tp_all[np.isfinite(tp_all)]
    lo, hi = np.percentile(tp_all, [0.2, 99.8])
    bins = np.linspace(np.floor(lo * 10) / 10, np.ceil(hi * 10) / 10, 55)
    ax.hist(p["Tp"][win & p["has"]], bins=bins, histtype="step", linewidth=1.6,
            ls="--", color="C0", label="pre-FSI primary p", zorder=6)
    ax.hist(l["Tp"][win], bins=bins, histtype="step", linewidth=2.0,
            color="C3", label="post-FSI leading p", zorder=5)
    style_axis(ax, title="proton kinetic energy",
               xlabel=r"$T_p$  (GeV)", logx=False, logy=True, ymin=None)
    ax.set_ylabel("events / bin", fontsize=FS_LABEL)
    if frac_line >= 0.5:
        dt_note = (f"$\\Delta T_p$ line: {mode:.0f} MeV "
                   f"({100*frac_line:.0f}% of events)")
    else:
        dt_note = f"$\\Delta T_p$ broad, median {np.median(dT):.0f} MeV"
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper left",
              title=dt_note, title_fontsize=FS_LEGEND_TITLE - 3)

    fig.suptitle(f"{target} pre- vs post-FSI proton — {tune}  "
                 f"({TUNE_GS[tune]})\n"
                 "section-4 in-window events (qel && hit p && $Q^2$ slice"
                 + (" && N$_p$=1)" if PROTON_SEL == "1p" else ")"),
                 fontsize=FS_SUPTITLE - 3)
    fig.tight_layout()
    out = OUT_DIR / f"fsi_prepost_{target.lower()}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("  wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=["Fe56", "C12"])
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_GS))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--proton-sel", default="leading", choices=["leading", "1p"],
                    help="1p: exactly one FS proton, outputs to v0.3")
    args = ap.parse_args()
    PROTON_SEL = args.proton_sel
    if PROTON_SEL == "1p":
        OUT_DIR = REPO / "results/prd-analyzer-v0.3"
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    for t in (sorted(TUNE_GS) if args.all_tunes else [args.tune]):
        make_figure(args.target, t)

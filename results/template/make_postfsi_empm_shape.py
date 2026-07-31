"""Post-FSI E_m and |p_m| SHAPES, normalized to the surviving events.

The shape companion to the two ladders (make_emiss_ladder_q2cut.py section
4, make_pmiss_ladder_q2cut.py section 4.1): one figure per target/tune with
the post-FSI proton's restored E_m (left) and |p_m| (right) distributions
normalized by the SURVIVING in-window post-FSI count -- not by the true-QEL
selection count N_sel -- so every curve has unit integral over its window
and the ~Z x survival occupancy scale is divided out. What remains is the
pure FSI shape distortion against the data and the input-table shapes:

    left  (E_m + T_rec, [0, 80) MeV, p_m < 300):  vs fig 9 / fig 11
    right (|p_m| < 320 MeV/c, E window as 4.1):   vs folded fig 6 p+s / fig 7

Each panel: post-FSI (solid) and pre-FSI (dashed) shapes -- each stage
normalized by its OWN in-window count -- the unit-normalized windowed input
table (SF tunes), and the unit-normalized data. The E windows per panel
mirror their sections: E panel [0, 80) for both targets; p panel Fe56
E_m < 80, C12 the fig 6 shell windows 10-25 (+) 30-50 MeV.

Reads the ladder caches built by make_emiss_ladder_q2cut.py (run it first;
--proton-sel 1p reads the v0.3 caches, stage 4 = the unique N_p = 1 proton).
Figures: results/prd-analyzer-v0.<2|3>/postfsi_shape_empm_<target>_<tune>.png.

Usage:
  pixi run python results/template/make_postfsi_empm_shape.py --target Fe56 --all-tunes --proton-sel 1p
  pixi run python results/template/make_postfsi_empm_shape.py --target C12  --all-tunes --proton-sel 1p
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_pmiss_ladder_q2cut import (TGT, TUNE_GS, load_table, n_windowed,
                                     in_windows)                # noqa: E402
from make_emiss_ladder_q2cut import rebin, f_restricted         # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"

PROTON_SEL = "leading"
E_EDGES = np.arange(0.0, 85.0, 5.0)     # E panel: [0, 80), 5-MeV bins
E_BINW = 5.0
PM_MAX_E = 300.0                        # E panel p_m window (section 4)
P_EDGES = np.arange(0.0, 321.0, 20.0)   # p panel: [0, 320), native 20 MeV/c
P_BINW = 20.0
P_DATA_BINW = 40.0


def _em_data_fe56():
    dem, dsf, _, dstat = np.loadtxt(DATA_DIR / "fig11_q1p2.dat", unpack=True)
    return dem, dsf, dstat, "Dutta Fig. 11 (unit-norm.)"


def _em_data_c12():
    from fig9_common import load_dutta
    dem, dsf, dstat, _ = load_dutta()
    return dem, dsf, dstat, "Dutta Fig. 9 (unit-norm.)"

EM_DATA = {"Fe56": _em_data_fe56, "C12": _em_data_c12}


def unit_hist(vals, edges, binw):
    """Histogram normalized by its own in-range count: unit integral."""
    v = vals[np.isfinite(vals)]
    v = v[(v >= edges[0]) & (v < edges[-1])]
    cnt, _ = np.histogram(v, bins=edges)
    n = int(cnt.sum())
    return cnt / max(n, 1) / binw, n


def make_figure(target, tune):
    cfg = TGT[target]
    from make_pmiss_ladder_q2cut import _m_rec_c12
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else _m_rec_c12()
    tlow = target.lower()
    cache = CACHE_ROOT / f"ladder_{tlow}" / f"{tune}.npz"
    if not cache.exists():
        raise SystemExit(f"missing cache {cache} — build it first with "
                         "make_emiss_ladder_q2cut.py"
                         + (" --proton-sel 1p" if PROTON_SEL == "1p" else ""))
    c = dict(np.load(cache))
    with np.errstate(invalid="ignore"):
        for s in (3, 4):
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)

    # --- E panel inputs (section-4 construction: p_m < 300, E in [0, 80)) ---
    yE, nE = {}, {}
    for s in (3, 4):
        sel = np.isfinite(c[f"E{s}r"]) & (c[f"p{s}"] < PM_MAX_E)
        yE[s], nE[s] = unit_hist(c[f"E{s}r"][sel], E_EDGES, E_BINW)
    dem, dsf, dstat, em_label = EM_DATA[target]()
    dnormE = 1.0 / (dsf.sum() * E_BINW)

    # --- p panel inputs (section-4.1 construction: E window, p < 320) ---
    yP, nP = {}, {}
    for s in (3, 4):
        win = in_windows(c[f"E{s}r"], cfg["e_windows"])
        yP[s], nP[s] = unit_hist(np.where(win, c[f"p{s}"], np.nan),
                                 P_EDGES, P_BINW)
    dx, dy, de = cfg["dutta"]()               # folded, [MeV^-3]
    wp = 4.0 * np.pi * dx ** 2
    dnormP = 1.0 / ((wp * dy).sum() * P_DATA_BINW)

    # --- unit-normalized table shapes (SF tunes) ---
    has_table = TUNE_GS[tune][0]
    yE_in = yP_in = kP_edges = None
    if has_table:
        stem, table = load_table(target)
        k, E, k_edges, P, dk, dE = table
        fE = rebin(E, f_restricted(k, P, dk, 1.0, kmax=PM_MAX_E), dE, E_EDGES)
        yE_in = fE / (fE.sum() * E_BINW)
        nwin, kP_edges = n_windowed(table, 1.0, cfg["e_windows"])
        sel = kP_edges[1:] <= P_EDGES[-1] + 1e-9
        yP_in = nwin / (nwin[sel].sum() * dk)

    print(f"[{tune}] survivors: E panel pre={nE[3]:,} post={nE[4]:,}  "
          f"p panel pre={nP[3]:,} post={nP[4]:,}")

    fig, (axE, axP) = new_panels(ncols=2, nrows=1, sharey=False)

    # left: E_m
    if yE_in is not None:
        axE.stairs(yE_in, E_EDGES, color="C1", linewidth=1.2, linestyle="-",
                   alpha=0.9, zorder=3, label="input table (unit-norm.)")
    axE.stairs(yE[3], E_EDGES, color="C0", linewidth=1.6, linestyle="--",
               zorder=4, label=f"pre-FSI shape (N={nE[3]:,})")
    axE.stairs(yE[4], E_EDGES, color="C3", linewidth=2.0, zorder=5,
               label=f"post-FSI shape (N={nE[4]:,})")
    axE.errorbar(dem, dsf * dnormE, yerr=dstat * dnormE, fmt="s", ms=4,
                 color="black", capsize=2, zorder=9, label=em_label)
    style_axis(axE, title=r"post-FSI $E_m$ shape  ($p_m<300$)",
               xlabel=r"$E_m+T_{rec}$  (MeV)", logx=False, logy=False,
               ymin=None)
    axE.set_xlim(0, 80)
    axE.set_ylim(0, 1.25 * max([yE[4].max(), (dsf * dnormE).max()]
                               + ([yE_in.max()] if yE_in is not None else [])))
    axE.set_ylabel(r"d$N/$d$(E_m+T_{rec})\,/\,N_{\rm surv}$   (MeV$^{-1}$)",
                   fontsize=FS_LABEL)
    axE.legend(fontsize=FS_LEGEND - 3, loc="upper right",
               title="each curve: unit integral over [0, 80)\n"
                     "(pre-FSI spikes may run off scale)",
               title_fontsize=FS_LEGEND_TITLE - 3)

    # right: |p_m|
    if yP_in is not None:
        axP.stairs(yP_in, kP_edges, color="C1", linewidth=1.2, linestyle="-",
                   alpha=0.9, zorder=3, label="input table (unit-norm.)")
    axP.stairs(yP[3], P_EDGES, color="C0", linewidth=1.6, linestyle="--",
               zorder=4, label=f"pre-FSI shape (N={nP[3]:,})")
    axP.stairs(yP[4], P_EDGES, color="C3", linewidth=2.0, zorder=5,
               label=f"post-FSI shape (N={nP[4]:,})")
    axP.errorbar(dx, wp * dy * dnormP, yerr=wp * de * dnormP, fmt="s", ms=4,
                 color="black", capsize=2, zorder=9,
                 label=cfg["data_label"].replace("publ. scale", "unit-norm."))
    style_axis(axP, title=r"post-FSI $|p_m|$ shape",
               xlabel=r"$|p_m|$  [MeV/c]", logx=False, logy=False, ymin=None)
    axP.set_xlim(0, 320)
    axP.set_ylim(0, 1.25 * max([yP[4].max(), (wp * dy * dnormP).max()]
                               + ([yP_in.max()] if yP_in is not None else [])))
    axP.set_ylabel(r"d$N/$d$|p_m|\,/\,N_{\rm surv}$   [(MeV/c)$^{-1}$]",
                   fontsize=FS_LABEL)
    axP.legend(fontsize=FS_LEGEND - 3, loc="upper right",
               title=cfg["win_label"] + ";\nunit integral over [0, 320)",
               title_fontsize=FS_LEGEND_TITLE - 3)

    fig.suptitle(f"{target} post-FSI shapes — {tune}  ({TUNE_GS[tune][1]})\n"
                 "qel && hit p && $Q^2=1.28\\pm5\\%$"
                 + (" && N$_p$=1" if PROTON_SEL == "1p" else "")
                 + "; normalized to the surviving events",
                 fontsize=FS_SUPTITLE - 3)
    fig.tight_layout()
    out = OUT_DIR / f"postfsi_shape_empm_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TGT))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_GS))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--proton-sel", default="leading", choices=["leading", "1p"],
                    help="1p: stage 4 = exactly one FS proton, reads/writes v0.3")
    args = ap.parse_args()
    PROTON_SEL = args.proton_sel
    if PROTON_SEL == "1p":
        CACHE_ROOT = REPO / "results/prd-analyzer-v0.3/cache"
        OUT_DIR = REPO / "results/prd-analyzer-v0.3"

    apply_style()
    for tune in (sorted(TUNE_GS) if args.all_tunes else [args.tune]):
        make_figure(args.target, tune)

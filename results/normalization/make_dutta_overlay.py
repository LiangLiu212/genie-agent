"""GENIE input tables overlaid on the Dutta E91-013 measurements, projected
through the SAME phase space and binning as each published figure.

Projections (exact partial-bin clipping via the parse_table grids):
  E_m spectra (figs 9/11):  f(E) = int_{k<300} 4pi k^2 P dk, bin-averaged
    into the data's 5-MeV bins over 0-80 MeV  [MeV^-1]
  p_m windows (figs 6/7):   n(p) = int_{E window} P(k,E) dE, bin-averaged
    into the data's 40-MeV/c bins and mirrored to signed p_m  [MeV^-3]
    (windows: fig6 top 10-25 MeV, fig6 bot 30-50 MeV, fig7 0-80 MeV)

Scales are NOT adjusted: tables stay on their native N*P (occupancy) scale,
the data on their published (FSI-distorted, renormalized) scales; each panel
annotates the data/table strength ratio over the plotted window (4pi p^2
weighted for the p_m panels). fig6/7 overlays use the Q^2 = 1.28 files (the
repo's replication kinematics). Data errors: figs 6/7 stat-only (col 4);
figs 9/11 stat + 2% + 5% in quadrature, with the fig9 published-bar
overrides at E_m = 17.5 / 22.5 MeV (report/dutta-e91013-figures.md sec 5).

With --native the tables are drawn on their NATIVE grids instead (0.025-MeV
E bins for pke12_2024, the offset 5-MeV grid for pke56, 20-MeV/c k bins for
the p_m panels); only the data keep the published binning. The annotated
data/table ratios are computed on the native grids (exact windowed sums) in
both modes, so the two figures carry identical numbers.

Usage:
  pixi run python results/normalization/make_dutta_overlay.py            # data binning
  pixi run python results/normalization/make_dutta_overlay.py --native   # native bins
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))
sys.path.insert(0, str(HERE))

import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LEGEND, FS_TICK, FS_SUPTITLE, DPI)  # noqa: E402
from integrate_all_pke import default_data_dir, parse_table    # noqa: E402

DUTTA = HERE.parents[1] / "data" / "Dipingkar-dutta-data-prc_figs"
K_MAX = 300.0                          # the paper's |p_m| window [MeV/c]
E_BINS = np.arange(0.0, 85.0, 5.0)     # data E_m binning [MeV]
P_BINS = np.arange(0.0, 360.0, 40.0)   # data |p_m| binning [MeV/c]


def clip_widths(edges, lo, hi):
    return np.clip(np.minimum(edges[1:], hi)
                   - np.maximum(edges[:-1], lo), 0.0, None)


def em_profile(res, bins, k_hi=K_MAX):
    """Bin-averaged f(E) = int_{k<k_hi} 4pi k^2 P dk on the data grid [MeV^-1]."""
    k, P, k_edges, E_edges, _, _, _ = res
    dk_eff = clip_widths(k_edges, 0.0, k_hi)
    fE = (4.0 * np.pi * k[:, None] ** 2 * P * dk_eff[:, None]).sum(axis=0)
    return np.array([(fE * clip_widths(E_edges, lo, hi)).sum() / (hi - lo)
                     for lo, hi in zip(bins[:-1], bins[1:])])


def pm_profile(res, E_win, bins=P_BINS):
    """Bin-averaged n(p) = int_{E window} P dE on the data grid [MeV^-3]."""
    _, P, k_edges, E_edges, _, _, _ = res
    dE_eff = clip_widths(E_edges, *E_win)
    nk = (P * dE_eff[None, :]).sum(axis=1)
    return np.array([(nk * clip_widths(k_edges, lo, hi)).sum() / (hi - lo)
                     for lo, hi in zip(bins[:-1], bins[1:])])


def em_native(res, k_hi=K_MAX):
    """f(E) on the table's native E grid [MeV^-1], k < k_hi."""
    k, P, k_edges, E_edges, _, _, _ = res
    dk_eff = clip_widths(k_edges, 0.0, k_hi)
    fE = (4.0 * np.pi * k[:, None] ** 2 * P * dk_eff[:, None]).sum(axis=0)
    return fE, E_edges


def pm_native(res, E_win, k_hi=P_BINS[-1]):
    """n(p) on the table's native k grid [MeV^-3], up to the plotted k_hi."""
    _, P, k_edges, E_edges, _, _, _ = res
    dE_eff = clip_widths(E_edges, *E_win)
    nk = (P * dE_eff[None, :]).sum(axis=1)
    n = int((clip_widths(k_edges, 0.0, k_hi) > 0).sum())
    return nk[:n], k_edges[:n + 1]


def em_strength(res, E_win=(0.0, 80.0), k_hi=K_MAX):
    """Exact windowed strength on the native grid (binning-independent)."""
    k, P, k_edges, E_edges, _, _, _ = res
    dk_eff = clip_widths(k_edges, 0.0, k_hi)
    dE_eff = clip_widths(E_edges, *E_win)
    return float((4.0 * np.pi * k[:, None] ** 2 * P
                  * dk_eff[:, None] * dE_eff[None, :]).sum())


def pm_strength(res, E_win, k_hi=P_BINS[-1]):
    """4pi p^2-weighted strength over the plotted |p_m| range, native grid."""
    k, P, k_edges, E_edges, _, _, _ = res
    dk_eff = clip_widths(k_edges, 0.0, k_hi)
    dE_eff = clip_widths(E_edges, *E_win)
    nk = (P * dE_eff[None, :]).sum(axis=1)
    return float((4.0 * np.pi * k ** 2 * nk * dk_eff).sum())


def mirror(vals, bins):
    """Signed-p_m step curve from |p_m| bin values (data are symmetrized)."""
    edges = np.concatenate([-bins[::-1], bins[1:]])
    return np.concatenate([vals[::-1], vals]), edges


def load_dutta(stem):
    x, y, _, e = np.loadtxt(DUTTA / f"{stem}.dat", unpack=True)
    return x, y, e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--native", action="store_true",
                    help="draw tables on their native grids (no rebinning)")
    args = ap.parse_args()
    data_dir = default_data_dir()
    tables = {name: parse_table(data_dir / name) for name in
              ["pke12_tot.data", "pke12_2024.table", "pke56_tot.data"]}
    C12 = [("pke12_tot", tables["pke12_tot.data"], "C0"),
           ("pke12_2024", tables["pke12_2024.table"], "C1")]
    FE = [("pke56_tot", tables["pke56_tot.data"], "C2")]

    apply_style()
    fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
    ax_em_c, ax_psh, ax_ssh, ax_em_fe, ax_pm_fe, ax_off = axes
    ax_off.set_visible(False)

    p_ctr = 0.5 * (P_BINS[:-1] + P_BINS[1:])
    e_ctr = 0.5 * (E_BINS[:-1] + E_BINS[1:])

    # ---- E_m spectra vs figs 9 / 11 ------------------------------------------
    for ax, stem, tabs, bars, ymax in [
        (ax_em_c, "fig9_q1p2", C12, {17.5: 0.081, 22.5: 0.047}, 0.7),
        (ax_em_fe, "fig11_q1p2", FE, {}, None),
    ]:
        x, y, e = load_dutta(stem)
        tot = np.sqrt(e ** 2 + (0.02 * y) ** 2 + (0.05 * y) ** 2)
        for em, frac in bars.items():
            tot[np.isclose(x, em)] = frac * y[np.isclose(x, em)]
        ratios = []
        for name, res, color in tabs:
            if args.native:
                fE, edges = em_native(res)
                ax.stairs(fE, edges, color=color, lw=1.5, zorder=4, label=name)
            else:
                v = em_profile(res, E_BINS)
                ax.stairs(v, E_BINS, color=color, lw=2.0, zorder=4, label=name)
            ratios.append(f"{(y.sum() * 5.0) / em_strength(res):.2f}")
        if stem == "fig9_q1p2" and not args.native:
            # resolved 2024 structure hidden by the data binning
            fE, edges = em_native(tables["pke12_2024.table"])
            E_c = 0.5 * (edges[:-1] + edges[1:])
            m = E_c <= 85.0
            ax.plot(E_c[m], fE[m], color="C1", lw=1.0, alpha=0.5, zorder=3)
        ax.errorbar(x, y, yerr=tot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(x, y, yerr=e, fmt="s", ms=5, color="black", capsize=2,
                    zorder=9, label="Dutta data")
        ax.text(0.03, 0.97, f"data/table = {', '.join(ratios)}",
                transform=ax.transAxes, va="top", fontsize=FS_TICK)
        fignum = stem.split("_")[0].replace("fig", "")
        style_axis(ax, title=f"{'C12' if tabs is C12 else 'Fe56'} $E_m$ "
                             f"spectrum vs fig {fignum}",
                   xlabel=r"$E_m$  [MeV]",
                   ylabel=r"$\int_{k<300} 4\pi k^2 P\,dk$   [MeV$^{-1}$]",
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 85)
        ax.set_ylim(0, ymax)   # fig9: clips the resolved 2024 spikes (v0 style)
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False)

    # ---- p_m windows vs figs 6 / 7 -------------------------------------------
    for ax, stem, tabs, E_win, title in [
        (ax_psh, "fig6_top_q1p2", C12, (10.0, 25.0),
         "C12 p-shell (10-25 MeV) vs fig 6 top"),
        (ax_ssh, "fig6_bot_q1p2", C12, (30.0, 50.0),
         "C12 s-shell (30-50 MeV) vs fig 6 bot"),
        (ax_pm_fe, "fig7_q1p2", FE, (0.0, 80.0),
         r"Fe56 ($E_m$ < 80 MeV) vs fig 7"),
    ]:
        x, y, e = load_dutta(stem)
        pos = x > 0
        s_data = 4.0 * np.pi * (y[pos] * x[pos] ** 2).sum() * 40.0
        ratios = []
        for name, res, color in tabs:
            ratios.append(f"{s_data / pm_strength(res, E_win):.2f}")
            if args.native:
                nk, edges = pm_native(res, E_win)
                vv, ee = mirror(nk, edges)
            else:
                vv, ee = mirror(pm_profile(res, E_win), P_BINS)
            ax.stairs(vv, ee, color=color, lw=2.0, zorder=4, label=name)
        m = y > 0
        ax.errorbar(x[m], y[m], yerr=e[m], fmt="s", ms=5, color="black",
                    capsize=2, zorder=9, label="Dutta data")
        ax.text(0.03, 0.97, f"data/table = {', '.join(ratios)}",
                transform=ax.transAxes, va="top", fontsize=FS_TICK)
        style_axis(ax, title=title, xlabel=r"$p_m$  [MeV/c]",
                   ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                   logx=False, ymin=None)
        ax.set_xlim(-340, 340)

    binning = ("native table binning" if args.native else "data binning")
    fig.suptitle("GENIE input tables vs Dutta E91-013, same phase space "
                 rf"($|p_m|$ < 300 MeV/c windows, {binning})"
                 "\ntables on their native N$\\cdot$P (occupancy) scale; "
                 "data FSI-distorted on published (renormalized) scales; "
                 r"figs 6/7 at $Q^2$ = 1.28",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = HERE / ("dutta_table_overlay_native.png" if args.native
                  else "dutta_table_overlay.png")
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

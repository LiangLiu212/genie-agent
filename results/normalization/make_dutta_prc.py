"""All 14 Dutta E91-013 author data files (PRC figs 6/7/9/11) in one figure,
with their normalization integrals.

Companion to this folder's README: the measured (distorted, renormalized)
counterpart of the pke* input-table checks. Data column semantics per
report/dutta-e91013-figures.md -- col 1 = x, col 2 = y, col 4 = stat error;
col 3 skipped (x/200 duplicate with a sign glitch in fig7_q1p2 row 1).

Panels:
  top-left  = fig 6 top, C12 p-shell window p_m distribution, 4 Q^2 sets
  top-right = fig 6 bottom, C12 s-shell window
  bot-left  = fig 7, Fe56 full-window p_m distribution, 4 Q^2 sets
  bot-right = figs 9 + 11, E_m spectral functions at Q^2 = 1.28 (C12, Fe56)

Printed integrals (stat-only errors in quadrature):
  p_m sets (figs 6/7): the 3D momentum integral  4*pi * Sigma y p_m^2 dp_m
    over the POSITIVE-half bins only (the files are exactly left-right
    symmetrized, so the positive half covers |p_m| in [0, 320) once);
    y = int S^D dE_m [MeV^-3], so the result is dimensionless strength.
  E_m spectra (figs 9/11): Sigma y * 5 MeV (y is already int S^D d^3p_m).

Usage:
  pixi run python results/normalization/make_dutta_prc.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))

import numpy as np
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LEGEND, FS_SUPTITLE, DPI)           # noqa: E402

DATA = HERE.parents[1] / "data" / "Dipingkar-dutta-data-prc_figs"

# Q^2 sets: file tag, legend label, marker (mirroring the paper's shapes)
QSETS = [
    ("q0p6", r"$Q^2$ = 0.64 (GeV/c)$^2$", "s"),
    ("q1p2", r"$Q^2$ = 1.28 (GeV/c)$^2$", "o"),
    ("q1p8", r"$Q^2$ = 1.8 (GeV/c)$^2$", "*"),
    ("q3p2", r"$Q^2$ = 3.25 (GeV/c)$^2$", "^"),
]

PM_XLABEL = r"$p_m$  [MeV/c]"
PM_YLABEL = r"$\int S^D\,dE_m$   [MeV$^{-3}$]"
EM_XLABEL = r"$E_m$  [MeV]"
EM_YLABEL = r"$\int S^D\,d^3p_m$   [MeV$^{-1}$]"


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def report_integral_em(stem, y, e, dE=5.0):
    I = y.sum() * dE
    dI = np.sqrt((e ** 2).sum()) * dE
    print(f"{stem:15s} int y dE_m         = {I:8.4f} +- {dI:.4f}")
    return I


def report_integral_3d(stem, x, y, e, dp=40.0):
    m = x > 0                       # symmetrized: positive half = full |p_m| range
    I = 4.0 * np.pi * (y[m] * x[m] ** 2).sum() * dp
    dI = 4.0 * np.pi * np.sqrt(((e[m] * x[m] ** 2) ** 2).sum()) * dp
    print(f"{stem:15s} 4pi int y p^2 dp_m = {I:8.4f} +- {dI:.4f}")
    return I


def draw_pm_sets(ax, prefix):
    for (tag, label, marker), color in zip(QSETS, COLORS):
        x, y, e = load(f"{prefix}_{tag}")
        report_integral_3d(f"{prefix}_{tag}", x, y, e)
        m = y > 0  # log scale
        ax.errorbar(x[m], y[m], yerr=e[m], fmt=marker, color=color,
                    ms=9 if marker == "*" else 5, lw=1, capsize=2, label=label)


def main():
    apply_style()
    fig, (ax_p, ax_s, ax_fe, ax_em) = new_panels(ncols=2, nrows=2, sharey=False)

    draw_pm_sets(ax_p, "fig6_top")
    style_axis(ax_p, title="fig 6 top -- C12 p-shell (10-25 MeV)",
               xlabel=PM_XLABEL, ylabel=PM_YLABEL, logx=False, ymin=5e-10)
    ax_p.set_ylim(5e-10, 6e-7)
    ax_p.legend(fontsize=FS_LEGEND - 2, ncols=2, frameon=False,
                loc="upper center")

    draw_pm_sets(ax_s, "fig6_bot")
    style_axis(ax_s, title="fig 6 bot -- C12 s-shell (30-50 MeV)",
               xlabel=PM_XLABEL, ylabel=PM_YLABEL, logx=False, ymin=5e-10)
    ax_s.set_ylim(5e-10, 6e-7)

    draw_pm_sets(ax_fe, "fig7")
    style_axis(ax_fe, title=r"fig 7 -- Fe56 ($E_m$ < 80 MeV)",
               xlabel=PM_XLABEL, ylabel=PM_YLABEL, logx=False, ymin=5e-9)
    ax_fe.set_ylim(5e-9, 4e-6)

    for stem, label, color in [
        ("fig9_q1p2", r"fig 9 -- C12", COLORS[0]),
        ("fig11_q1p2", r"fig 11 -- Fe56", COLORS[1]),
    ]:
        x, y, e = load(stem)
        report_integral_em(stem, y, e)
        ax_em.errorbar(x, y, yerr=e, fmt="s" if "9" in stem else "o",
                       color=color, ms=5, lw=1, capsize=2, label=label)
    style_axis(ax_em, title=r"figs 9/11 -- $E_m$ spectra, $Q^2$=1.28",
               xlabel=EM_XLABEL, ylabel=EM_YLABEL, logx=False, logy=False)
    ax_em.set_xlim(0, 85)
    ax_em.set_ylim(-0.02, 1.0)
    ax_em.legend(fontsize=FS_LEGEND, frameon=False, loc="upper right")

    fig.suptitle("Dutta E91-013 (e,e'p) author data -- figs 6, 7, 9, 11\n"
                 "(distorted spectral functions, published normalization)",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = HERE / "dutta_prc_data.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

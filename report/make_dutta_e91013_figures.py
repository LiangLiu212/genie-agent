"""Replot Dutta E91-013 figs 6/7/9/11 from the author data files.

Companion to report/dutta-e91013-figures.md: renders the 14 .dat files in
data/Dipingkar-dutta-data-prc_figs/ on the same axes as the published figures
(papers/nucl-ex_0303011/figures/fig{6,7,9,11}.png) so the report can show the
two side by side. Column 1 = x, column 2 = y, column 4 = statistical error;
column 3 is skipped (x/200 duplicate with a sign glitch in fig7_q1p2 row 1).

Run from the repo root:  pixi run python report/make_dutta_e91013_figures.py
Outputs: report/figures/dutta_fig{6,7,9,11}_replot.png
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "results/template")
from plot_style import (COLORS, DPI, FS_LEGEND, FS_TITLE, apply_style,
                        new_panels, style_axis)

apply_style()
import matplotlib.pyplot as plt

DATA = Path("data/Dipingkar-dutta-data-prc_figs")
OUT = Path("report/figures")
OUT.mkdir(exist_ok=True)

# Q^2 sets: file tag, legend label, marker (mirroring the paper's shapes)
QSETS = [
    ("q0p6", r"$Q^2$ = 0.64 (GeV/c)$^2$", "s"),
    ("q1p2", r"$Q^2$ = 1.28 (GeV/c)$^2$", "o"),
    ("q1p8", r"$Q^2$ = 1.8 (GeV/c)$^2$", "*"),
    ("q3p2", r"$Q^2$ = 3.25 (GeV/c)$^2$", "^"),
]

PM_XLABEL = r"$p_m$ (MeV/c)"
PM_YLABEL = r"$\int S^D(E_m,p_m)\,dE_m$ (MeV$^{-3}$)"
EM_XLABEL = r"$E_m$ (MeV)"
EM_YLABEL = r"$\int S^D(E_m,p_m)\,d^3p_m$ (MeV$^{-1}$)"


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def draw_pm_sets(ax, prefix):
    """Overlay the four Q^2 datasets of a p_m-distribution panel (log y)."""
    for (tag, label, marker), color in zip(QSETS, COLORS):
        x, y, e = load(f"{prefix}_{tag}")
        m = y > 0  # log scale
        ax.errorbar(x[m], y[m], yerr=e[m], fmt=marker, color=color,
                    ms=9 if marker == "*" else 5, lw=1, capsize=2, label=label)
    ax.legend(fontsize=FS_LEGEND, ncols=2, frameon=False, loc="upper center")


# ---- fig 6: carbon p-shell (top) / s-shell (bottom) momentum distributions
fig, (ax_p, ax_s) = new_panels(ncols=1, nrows=2, sharey=True)
fig.set_size_inches(7, 10.5)
draw_pm_sets(ax_p, "fig6_top")
draw_pm_sets(ax_s, "fig6_bot")
style_axis(ax_p, title=r"C p-shell (10 < $E_m$ < 25 MeV)",
           ylabel=PM_YLABEL, logx=False, ymin=5e-10)
style_axis(ax_s, title=r"C s-shell (30 < $E_m$ < 50 MeV)",
           xlabel=PM_XLABEL, ylabel=PM_YLABEL, logx=False, ymin=5e-10)
ax_p.set_ylim(5e-10, 6e-7)  # headroom band for the in-axes legends (shared y)
fig.suptitle("Dutta fig. 6 data files", fontsize=FS_TITLE)
fig.tight_layout()
fig.savefig(OUT / "dutta_fig6_replot.png", dpi=DPI)
plt.close(fig)

# ---- fig 7: iron momentum distribution, 0 < E_m < 80 MeV
fig, (ax,) = new_panels(ncols=1, nrows=1)
fig.set_size_inches(7, 5.5)
draw_pm_sets(ax, "fig7")
style_axis(ax, title=r"Dutta fig. 7 data files — Fe (0 < $E_m$ < 80 MeV)",
           xlabel=PM_XLABEL, ylabel=PM_YLABEL, logx=False, ymin=5e-9)
ax.set_ylim(5e-9, 4e-6)
fig.tight_layout()
fig.savefig(OUT / "dutta_fig7_replot.png", dpi=DPI)
plt.close(fig)

# ---- figs 9 / 11: missing-energy spectral functions at Q^2 = 1.28 (linear)
# open_questions.md: the published fig9 bars, pixel-measured, exceed the stat-only
# column 4 where visible -- +-0.046 MeV^-1 at E_m = 17.5 and +-0.013 at 22.5.
FIG9_PUBLISHED_BARS = {17.5: 0.046, 22.5: 0.013}

for stem, label, published_bars, ymax in [
    ("fig9_q1p2", r"$^{12}$C, $Q^2$ = 1.28 (GeV/c)$^2$", FIG9_PUBLISHED_BARS, 0.7),
    ("fig11_q1p2", r"$^{56}$Fe, $Q^2$ = 1.28 (GeV/c)$^2$", {}, 1.5),
]:
    x, y, e = load(stem)
    fig, (ax,) = new_panels(ncols=1, nrows=1)
    if published_bars:
        xb = np.array(sorted(published_bars))
        yb = np.array([y[x == v][0] for v in xb])
        eb = np.array([published_bars[v] for v in xb])
        ax.errorbar(xb, yb, yerr=eb, fmt="none", ecolor="0.6", elinewidth=4,
                    capsize=5, label="published bars (pixel-measured)")
    ax.errorbar(x, y, yerr=e, fmt="s", color=COLORS[0], ms=5, lw=1,
                capsize=2, label="data file (stat errors, col 4)")
    ax.text(0.95, 0.93, label, transform=ax.transAxes, ha="right",
            fontsize=FS_LEGEND + 2)
    ax.legend(fontsize=FS_LEGEND, frameon=False, loc="upper right",
              bbox_to_anchor=(1.0, 0.62))
    ax.set_xlim(0, 85)
    ax.set_ylim(-0.02, ymax)
    fignum = stem.split("_")[0].replace("fig", "")
    style_axis(ax, title=f"Dutta fig. {fignum} data file",
               xlabel=EM_XLABEL, ylabel=EM_YLABEL, logx=False, logy=False)
    fig.tight_layout()
    fig.savefig(OUT / f"dutta_fig{fignum}_replot.png", dpi=DPI)
    plt.close(fig)

print(f"wrote 4 figures to {OUT}/")

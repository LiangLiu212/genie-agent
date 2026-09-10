"""Published Dutta figure next to its replot from the author data table.

Section 1 of report/dutta-integral/README.md: for each of the four
data-backed figures of nucl-ex/0303011 (fig 9: C12 E_m; fig 6: C12 p_m,
p-shell / s-shell panels; fig 11: Fe56 E_m; fig 7: Fe56 p_m) put the paper's
render (papers/nucl-ex_0303011/figures/fig<N>.png) on the left and, on the
right, the same quantity drawn from data/Dipingkar-dutta-data-prc_figs/
on the same axes (linear for the E_m figures, log y for the p_m ones, the
paper's marker shapes per Q^2 set). Column 1 = x, column 2 = y as
published, column 4 = statistical error; nothing is rescaled.

Outputs (report/dutta-integral/figures/):
  dutta_fig9_c12_em_published_vs_table.png
  dutta_fig6_c12_pm_published_vs_table.png
  dutta_fig11_fe56_em_published_vs_table.png
  dutta_fig7_fe56_pm_published_vs_table.png
  dutta_published_vs_table.txt   ratio of every p_m file to its Q^2 = 1.8
                                 reference + histdiag describe1d of all 14 files

Run from anywhere:  pixi run python report/dutta-integral/make_published_vs_table.py
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "data" / "Dipingkar-dutta-data-prc_figs"
PUB = REPO / "papers" / "nucl-ex_0303011" / "figures"
OUT = HERE / "figures"

sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (COLORS, DPI, FS_LEGEND, FS_SUPTITLE, FS_TITLE,  # noqa: E402
                        apply_style, style_axis)
import histdiag as hd  # noqa: E402

apply_style()
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec  # noqa: E402

DE_MEV, DP_MEVC = 5.0, 40.0
EM_EDGES = np.arange(0.0, 80.0 + DE_MEV, DE_MEV)
PM_EDGES = np.arange(-320.0, 320.0 + DP_MEVC, DP_MEVC)

# the four Q^2 sets of figs 6/7: file tag, legend label, marker (paper's shapes)
QSETS = [("q0p6", r"$Q^2$ = 0.64 (GeV/c)$^2$", "s"),
         ("q1p2", r"$Q^2$ = 1.28 (GeV/c)$^2$", "o"),
         ("q1p8", r"$Q^2$ = 1.8 (GeV/c)$^2$", "*"),
         ("q3p2", r"$Q^2$ = 3.25 (GeV/c)$^2$", "^")]
REF_TAG = "q1p8"          # the caption's rescale reference

EM_XLABEL = r"$E_m$ (MeV)"
EM_YLABEL = r"$\int S^D\,d^3p_m$  [MeV$^{-1}$]"
PM_XLABEL = r"$p_m$ (MeV/c)"
PM_YLABEL = r"$\int S^D\,dE_m$  [MeV$^{-3}$]"


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def published_panel(ax, fignum, pad=12):
    """The paper's render, autocropped to its ink (the eps renders carry wide
    white margins that would shrink the figure next to the replot)."""
    img = mpimg.imread(PUB / f"fig{fignum}.png")
    ink = img[..., :3].min(axis=2) < 0.95
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    img = img[max(rows[0] - pad, 0):rows[-1] + pad, max(cols[0] - pad, 0):cols[-1] + pad]
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(f"published fig. {fignum}", fontsize=FS_TITLE)


def em_panel(ax, stem, label, ymax):
    """E_m spectral function from one table: points + stat errors, paper axes."""
    x, y, e = load(stem)
    ax.errorbar(x, y, yerr=e, fmt="s", ms=5, lw=1, capsize=2, color=COLORS[0])
    ax.text(0.95, 0.9, label, transform=ax.transAxes, ha="right",
            fontsize=FS_LEGEND + 2)
    ax.set_xlim(0, 85)
    ax.set_ylim(-0.02, ymax)
    style_axis(ax, title=f"from the table: {stem}.dat",
               xlabel=EM_XLABEL, ylabel=EM_YLABEL)


def pm_panel(ax, prefix, title, ylim):
    """p_m distribution: the four Q^2 files of one panel, log y, paper markers."""
    for (tag, label, marker), color in zip(QSETS, COLORS):
        x, y, e = load(f"{prefix}_{tag}")
        m = y > 0
        ax.errorbar(x[m], y[m], yerr=e[m], fmt=marker, color=color,
                    ms=9 if marker == "*" else 5, lw=1, capsize=2, label=label)
    ax.set_xlim(-320, 320)
    style_axis(ax, title=title, xlabel=PM_XLABEL, ylabel=PM_YLABEL,
               logy=True, ymin=ylim[0])
    ax.set_ylim(*ylim)
    ax.legend(fontsize=FS_LEGEND, ncols=2, frameon=False, loc="upper center",
              handlelength=1.0, handletextpad=0.4, columnspacing=1.0)


def composite_em(fignum, stem, label, ymax, suptitle, out):
    fig = plt.figure(figsize=(10.5, 5.5))
    gs = GridSpec(1, 2, figure=fig)
    published_panel(fig.add_subplot(gs[0]), fignum)
    em_panel(fig.add_subplot(gs[1]), stem, label, ymax)
    fig.suptitle(suptitle, fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(OUT / out, dpi=DPI)
    plt.close(fig)
    return out


def composite_pm(fignum, panels, suptitle, out, figsize):
    """panels: [(file prefix, panel title, (ymin, ymax)), ...] stacked on the right."""
    fig = plt.figure(figsize=figsize)
    gs = GridSpec(1, 2, figure=fig)
    published_panel(fig.add_subplot(gs[0]), fignum)
    sub = GridSpecFromSubplotSpec(len(panels), 1, subplot_spec=gs[1], hspace=0.45)
    for i, (prefix, title, ylim) in enumerate(panels):
        pm_panel(fig.add_subplot(sub[i]), prefix, title, ylim)
    fig.suptitle(suptitle, fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(OUT / out, dpi=DPI)
    plt.close(fig)
    return out


def readouts(path):
    """Ratios of every p_m file to its Q^2 = 1.8 reference (the caption's
    normalization) and histdiag describe1d of all 14 files."""
    with open(path, "w") as fh:
        fh.write("Dutta author data tables: ratio to the Q^2 = 1.8 reference file "
                 "and histdiag describe1d readouts\n"
                 "weights = column 2 as published (no rescaling), errors = column 4 "
                 "(statistical); integral = Sum y (bin values, not Sum y dx)\n\n")
        fh.write("== ratio y / y(q1p8) over the 16 signed p_m bins (figs 6/7 are "
                 "normalized to the Q^2 = 1.8 integral in print)\n")
        fh.write(f"{'panel':10s} {'Q2 set':7s} {'median':>8s} {'min':>8s} {'max':>8s}"
                 f"  {'Sum y dp / ref':>14s}\n")
        for prefix in ("fig6_top", "fig6_bot", "fig7"):
            _, yref, _ = load(f"{prefix}_{REF_TAG}")
            for tag, _, _ in QSETS:
                if tag == REF_TAG:
                    continue
                _, y, _ = load(f"{prefix}_{tag}")
                r = y / yref
                fh.write(f"{prefix:10s} {tag:7s} {np.median(r):8.3f} {r.min():8.3f} "
                         f"{r.max():8.3f}  {y.sum() / yref.sum():14.3f}\n")
        fh.write("\n")
        for stem in ("fig9_q1p2", "fig11_q1p2"):
            x, y, e = load(stem)
            hd.describe1d(y, EM_EDGES, errors=e, table=True, quiet=True, save=fh,
                          name=f"E_m  {stem}.dat  [MeV]")
            fh.write("\n")
        for prefix in ("fig6_top", "fig6_bot", "fig7"):
            for tag, _, _ in QSETS:
                stem = f"{prefix}_{tag}"
                x, y, e = load(stem)
                hd.describe1d(y, PM_EDGES, errors=e, table=True, quiet=True, save=fh,
                              name=f"p_m  {stem}.dat  [MeV/c]")
                fh.write("\n")


def main():
    OUT.mkdir(exist_ok=True)
    q2 = r"$Q^2$ = 1.28 (GeV/c)$^2$"
    outs = [
        composite_em(9, "fig9_q1p2", r"$^{12}$C, " + q2, 0.7,
                     r"Dutta fig. 9: $^{12}$C missing-energy spectral function, " + q2,
                     "dutta_fig9_c12_em_published_vs_table.png"),
        composite_pm(6, [("fig6_top", r"C p-shell (10 < $E_m$ < 25 MeV)", (8e-10, 2e-6)),
                         ("fig6_bot", r"C s-shell (30 < $E_m$ < 50 MeV)", (8e-10, 2e-6))],
                     r"Dutta fig. 6: $^{12}$C missing-momentum distributions",
                     "dutta_fig6_c12_pm_published_vs_table.png", (10.5, 8.5)),
        composite_em(11, "fig11_q1p2", r"$^{56}$Fe, " + q2, 1.5,
                     r"Dutta fig. 11: $^{56}$Fe missing-energy spectral function, " + q2,
                     "dutta_fig11_fe56_em_published_vs_table.png"),
        composite_pm(7, [("fig7", r"Fe (0 < $E_m$ < 80 MeV)", (1e-9, 2e-5))],
                     r"Dutta fig. 7: $^{56}$Fe missing-momentum distribution",
                     "dutta_fig7_fe56_pm_published_vs_table.png", (10.5, 5.5)),
    ]
    for o in outs:
        print("wrote", OUT / o)
    readouts(OUT / "dutta_published_vs_table.txt")
    print("wrote", OUT / "dutta_published_vs_table.txt")


if __name__ == "__main__":
    main()

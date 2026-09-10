"""Side-by-side E_m and p_m panels from the Dutta E91-013 author data tables.

Section 1 of report/dutta-integral/README.md: for each nucleus (rows: C12,
Fe56) draw the missing-energy spectral function (left, figs 9 / 11) next to
the missing-momentum distribution (right, figs 6 / 7) at the same kinematics,
Q^2 = 1.28 (GeV/c)^2, straight from the .dat files in
data/Dipingkar-dutta-data-prc_figs/ -- column 1 = x, column 2 = y as
published, column 4 = statistical error; column 3 (x/200, sign glitch in
fig7_q1p2 row 1) is skipped. Nothing is rescaled: the y values are the
published ones (the factor-2 convention of the E_m files is the subject of
the later sections, not of this figure). The E_m windows the p_m panels
integrate over are shaded on the E_m panels.

Outputs (report/dutta-integral/figures/):
  dutta_empm_sidebyside.png       linear axes (house default)
  dutta_empm_sidebyside_log.png   log y; zero bins are not drawn
  dutta_empm_sidebyside.txt       histdiag describe1d readout of every series
                                  (weights = the published y, errors = col 4)

Run from anywhere:  pixi run python report/dutta-integral/make_empm_sidebyside.py
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "data" / "Dipingkar-dutta-data-prc_figs"
OUT = HERE / "figures"

sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (COLORS, DPI, FS_LEGEND, FS_SUPTITLE, apply_style,  # noqa: E402
                        new_panels, style_axis)
import histdiag as hd  # noqa: E402

apply_style()
import matplotlib.pyplot as plt  # noqa: E402

DE_MEV = 5.0                                   # E_m bin width, figs 9/11
DP_MEVC = 40.0                                 # p_m bin width, figs 6/7
EM_EDGES = np.arange(0.0, 80.0 + DE_MEV, DE_MEV)        # 16 bins, centres 2.5..77.5
PM_EDGES = np.arange(-320.0, 320.0 + DP_MEVC, DP_MEVC)  # 16 bins, centres -300..300

EM_XLABEL = r"$E_m$ (MeV)"
EM_YLABEL = r"$\int S^D\,d^3p_m$  [MeV$^{-1}$]"
PM_XLABEL = r"$p_m$ (MeV/c)"
PM_YLABEL = r"$\int S^D\,dE_m$  [MeV$^{-3}$]"
EM_RANGE_LABEL = r"($|p_m| < 300$ MeV/c)"

# rows of the figure: nucleus -> E_m file (figs 9/11) and the p_m files
# (figs 6/7) with the E_m window each one integrates over, its label, colour;
# em_ylim_log / pm_ylim_log are the log-variant y ranges (zero bins hidden)
PANELS = {
    "C12": dict(
        title=r"$^{12}$C", em="fig9_q1p2", em_fig=9, pm_fig=6,
        pm=[("fig6_top_q1p2", (10, 25), "p-shell window", COLORS[1]),
            ("fig6_bot_q1p2", (30, 50), "s-shell window", COLORS[2])],
        em_ylim_log=(1e-3, 30.0), pm_ylim_log=(5e-10, 3e-6)),
    "Fe56": dict(
        title=r"$^{56}$Fe", em="fig11_q1p2", em_fig=11, pm_fig=7,
        pm=[("fig7_q1p2", (0, 80), "all shells", COLORS[0])],
        em_ylim_log=(1e-2, 20.0), pm_ylim_log=(5e-9, 1e-5)),
}
EM_COLOR = COLORS[0]
HEADROOM = 1.6      # linear y range = HEADROOM x max(data), room for the legend


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def draw_series(ax, x, y, e, color, label, logy):
    m = y > 0 if logy else np.ones_like(y, dtype=bool)
    ax.errorbar(x[m], y[m], yerr=e[m], fmt="-o", ms=3, lw=1, capsize=2,
                color=color, label=label)


def draw(logy):
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    for row, (nucleus, spec) in enumerate(PANELS.items()):
        ax_em, ax_pm = axes[2 * row], axes[2 * row + 1]

        # ---- left: missing-energy spectral function (integrated over signed p_m)
        x, y, e = load(spec["em"])
        draw_series(ax_em, x, y, e, EM_COLOR,
                    f"{spec['em']}.dat  {EM_RANGE_LABEL}", logy)
        for _, (lo, hi), lab, col in spec["pm"]:
            if (lo, hi) != (0, 80):        # the full window is the whole axis
                ax_em.axvspan(lo, hi, color=col, alpha=0.12,
                              label=f"{lab} {lo}–{hi} MeV")
        ax_em.set_xlim(0, 80)
        style_axis(ax_em, title=f"{spec['title']} missing energy (fig. {spec['em_fig']})",
                   xlabel=EM_XLABEL, ylabel=EM_YLABEL, logy=logy,
                   ymin=spec["em_ylim_log"][0])
        ax_em.set_ylim(*(spec["em_ylim_log"] if logy else (0, HEADROOM * y.max())))
        ax_em.legend(fontsize=FS_LEGEND, frameon=False, loc="upper right")

        # ---- right: missing-momentum distribution(s) (integrated over E_m windows)
        ymax = 0.0
        for stem, (lo, hi), lab, col in spec["pm"]:
            x, y, e = load(stem)
            draw_series(ax_pm, x, y, e, col,
                        f"{stem}.dat  ({lo} < $E_m$ < {hi} MeV)", logy)
            ymax = max(ymax, y.max())
        ax_pm.set_xlim(-320, 320)
        style_axis(ax_pm, title=f"{spec['title']} missing momentum (fig. {spec['pm_fig']})",
                   xlabel=PM_XLABEL, ylabel=PM_YLABEL, logy=logy,
                   ymin=spec["pm_ylim_log"][0])
        ax_pm.set_ylim(*(spec["pm_ylim_log"] if logy else (0, HEADROOM * ymax)))
        ax_pm.legend(fontsize=FS_LEGEND, frameon=False, loc="upper center")

    fig.suptitle(r"Dutta E91-013 (e,e'p) data tables at $Q^2$ = 1.28 (GeV/c)$^2$",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    name = "dutta_empm_sidebyside" + ("_log" if logy else "")
    fig.savefig(OUT / f"{name}.png", dpi=DPI)
    plt.close(fig)
    return name


def readouts(path):
    """histdiag describe1d of every plotted series, on the published y with
    the tabulated statistical errors, kept next to the PNG."""
    with open(path, "w") as fh:
        fh.write("histdiag describe1d readouts of the series in "
                 "dutta_empm_sidebyside.png\n"
                 "weights = column 2 as published (no rescaling), errors = column 4 "
                 "(statistical); integral = Sum y (bin values, not Sum y dx)\n\n")
        for nucleus, spec in PANELS.items():
            x, y, e = load(spec["em"])
            hd.describe1d(y, EM_EDGES, errors=e, table=True, quiet=True, save=fh,
                          name=f"{nucleus} E_m  {spec['em']}.dat  [MeV]")
            fh.write("\n")
            for stem, (lo, hi), lab, _ in spec["pm"]:
                x, y, e = load(stem)
                hd.describe1d(y, PM_EDGES, errors=e, table=True, quiet=True, save=fh,
                              name=f"{nucleus} p_m  {stem}.dat  ({lo}<E_m<{hi} MeV)  [MeV/c]")
                fh.write("\n")


def main():
    OUT.mkdir(exist_ok=True)
    for logy in (False, True):
        print("wrote", OUT / f"{draw(logy)}.png")
    readouts(OUT / "dutta_empm_sidebyside.txt")
    print("wrote", OUT / "dutta_empm_sidebyside.txt")


if __name__ == "__main__":
    main()

"""Plot ALL QES-archive inclusive (e,e') settings for 12C and 56Fe.

Companion to make_electron_scattering_data.py (which covers only 2-3 GeV):
one panel per beam energy, one series per (theta, citation). Axes are linear
by default; a panel opts into log y when its settings span more than two
decades in sigma (the multi-angle >= 4 GeV sets), per the plot-style rule.
12C includes the 2024 Mihovilovic 855 MeV / 70 deg set from Miho_12C.dat
(MeV units in the source file, converted here).

Run: pixi run python report/make_electron_scattering_all.py
"""

import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

DATA = REPO / "data" / "qes-archive"
OUT = REPO / "report"
NCOLS = 3
LOGY_RATIO = 100.0    # panel switches to log y above this max/min sigma spread


def load(datfile, scale=1.0):
    """-> {E: {(theta, citation): ([omega], [sigma], [err])}}, energies in GeV."""
    by_e = defaultdict(lambda: defaultdict(lambda: ([], [], [])))
    for line in datfile.read_text().splitlines():
        t = line.split()
        if len(t) < 8:
            continue
        try:
            e, theta, omega, sigma, err = (float(t[2]) * scale, float(t[3]),
                                           float(t[4]) * scale, float(t[5]),
                                           float(t[6]))
        except ValueError:        # header/comment lines (Miho file)
            continue
        ser = by_e[e][(theta, t[-1])]
        ser[0].append(omega); ser[1].append(sigma); ser[2].append(err)
    return by_e


def plot(nucleus, by_e, png):
    energies = sorted(by_e)
    nrows = (len(energies) + NCOLS - 1) // NCOLS
    fig, axes = new_panels(ncols=NCOLS, nrows=nrows, sharey=False)
    for ax, e in zip(axes, energies):
        allsig = [s for d in by_e[e].values() for s in d[1] if s > 0]
        logy = max(allsig) / min(allsig) > LOGY_RATIO
        for i, (theta, cite) in enumerate(sorted(by_e[e])):
            om, sig, err = by_e[e][(theta, cite)]
            ax.errorbar(om, sig, yerr=err, fmt="o", ms=3, capsize=2,
                        color=COLORS[i % len(COLORS)],
                        label=f"{theta:g}°  {cite}")
        style_axis(ax, title=f"E = {e:g} GeV", xlabel="$\\omega$  [GeV]",
                   logy=logy, ymin=None)
        ax.legend(fontsize=FS_LEGEND - 2)
    for ax in axes[len(energies):]:
        ax.set_visible(False)
    for r in range(nrows):
        axes[r * NCOLS].set_ylabel(
            "$d\\sigma/d\\Omega\\,d\\omega$  [nb/sr/GeV]", fontsize=FS_LABEL)
    # reserve a fixed ~0.5 in for the suptitle: on a tall grid the default
    # y=0.98 lands inside the first panel row
    top = 1 - 0.5 / (5 * nrows)
    fig.suptitle(f"{nucleus}(e,e') inclusive cross sections — "
                 "all QES-archive settings", fontsize=FS_SUPTITLE,
                 y=1 - 0.15 / (5 * nrows))
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(png, dpi=DPI)
    npts = sum(len(s[0]) for d in by_e.values() for s in d.values())
    print(f"{png}: {len(energies)} panels, {npts} points")


apply_style()

c12 = load(DATA / "12C.dat")
for e, d in load(DATA / "Miho_12C.dat", scale=1e-3).items():
    c12[e].update(d)
plot("$^{12}$C", c12, OUT / "c12_all.png")
plot("$^{56}$Fe", load(DATA / "56Fe.dat"), OUT / "fe56_all.png")

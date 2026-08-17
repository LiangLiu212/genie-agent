"""Plot QES-archive inclusive (e,e') data for 12C and 56Fe, beam energy 2.0-3.0 GeV.

Data: data/qes-archive/{12C,56Fe}.dat (Day archive, nucl-ex/0603032).
Columns: Z A E(GeV) theta(deg) omega(GeV) sigma(nb/sr/GeV) err [syst] citation.
One figure per nucleus, one panel per beam energy, one series per (theta, citation).

Run: pixi run python report/make_electron_scattering_data.py
"""

import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

EMIN, EMAX = 2.0, 3.0
DATA = REPO / "data" / "qes-archive"
OUT = REPO / "report"


def load(datfile):
    """-> {E: {(theta, citation): ([omega], [sigma], [err])}} for the E window."""
    by_e = defaultdict(lambda: defaultdict(lambda: ([], [], [])))
    for line in datfile.read_text().splitlines():
        t = line.split()
        if len(t) < 8:
            continue
        e, theta, omega, sigma, err = (float(t[2]), float(t[3]),
                                       float(t[4]), float(t[5]), float(t[6]))
        if not (EMIN <= e <= EMAX):
            continue
        ser = by_e[e][(theta, t[-1])]
        ser[0].append(omega); ser[1].append(sigma); ser[2].append(err)
    return by_e


def plot(nucleus, datfile, png):
    by_e = load(datfile)
    energies = sorted(by_e)
    ncols = 3
    nrows = (len(energies) + ncols - 1) // ncols
    # per-panel y scale: on linear axes the settings span ~3 decades in sigma
    fig, axes = new_panels(ncols=ncols, nrows=nrows, sharey=False)
    for ax, e in zip(axes, energies):
        for i, (theta, cite) in enumerate(sorted(by_e[e])):
            om, sig, err = by_e[e][(theta, cite)]
            ax.errorbar(om, sig, yerr=err, fmt="o", ms=3, capsize=2,
                        color=COLORS[i % len(COLORS)],
                        label=f"{theta:g}°  {cite}")
        style_axis(ax, title=f"E = {e:g} GeV",
                   xlabel="$\\omega$  [GeV]", ymin=None)
        ax.legend(title="$\\theta$, dataset", fontsize=FS_LEGEND,
                  title_fontsize=FS_LEGEND_TITLE)
    for ax in axes[len(energies):]:
        ax.set_visible(False)
    for r in range(nrows):
        axes[r * ncols].set_ylabel(
            "$d\\sigma/d\\Omega\\,d\\omega$  [nb/sr/GeV]", fontsize=FS_LABEL)
    fig.suptitle(f"{nucleus}(e,e') inclusive cross sections, "
                 f"E = {EMIN:g}–{EMAX:g} GeV (QES archive)",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(png, dpi=DPI)
    print(f"{png}: {len(energies)} panels, "
          f"{sum(len(s[0]) for d in by_e.values() for s in d.values())} points")


apply_style()
plot("$^{12}$C", DATA / "12C.dat", OUT / "c12_2to3gev.png")
plot("$^{56}$Fe", DATA / "56Fe.dat", OUT / "fe56_2to3gev.png")

"""Plot Dutta et al. (nucl-ex/0303011) Fig. 9: carbon missing-energy spectral
function at Q^2 = 1.28 (GeV/c)^2, from the digitized data file
data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat.

File format (see report/simc-eep-normalization.md discussion): 4 columns
  Em [MeV] (bin center, 5 MeV bins) | integral S^D d3Pm [MeV^-1] | Em/200 | error
Linear axes on purpose: this reproduces the paper's linear-scale figure, not a
log-log spline plot.
"""

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LEGEND, DPI)

apply_style()
import matplotlib.pyplot as plt  # noqa: E402  (after Agg backend)

DATA = REPO / "data" / "Dipingkar-dutta-data-prc_figs" / "fig9_q1p2.dat"
OUT = REPO / "results" / "dutta_fig9_c12_q1p28_em.png"

em, sf, _, err = np.loadtxt(DATA, unpack=True)

fig, (ax,) = new_panels(ncols=1, sharey=False)
ax.errorbar(em, sf, yerr=err, fmt="o", ms=4, capsize=2,
            color=COLORS[0], label="Dutta et al. data (deradiated)")
style_axis(ax,
           title=r"$^{12}$C,  $Q^2 = 1.28$ (GeV/$c$)$^2$",
           xlabel=r"$E_m$  (MeV)",
           ylabel=r"$\int S^{D}(E_m, p_m)\,d^3p_m$   (MeV$^{-1}$)",
           logx=False, logy=False, ymin=None)
ax.set_xlim(0, 85)
ax.set_ylim(0, 0.7)
ax.legend(fontsize=FS_LEGEND)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print(f"saved {OUT}")

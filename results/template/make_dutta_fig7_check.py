"""Dutta Fig. 7 digitization check: replot the .dat files next to the paper figure.

Fig. 7 of nucl-ex/0303011 = Fe56 missing-momentum distribution
int S^D(E_m,p_m) dE_m (0 < E_m < 80 MeV) at the four Q^2 settings, log y.
Left panel: the digitized files data/Dipingkar-dutta-data-prc_figs/fig7_*.dat
replotted with the PAPER's marker/color coding (star 1.28 / blue triangle
0.64 / black circle 1.8 / red square 3.25) on the paper's axis ranges.
Right panel: the published render papers/nucl-ex_0303011/figures/fig7.png.

Known caveats of the .dat files (papers/nucl-ex_0303011/open_questions.md):
all four are exactly left-right symmetrized (y(-p) = y(+p); only 8 independent
values each; errors NOT symmetrized), and col 4 is statistical only. Col 3 is
an x/200 artifact (sign glitch in fig7_q1p2 row 1) and is skipped.

Usage: pixi run python results/template/make_dutta_fig7_check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import apply_style, style_axis, FS_LEGEND, FS_TITLE, FS_SUPTITLE, DPI

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data/Dipingkar-dutta-data-prc_figs"
PAPER_FIG = REPO / "papers/nucl-ex_0303011/figures/fig7.png"
OUT = REPO / "results/prd-analyzer-v0.1/dutta_fig7_replot_vs_paper.png"

# paper's own coding: (tag, label, marker, color)
QSETS = [
    ("q1p2", r"$Q^2$ = 1.28 (GeV/c)$^2$", "*", "black"),
    ("q0p6", r"$Q^2$ = 0.64 (GeV/c)$^2$", "^", "tab:blue"),
    ("q3p2", r"$Q^2$ = 3.25 (GeV/c)$^2$", "s", "red"),
    ("q1p8", r"$Q^2$ = 1.8 (GeV/c)$^2$",  "o", "black"),
]

apply_style()
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

fig, (axl, axr) = plt.subplots(1, 2, figsize=(13, 6.2), layout="constrained")

for tag, label, marker, color in QSETS:
    x, y, _, e = np.loadtxt(DATA / f"fig7_{tag}.dat", unpack=True)
    m = y > 0
    axl.errorbar(x[m], y[m], yerr=e[m], fmt=marker, color=color,
                 ms=10 if marker == "*" else 6,
                 mfc=color if marker in "s^" else color, lw=1, capsize=0,
                 label=label)
    print(f"fig7_{tag}: peak {y.max():.3e} MeV^-3 at |p_m|="
          f"{abs(x[np.argmax(y)]):.0f}, edge(300) {y[np.isclose(np.abs(x),300)].mean():.2e}, "
          f"symmetric: {np.allclose(y[np.argsort(x)], y[np.argsort(-x)])}")

axl.set_yscale("log")
style_axis(axl, title="digitized fig7_*.dat (paper marker coding)",
           xlabel=r"$P_{\rm miss}$  [MeV/c]", logx=False, logy=True, ymin=None)
axl.set_xlim(-330, 330)
axl.set_ylim(1e-9, 5e-6)
axl.set_ylabel(r"$\int S^D(E_m,p_m)\,dE_m$   (MeV$^{-3}$)", fontsize=FS_TITLE)
axl.legend(fontsize=FS_LEGEND - 2, ncols=2, frameon=False, loc="upper center")

axr.imshow(mpimg.imread(PAPER_FIG))
axr.set_axis_off()
axr.set_title("published Fig. 7 (nucl-ex/0303011)", fontsize=FS_TITLE)

fig.suptitle("Dutta Fig. 7 — Fe56 missing momentum (0 < $E_m$ < 80 MeV): "
             "digitized data vs published figure", fontsize=FS_SUPTITLE - 2)
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

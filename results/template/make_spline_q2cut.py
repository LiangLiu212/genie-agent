"""Regenerate results/spline_q2cut.png using the personal plot style.

Run from repo root:  pixi run python results/template/make_spline_q2cut.py
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import (apply_style, new_panels, style_axis, COLORS, FLOOR,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

# Spline XMLs pulled from the grid (one per tune). Adjust the glob/dir as needed.
SRC = os.environ.get("SPL_DIR", "/tmp/spl_cmp")
q2 = {"04_000": 0.54, "05_000": 1.18, "06_000": 1.70, "07_000": 1.73,
      "08_000": 3.15}
tgt_name = {"1000060120": "C12", "1000260560": "Fe56", "1000791970": "Au197"}
order = ["1000060120", "1000260560", "1000791970"]

data = {}
for f in sorted(glob.glob(os.path.join(SRC, "GEM21_11a_*.xml"))):
    tune = re.search(r"11a_(\d\d_\d\d\d)", f).group(1)
    root = ET.parse(f).getroot()
    per = {}
    for spl in root.iter("spline"):
        tgt = re.search(r"tgt:(\d+)", spl.get("name")).group(1)
        knots = [(float(k.find("E").text), float(k.find("xsec").text))
                 for k in spl.iter("knot")]
        per[tgt] = knots if tgt not in per else \
            [(e, a + b) for (e, a), (_, b) in zip(per[tgt], knots)]
    data[tune] = per

apply_style()
fig, axes = new_panels(ncols=3)
for ax, tgt in zip(axes, order):
    for i, tune in enumerate(sorted(data)):
        E = [e for e, _ in data[tune][tgt]]
        X = [max(x, FLOOR) for _, x in data[tune][tgt]]
        ax.plot(E, X, "-o", ms=3, color=COLORS[i % len(COLORS)],
                label=f"Q2cut={q2[tune]:.2f} ({tune[:2]})")
    style_axis(ax, title=f"{tgt_name[tgt]}  (e- EM-QES)", xlabel="E [GeV]")

# Set the shared y-range from the largest target (Au197) so its curves are not
# clipped by C12's smaller autoscale.
au197 = "1000791970"
ymax = max(x for tune in data for _, x in data[tune][au197])
axes[0].set_ylim(FLOOR, ymax * 2)   # sharey propagates to all panels

axes[0].set_ylabel("xsec  [GENIE units]", fontsize=FS_LABEL)
axes[0].legend(title="EM-MinQ2Limit [GeV$^2$]", fontsize=FS_LEGEND,
               title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("GEM21_11a EM-QES spline vs EM-MinQ2Limit cut  "
             "(e- on C12 / Fe56 / Au197)", fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/spline_q2cut.png"
fig.savefig(out, dpi=DPI)
print("saved", out)

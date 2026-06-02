"""EM-QES Q^2 distribution, SF vs LFG, across the 6 E91-013 energy points (C12, grid).

Reads one gst (100k-event process) per (config, energy point) from the staged grid outputs.
6 panels (one per beam-energy / Q2-cut setting); each overlays LFG (GEM26_11a) and SF
(GEM26_22a). Personal plot style (results/template/plot_style.py).
"""
import sys
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

STAGE = "/tmp/claude-12900/gem26"
CUTLIM = {"04": 0.54, "05": 1.18, "06": 1.70, "07": 1.73, "08": 3.15}
# (cut, beam E) for the 6 points, ordered
POINTS = [("04", "2.445"), ("04", "0.845"), ("05", "2.445"),
          ("06", "3.245"), ("07", "1.645"), ("08", "3.245")]

MAP = {}                                  # (cfg, cut, E) -> gst basename
for ln in open("/tmp/gst_map.txt"):
    cfg, cut, E, b = ln.split()
    MAP[(cfg, cut, E)] = b

def q2(cfg, cut, E):
    b = MAP.get((cfg, cut, E))
    if not b:
        return None
    return uproot.open(f"{STAGE}/{b}")["gst"]["Q2"].array(library="np")

BINS = np.logspace(np.log10(0.4), np.log10(7.0), 45)
apply_style()
fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
for ax, (cut, E) in zip(axes, POINTS):
    for cfg, col, lab in [("11a", "C0", "LFG"), ("22a", "C1", "SF")]:
        d = q2(cfg, cut, E)
        if d is None:
            continue
        ax.hist(d, bins=BINS, histtype="step", linewidth=1.7, color=col, label=lab)
    style_axis(ax, title=f"E={E} GeV · t{cut}  (Q²>{CUTLIM[cut]})",
               xlabel="Q²  [(GeV/c)²]", logx=True, logy=True, ymin=0.5)
for i in (0, 3):
    axes[i].set_ylabel("events / bin", fontsize=FS_LABEL)
axes[0].legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("EM-QES Q² distribution: SF vs LFG  (e⁻ on C12, 100k ev/point, GEM26 Rosenbluth)\n"
             "JLab E91-013 kinematics — one panel per beam-energy / Q²-cut setting",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/q2_gem26_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

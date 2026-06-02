"""EM-QES total cross-section spline vs energy for the GEM26 Rosenbluth Q2-cut tunes (C12).

Reads the grid gmkspl spline XMLs (one per config x cut) staged locally, sums the two
bound-nucleon sub-splines into the total C12 QEL-EM sigma(E), and overlays the five
EM-MinQ2Limit cuts (t04..t08). The spline is ground-state independent, so SF (GEM26_22a)
and LFG (GEM26_11a) coincide; we draw SF solid and LFG dashed to show the overlap.
Personal plot style (results/template/plot_style.py).
"""
import sys, glob, re, os
sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

STAGE = "/tmp/claude-12900/gem26"
CUTS = {"04": 0.54, "05": 1.18, "06": 1.70, "07": 1.73, "08": 3.15}

def total_sigma(xmlpath):
    txt = open(xmlpath).read()
    E = np.array(re.findall(r"<E>\s*([0-9.eE+-]+)\s*</E>", txt), float)
    xs = np.array(re.findall(r"<xsec>\s*([0-9.eE+-]+)\s*</xsec>", txt), float)
    n = len(E) // 2                      # two sub-splines share the same E grid
    return E[:n], xs[:n] + xs[n:2*n]     # total = e-p(bound) + e-n(bound)

def find_xml(cfg, cut):
    hits = glob.glob(f"{STAGE}/*GEM26_{cfg}_{cut}_000*.xml")
    return hits[0] if hits else None

apply_style()
fig, axes = new_panels(ncols=1)
fig.set_size_inches(10, 5.5)
ax = axes[0]
for i, (cut, lim) in enumerate(CUTS.items()):
    c = COLORS[i % len(COLORS)]
    for cfg, ls, lab in [("22a", "-", None), ("11a", "--", None)]:
        f = find_xml(cfg, cut)
        if not f:
            continue
        E, sig = total_sigma(f)
        ax.plot(E, sig, ls=ls, color=c, lw=1.8,
                label=(f"t{cut}: Q² > {lim} GeV²" if cfg == "22a" else None))
style_axis(ax, title=None,
           xlabel="E$_e$  [GeV]", ylabel="σ(QEL-EM)  [10⁻³⁸ cm²]",
           logx=True, logy=True, ymin=1e-6)
ax.legend(title="EM-MinQ2Limit cut", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
ax.text(0.97, 0.05, "solid = SF (GEM26_22a)\ndashed = LFG (GEM26_11a)\nidentical — spline is\nground-state independent",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=FS_LEGEND, color="0.35")
fig.suptitle("EM-QES spline vs Q²-cut  (e⁻ on C12, GEM26 Rosenbluth)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/spline_gem26_q2cut.png"
fig.savefig(out, dpi=130)
print("wrote", out)

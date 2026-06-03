"""EM-QES total cross-section spline vs energy for the GEM26 Rosenbluth Q2-cut tunes (C12).

Reads the grid gmkspl spline XMLs (one per config x cut) staged locally, sums the two
bound-nucleon sub-splines into the total C12 QEL-EM sigma(E), and overlays the five
EM-MinQ2Limit cuts (t04..t08). The spline is ground-state independent, so SF (GEM26_22a)
and LFG (GEM26_11a) coincide; we draw SF solid and LFG dashed to show the overlap.
Emits a log-log view and a linear (normal-axes) view. Personal plot style.
"""
import sys, glob, re
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
    n = len(E) // 2
    return E[:n], xs[:n] + xs[n:2*n]

def find_xml(cfg, cut):
    hits = glob.glob(f"{STAGE}/*GEM26_{cfg}_{cut}_000*.xml")
    return hits[0] if hits else None

CURVES = []                               # (color_idx, cut, lim, cfg, ls, E, sig)
for i, (cut, lim) in enumerate(CUTS.items()):
    for cfg, ls in [("22a", "-"), ("11a", "--")]:
        f = find_xml(cfg, cut)
        if f:
            E, sig = total_sigma(f)
            CURVES.append((i, cut, lim, cfg, ls, E, sig))

def make_fig(out, logx, logy, ymin):
    apply_style()
    fig, axes = new_panels(ncols=1)
    fig.set_size_inches(10, 5.5)
    ax = axes[0]
    for i, cut, lim, cfg, ls, E, sig in CURVES:
        ax.plot(E, sig, ls=ls, color=COLORS[i % len(COLORS)], lw=1.8,
                label=(f"t{cut}: Q² > {lim} GeV²" if cfg == "22a" else None))
    style_axis(ax, title=None, xlabel="E$_e$  [GeV]", ylabel="σ(QEL-EM)  [10⁻³⁸ cm²]",
               logx=logx, logy=logy, ymin=ymin)
    ax.legend(title="EM-MinQ2Limit cut", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    ax.text(0.97, 0.05, "solid = SF (GEM26_22a)\ndashed = LFG (GEM26_11a)\nidentical — spline is\nground-state independent",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=FS_LEGEND, color="0.35")
    fig.suptitle("EM-QES spline vs Q²-cut  (e⁻ on C12, GEM26 Rosenbluth)", fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)

make_fig("results/spline_gem26_q2cut.png", logx=True, logy=True, ymin=1e-6)
make_fig("results/spline_gem26_q2cut_linear.png", logx=False, logy=False, ymin=None)

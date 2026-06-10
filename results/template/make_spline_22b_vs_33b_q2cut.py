"""EM-QES total cross-section spline vs energy: GEM26_22b vs GEM26_33b (C12).

Both tunes use the SF-consistent genie::UnifiedQELPXSec/Dipole QEL-EM model and differ
only in the C12 ground state: 22b = Benhar SF (pke12_tot.data), 33b = 2024
Ankowski-Benhar-Sakuda SF (pke12_2024.table). Unlike the Rosenbluth tunes, the SF enters
this cross section, so the splines may genuinely differ. One curve per EM-MinQ2Limit cut
(t04..t08); the same cut keeps the same color in both families, 22b solid, 33b dashed.

Reads the grid gmkspl spline XMLs staged under genie-agent/splines/<tune>/ (pulled from
PNFS; regenerable), sums the two bound-nucleon sub-splines into the total C12 QEL-EM
sigma(E). Emits a log-log view and a linear view. Personal plot style.
"""
import sys, glob, re
sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

STAGE = "genie-agent/splines"
CUTS = {"04": 0.54, "05": 1.18, "06": 1.70, "07": 1.73, "08": 3.15}

def total_sigma(xmlpath):
    txt = open(xmlpath).read()
    E = np.array(re.findall(r"<E>\s*([0-9.eE+-]+)\s*</E>", txt), float)
    xs = np.array(re.findall(r"<xsec>\s*([0-9.eE+-]+)\s*</xsec>", txt), float)
    n = len(E) // 2
    assert np.allclose(E[:n], E[n:2*n]), f"sub-spline E grids differ in {xmlpath}"
    return E[:n], xs[:n] + xs[n:2*n]

def find_xml(cfg, cut):
    hits = glob.glob(f"{STAGE}/GEM26_{cfg}_{cut}_000/*.xml")
    return hits[0] if hits else None

CURVES = []                               # (color_idx, cut, lim, cfg, ls, E, sig)
for i, (cut, lim) in enumerate(CUTS.items()):
    for cfg, ls in [("22b", "-"), ("33b", "--")]:
        f = find_xml(cfg, cut)
        if f:
            E, sig = total_sigma(f)
            CURVES.append((i, cut, lim, cfg, ls, E, sig))
        else:
            print(f"WARNING: no spline XML for GEM26_{cfg}_{cut}_000")

def make_fig(out, logx, logy, ymin):
    apply_style()
    fig, axes = new_panels(ncols=1)
    fig.set_size_inches(10, 5.5)
    ax = axes[0]
    for i, cut, lim, cfg, ls, E, sig in CURVES:
        ax.plot(E, sig, ls=ls, color=COLORS[i % len(COLORS)], lw=1.8,
                label=(f"t{cut}: Q² > {lim} GeV²" if cfg == "22b" else None))
    style_axis(ax, title=None, xlabel="E$_e$  [GeV]", ylabel="σ(QEL-EM)  [10⁻³⁸ cm²]",
               logx=logx, logy=logy, ymin=ymin)
    ax.legend(title="EM-MinQ2Limit cut", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    ax.text(0.97, 0.05, "solid = Benhar SF (GEM26_22b)\ndashed = ABS 2024 SF (GEM26_33b)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=FS_LEGEND, color="0.35")
    fig.suptitle("EM-QES spline vs Q²-cut  (e⁻ on C12, GEM26 UnifiedQEL-SF)", fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)

make_fig("results/spline_22b_vs_33b_q2cut.png", logx=True, logy=True, ymin=1e-6)
make_fig("results/spline_22b_vs_33b_q2cut_linear.png", logx=False, logy=False, ymin=None)

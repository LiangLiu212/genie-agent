"""EM-QES Q^2 distribution, SF vs LFG, across the 6 E91-013 energy points (C12, grid).

Reads one gst (100k-event process) per (config, energy point) from the staged grid outputs.
6 panels (one per beam-energy / Q2-cut setting); each overlays LFG (GEM26_11a) and SF
(GEM26_22a). Emits a log-log view and a linear (normal-axes) view. Personal plot style.
"""
import sys
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

STAGE = "/tmp/claude-12900/gem26"
CUTLIM = {"04": 0.54, "05": 1.18, "06": 1.70, "07": 1.73, "08": 3.15}
POINTS = [("04", "2.445"), ("04", "0.845"), ("05", "2.445"),
          ("06", "3.245"), ("07", "1.645"), ("08", "3.245")]

MAP = {}
for ln in open("/tmp/gst_map.txt"):
    cfg, cut, E, b = ln.split()
    MAP[(cfg, cut, E)] = b

def q2(cfg, cut, E):
    b = MAP.get((cfg, cut, E))
    return uproot.open(f"{STAGE}/{b}")["gst"]["Q2"].array(library="np") if b else None

LOGBINS = np.logspace(np.log10(0.4), np.log10(7.0), 45)

def make_fig(out, log):
    apply_style()
    fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
    for ax, (cut, E) in zip(axes, POINTS):
        dL, dS = q2("11a", cut, E), q2("22a", cut, E)
        if log:
            bins = LOGBINS
        else:
            both = np.concatenate([x for x in (dL, dS) if x is not None])
            hi = np.percentile(both, 99.7) if both.size else 7.0
            bins = np.linspace(CUTLIM[cut] * 0.9, hi, 45)
        for d, col, lab in [(dL, "C0", "LFG"), (dS, "C1", "SF")]:
            if d is not None:
                ax.hist(d, bins=bins, histtype="step", linewidth=1.7, color=col, label=lab)
        style_axis(ax, title=f"E={E} GeV · t{cut}  (Q²>{CUTLIM[cut]})",
                   xlabel="Q²  [(GeV/c)²]", logx=log, logy=log, ymin=(0.5 if log else None))
    for i in (0, 3):
        axes[i].set_ylabel("events / bin", fontsize=FS_LABEL)
    axes[0].legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    fig.suptitle("EM-QES Q² distribution: SF vs LFG  (e⁻ on C12, 100k ev/point, GEM26 Rosenbluth)\n"
                 "JLab E91-013 kinematics — one panel per beam-energy / Q²-cut setting",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)

make_fig("results/q2_gem26_sf_lfg.png", log=True)
make_fig("results/q2_gem26_sf_lfg_linear.png", log=False)

"""Q^2 distribution for the 18 EM-QES gevgen grid jobs (paper nucl-ex/0303011 kinematics).

3 panels, one per target (C12, Fe56, Au197). Each panel overlays the per-setting
Q^2 histograms (each setting = beam energy + GEM21 Q2-cut tune). Reads the gst
ROOT trees with uproot. Follows the personal plot style (results/template/plot_style.py).
"""
import sys, glob, os
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

GSTDIR = "/tmp/claude-12900/gst"

# stem-substring -> (target, beamE GeV, Q2 point, tune)
SETTINGS = [
    ("eminus_C12_20260601-142130",  "C12",   2.445, 0.64, "04"),
    ("eminus_C12_20260601-142137",  "C12",   0.845, 0.64, "04"),
    ("eminus_C12_20260601-142144",  "C12",   2.445, 1.28, "05"),
    ("eminus_C12_20260601-142150",  "C12",   3.245, 1.80, "06"),
    ("eminus_C12_20260601-142156",  "C12",   1.645, 1.83, "07"),
    ("eminus_C12_20260601-142203",  "C12",   3.245, 3.25, "08"),
    ("eminus_Fe56_20260601-142133", "Fe56",  2.445, 0.64, "04"),
    ("eminus_Fe56_20260601-142139", "Fe56",  0.845, 0.64, "04"),
    ("eminus_Fe56_20260601-142146", "Fe56",  2.445, 1.28, "05"),
    ("eminus_Fe56_20260601-142152", "Fe56",  3.245, 1.80, "06"),
    ("eminus_Fe56_20260601-142158", "Fe56",  1.645, 1.83, "07"),
    ("eminus_Fe56_20260601-142205", "Fe56",  3.245, 3.25, "08"),
    ("eminus_Au197_20260601-142135","Au197", 2.445, 0.64, "04"),
    ("eminus_Au197_20260601-142142","Au197", 0.845, 0.64, "04"),
    ("eminus_Au197_20260601-142148","Au197", 2.445, 1.28, "05"),
    ("eminus_Au197_20260601-142154","Au197", 3.245, 1.80, "06"),
    ("eminus_Au197_20260601-142200","Au197", 1.645, 1.83, "07"),
    ("eminus_Au197_20260601-142207","Au197", 3.245, 3.25, "08"),
]

TARGETS = ["C12", "Fe56", "Au197"]
# series order = beam-energy / Q2 setting, shared color across panels
SERIES = [
    (2.445, 0.64, "04"),
    (0.845, 0.64, "04"),
    (2.445, 1.28, "05"),
    (3.245, 1.80, "06"),
    (1.645, 1.83, "07"),
    (3.245, 3.25, "08"),
]

def find_file(stem):
    hits = glob.glob(os.path.join(GSTDIR, f"*{stem}*.gst.root"))
    return hits[0] if hits else None

def load_q2(stem):
    f = find_file(stem)
    if not f:
        print(f"  MISSING {stem}")
        return None
    q2 = uproot.open(f)["gst"]["Q2"].array(library="np")
    return np.asarray(q2, dtype=float)

# common log-spaced Q^2 binning across all panels
BINS = np.logspace(np.log10(0.02), np.log10(6.0), 50)

apply_style()
fig, axes = new_panels(ncols=3)

for ax, tgt in zip(axes, TARGETS):
    for i, (E, q2pt, tune) in enumerate(SERIES):
        stem = next((s[0] for s in SETTINGS
                     if s[1] == tgt and s[2] == E and s[4] == tune), None)
        if stem is None:
            continue
        q2 = load_q2(stem)
        if q2 is None or len(q2) == 0:
            continue
        label = f"E={E} GeV, Q²≈{q2pt} (t{tune})"
        ax.hist(q2, bins=BINS, histtype="step", linewidth=1.5,
                color=COLORS[i % len(COLORS)], label=label)
    style_axis(ax, title=tgt, xlabel="Q²  [(GeV/c)²]",
               logx=True, logy=True, ymin=0.5)

axes[0].set_ylabel("events / bin", fontsize=FS_LABEL)
axes[0].legend(title="beam setting", fontsize=FS_LEGEND,
               title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("EM-QES Q² distribution  (e⁻, 1000 evts, GEM21_11a Q²-cut tunes)\n"
             "JLab E91-013 kinematics  —  nucl-ex/0303011",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/q2_dist_emqes.png"
fig.savefig(out, dpi=130)
print("wrote", out)

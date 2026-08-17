import sys
import matplotlib
matplotlib.use("Agg")
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import apply_style, style_axis, COLORS, FS_LABEL, FS_LEGEND, FS_SUPTITLE, DPI
import matplotlib.pyplot as plt

import glob
# grid batch gevgen_grid-eminus_Ar40_20260714-175321-bd666d, 10k events/process
GST = sorted(glob.glob(
    "/exp/dune/data/users/liangliu/genie-dev/genie-agent/genie-runs/"
    "GEM26_44b_grid_pulled-2026-07-14/ar40_gst/*.gst.root"))
print(f"gst files: {len(GST)}")
DEUTERON = 1000010020

import awkward as ak
arr = uproot.concatenate([f + ":gst" for f in GST], ["pdgf", "pf"], library="ak")
pdgf, pf = arr["pdgf"], arr["pf"]
mask = pdgf == DEUTERON
p_deut = pf[mask]
has_d = ak.num(p_deut) > 0
leading = ak.to_numpy(ak.max(p_deut[has_d], axis=1))

n_ev = len(pdgf)
n_d_ev = int(ak.sum(has_d))
print(f"events: {n_ev}, events with >=1 deuteron: {n_d_ev} ({100*n_d_ev/n_ev:.1f}%)")
print(f"deuteron multiplicity total: {int(ak.sum(ak.num(p_deut)))}")
print(f"leading p: min {leading.min():.3f}, max {leading.max():.3f}, mean {leading.mean():.3f} GeV")

apply_style()
fig, ax = plt.subplots(1, 1, figsize=(6.5, 5.5))
ax.hist(leading, bins=40, color=COLORS[0], histtype="step", lw=1.5,
        label=f"{n_d_ev}/{n_ev} events with a deuteron")
style_axis(ax, title="2 GeV e$^-$ on Ar40, EM QEL, GEM26_44b",
           xlabel="leading deuteron p  [GeV]", logx=True, logy=True)
ax.set_xscale("linear")  # momentum spans <1 decade; log x not useful here
ax.set_yscale("linear")
ax.set_ylabel("events", fontsize=FS_LABEL)
ax.set_ylim(0, None)
ax.legend(fontsize=FS_LEGEND, loc="upper right")
fig.suptitle("Leading deuteron momentum (INCL++ GS+FSI)", fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/gem26_44b_ar40_leading_deuteron_p.png"
fig.savefig(out, dpi=DPI)
print("saved:", out)

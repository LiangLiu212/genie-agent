"""Missing energy & missing momentum at Q²=1.28 (e,e'p), SF vs LFG — vs Dutta et al. Figs 9/10.

Applies the shared spectrometer selection (selection.select, Table I row 5) to the full 10M-event
GEM26 grid samples at E_beam = 2.445 GeV, cut t05 (Q² ≈ 1.28): LFG (GEM26_11a_05) and
SF (GEM26_22a_05). Plots the reconstructed (post-FSI) missing energy E_m = ω − T_p and missing
momentum p_m = |q⃗ − p⃗_p|, in the paper windows (E_m ≤ 80 MeV, |p_m| < 300 MeV/c).
Personal plot style (results/template/plot_style.py).
"""
import sys, glob
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import selection as sel

SCRATCH = "/exp/dune/data/users/liangliu/prd_scratch/t05"

def collect(cfg):
    Em, Pm, ntot, nsel = [], [], 0, 0
    for f in sorted(glob.glob(f"{SCRATCH}/*GEM26_{cfg}_05_000*.gst.root")):
        ev = sel.load_events(f)
        m = sel.select(ev)
        ntot += len(m); nsel += int(m.sum())
        Em.append(ev["E_miss"][m]); Pm.append(ev["p_miss"][m])
    return np.concatenate(Em), np.concatenate(Pm), ntot, nsel

EmL, PmL, ntL, nsL = collect("11a")
EmS, PmS, ntS, nsS = collect("22a")
print(f"LFG: {nsL}/{ntL} selected;  SF: {nsS}/{ntS} selected")

EBINS = np.linspace(0.0, 80.0, 33)    # E_m  [MeV]   (paper window E_m <= 80)
PBINS = np.linspace(0.0, 300.0, 31)   # p_m  [MeV/c] (paper window |p_m| < 300)
apply_style()
fig, axes = new_panels(ncols=2, sharey=False)
fig.set_size_inches(11, 5.5)
axE, axP = axes
for Em, Pm, col, lab, ns in [(EmL, PmL, "C0", "LFG  (LocalFGM)", nsL),
                             (EmS, PmS, "C1", "SF  (SpectralFunc)", nsS)]:
    axE.hist(Em, bins=EBINS, histtype="step", linewidth=1.8, color=col, label=f"{lab}  (N={ns})")
    axP.hist(Pm, bins=PBINS, histtype="step", linewidth=1.8, color=col, label=f"{lab}  (N={ns})")
style_axis(axE, title="missing energy", xlabel=r"E$_m$ = ω − T$_p$  [MeV]",
           logx=False, logy=False, ymin=None)
style_axis(axP, title="missing momentum", xlabel=r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]",
           logx=False, logy=False, ymin=None)
for ax in (axE, axP):
    ax.set_ylabel("events / bin", fontsize=FS_LABEL)
axE.legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("(e,e'p) missing energy & momentum at Q²=1.28 — SF vs LFG\n"
             "e⁻ on C12, 2.445 GeV · Table I row 5 spectrometer cuts (Dutta et al., E91-013)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer/missing_e_p_q2_1.28.png"
fig.savefig(out, dpi=130)
print("wrote", out)

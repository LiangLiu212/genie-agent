"""Missing energy & missing momentum at Q²=1.28 (e,e'p), 5 QE-EM models — cf. Dutta Figs 9/10.

Reads the XRootD-streamed cache (build_cache.py) for the full ~10M-event C12 samples at
E_beam = 2.445 GeV, cut t05 (Q² ≈ 1.28): LFG and SF (Rosenbluth, GEM26_11a/22a_05), SuSAv2
(Hybrid-QEL, GEM21_11a_05), and UnifiedQEL with the old Benhar SF (GEM26_22b_05) vs the 2024
ABS SF (GEM26_33b_05). Applies the stage-2 (e,e'p) coincidence selection and plots the
reconstructed (post-FSI) missing energy E_m = ω − T_p and missing momentum p_m = |q⃗ − p⃗_p| in
the paper windows (E_m ≤ 80 MeV, |p_m| < 300 MeV/c).

Histograms are AREA-NORMALIZED: the five models have different total QE cross sections, so raw
counts are not a fair overlay — the selected event count N (a rate proxy) is shown in the legend.
Personal plot style (results/template/plot_style.py).
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import samples as S

EBINS = np.linspace(0.0, 80.0, 33)    # E_m  [MeV]   (paper window E_m <= 80)
PBINS = np.linspace(0.0, 300.0, 31)   # p_m  [MeV/c] (paper window |p_m| < 300)

data = {}
for m in S.MODELS:
    c = S.load_cache(m)
    s2 = c["stage2"].astype(bool)
    data[m] = (c["E_miss"][s2], c["p_miss"][s2], int(s2.sum()))
    print(f"{m}: stage-2 selected N={int(s2.sum())}")

apply_style()
fig, axes = new_panels(ncols=2, sharey=False)
fig.set_size_inches(11, 5.5)
axE, axP = axes
for m in S.MODELS:
    Em, Pm, n = data[m]
    axE.hist(Em, bins=EBINS, histtype="step", linewidth=S.lw(m, base=1.8), color=S.color(m),
             density=True, label=f"{S.label(m)}  (N={n})", zorder=S.zorder(m))
    axP.hist(Pm, bins=PBINS, histtype="step", linewidth=S.lw(m, base=1.8), color=S.color(m),
             density=True, label=f"{S.label(m)}  (N={n})", zorder=S.zorder(m))
style_axis(axE, title="missing energy", xlabel=r"E$_m$ = ω − T$_p$  [MeV]",
           logx=False, logy=False, ymin=None)
style_axis(axP, title="missing momentum", xlabel=r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]",
           logx=False, logy=False, ymin=None)
for ax in (axE, axP):
    ax.set_ylabel("normalized / bin", fontsize=FS_LABEL)
axE.legend(title="QE-EM model", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("(e,e'p) missing energy & momentum at Q²=1.28\n"
             "e⁻ on C12, 2.445 GeV · E91-013 Table I row 5 cuts · area-normalized",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer/missing_e_p_q2_1.28.png"
fig.savefig(out, dpi=130)
print("wrote", out)

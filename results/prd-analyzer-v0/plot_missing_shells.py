"""Missing momentum in E_m shell windows — p-shell vs s-shell, both stages, 5 QE-EM models.

Slices the (e,e'p) missing-energy spectrum into the two C12 proton shells and plots the
missing momentum p_m = |q⃗ − p⃗_p| of each slice, from the XRootD-streamed cache
(build_cache.py), C12 t05 (Q²=1.28, 2.445 GeV):

    p-shell : 10 < E_m < 25 MeV   (l=1 — expect a node at p_m ≈ 0, peak ~100 MeV/c)
    s-shell : 30 < E_m < 50 MeV   (l=0 — expect the peak at low p_m)

Rows = stage 1 (electron arm) / stage 2.1 (+ T_p, θ_p free) / stage 2 (full coincidence);
columns = p-shell / s-shell.
Area-normalized (the models differ in total σ and in shell-window content); the per-panel
selected count N is in each legend. A model with N < MIN_N in a window gets a legend entry
but no curve — a near-empty density histogram is all spikes (and LFG's fixed removal energy
~36 MeV leaves it essentially no p-shell strength at all). Personal plot style
(results/template/plot_style.py).
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import samples as S
import selection as sel

SHELLS = [("p-shell", 10.0, 25.0), ("s-shell", 30.0, 50.0)]
STAGES = [("stage 1", "1"), ("stage 2.1", "2.1"), ("stage 2", "2")]
PBINS = np.linspace(0.0, 300.0, 9)    # p_m  [MeV/c] (paper window |p_m| < 300), 8 bins
MIN_N = 50                            # below this, legend-only (density hist would be spikes)

cache = {m: S.load_cache(m) for m in S.MODELS}
stage_masks = {m: sel.cache_stage_masks(cache[m]) for m in S.MODELS}

apply_style()
fig, axes = new_panels(ncols=2, nrows=len(STAGES), sharey=False)
for r, (stage_lab, stage) in enumerate(STAGES):
    for ci, (shell_lab, lo, hi) in enumerate(SHELLS):
        ax = axes[r * 2 + ci]
        for m in S.MODELS:
            c = cache[m]
            msk = (c["E_miss"] > lo) & (c["E_miss"] < hi) & stage_masks[m][stage]
            pm = c["p_miss"][msk]
            if len(pm) >= MIN_N:
                ax.hist(pm, bins=PBINS, histtype="step", linewidth=S.lw(m), color=S.color(m),
                        density=True, label=f"{S.label(m)}  (N={len(pm)})", zorder=S.zorder(m))
            else:                      # keep the legend entry so the absence is explicit
                ax.plot([], [], color=S.color(m), lw=S.lw(m),
                        label=f"{S.label(m)}  (N={len(pm)}, not drawn)")
        style_axis(ax, title=f"{shell_lab} ({lo:g} < E$_m$ < {hi:g} MeV) · {stage_lab}",
                   xlabel=r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]", logx=False, logy=False, ymin=None)
        ax.set_ylabel("normalized / bin", fontsize=FS_LABEL)
        ax.legend(title="QE-EM model", fontsize=FS_LEGEND - 2,
                  title_fontsize=FS_LEGEND_TITLE - 2)
fig.set_size_inches(11, 5 * len(STAGES))
fig.suptitle("(e,e'p) missing momentum by shell\ne⁻ on C12, Q²=1.28 (t05) · area-normalized",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer-v0/missing_p_shells.png"
fig.savefig(out, dpi=130)
print("wrote", out)

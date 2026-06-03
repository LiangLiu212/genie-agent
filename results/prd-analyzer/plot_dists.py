"""Cut-stage diagnostics: 7 (e,e'p) variables after each selection stage, 3 QE-EM models.

Two figures from the XRootD-streamed cache (build_cache.py), C12 t05 (Q²=1.28, 2.445 GeV):
  stage 1 — electron arm only (El ∧ θ_e)            -> dists_stage1_electron.png
  stage 2 — full coincidence (El ∧ θ_e ∧ T_p ∧ θ_p) -> dists_stage2_full.png
Each shows El, θ_e, T_p, θ_p, Q², E_miss, p_miss for LFG, SF and SuSAv2 (area-normalized);
acceptance windows drawn as grey dashed lines. Personal plot style.
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import selection as sel
import samples as S

# panel -> (cache key, axis label, (lo, hi), nbins, cut-key-in-CUTS-or-None)
PANELS = [
    ("El",      r"E$_{e'}$  [GeV]",        (1.70, 1.75),  50, "El"),
    ("theta_e", r"$\theta_{e'}$  [deg]",   (30.5, 33.5),  50, "theta_e"),
    ("Tp",      r"T$_p$  [GeV]",           (0.50, 0.95),  50, "Tp"),
    ("theta_p", r"$\theta_p$  [deg]",      (32.0, 56.0),  50, "theta_p"),
    ("Q2",      r"Q$^2$  [(GeV/c)$^2$]",   (1.05, 1.55),  50, None),
    ("E_miss",  r"E$_m$  [MeV]",           (-20., 140.),  55, None),
    ("p_miss",  r"p$_m$  [MeV/c]",         (0., 400.),    50, None),
]

# cache: each model -> (dict of stage-1 arrays, stage-2 mask within stage-1)
data = {}
for m in S.MODELS:
    c = S.load_cache(m)
    data[m] = (c, c["stage2"].astype(bool))


def make_fig(out, use_stage2, stage_label):
    apply_style()
    fig, axes = new_panels(ncols=4, nrows=2, sharey=False)
    for ax, (key, lab, rng, nb, cutkey) in zip(axes, PANELS):
        bins = np.linspace(rng[0], rng[1], nb)
        for m in S.MODELS:
            c, s2 = data[m]
            x = c[key][s2] if use_stage2 else c[key]
            x = x[np.isfinite(x)]
            ax.hist(x, bins=bins, histtype="step", linewidth=1.6, color=S.color(m),
                    density=True, label=S.label(m))
        if cutkey:                                   # mark the acceptance window
            cc, hw = sel.CUTS[cutkey]
            for v in (cc - hw, cc + hw):
                ax.axvline(v, color="0.5", ls="--", lw=1.0)
        style_axis(ax, title=None, xlabel=lab, logx=False, logy=False, ymin=None)
        ax.set_ylabel("normalized / bin", fontsize=FS_LABEL)
    # use the empty 8th panel for the legend
    axes[7].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[7].legend(handles, labels, title="QE-EM model", loc="center",
                   fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    ns = {m: (int(data[m][1].sum()) if use_stage2 else len(data[m][0]["El"])) for m in S.MODELS}
    fig.suptitle(f"(e,e'p) distributions after {stage_label}  —  e⁻ on C12, Q²=1.28 (t05): LFG+Rosenbluth, SF+Rosenbluth, LFG+SuSAv2\n"
                 "grey dashed = acceptance window · selected N: "
                 + ",  ".join(f"{m} {ns[m]}" for m in S.MODELS),
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)


make_fig("results/prd-analyzer/dists_stage1_electron.png", False,
         "stage 1 (electron cut: El ∧ θ_e)")
make_fig("results/prd-analyzer/dists_stage2_full.png", True,
         "stage 2 (full: El ∧ θ_e ∧ T_p ∧ θ_p)")

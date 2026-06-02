"""Cut-stage diagnostics: distributions of 7 variables after the (e,e'p) selection stages.

Two figures over the t05 (Q²=1.28, E=2.445 GeV) GEM26 samples, SF vs LFG:
  stage 1  — electron arm only (El ∧ θ_e)            -> dists_stage1_electron.png
  stage 2  — full coincidence (El ∧ θ_e ∧ T_p ∧ θ_p) -> dists_stage2_full.png
Each shows El, θ_e, T_p, θ_p, Q², E_miss, p_miss. Cut windows drawn as grey dashed lines.
Uses the shared selection util. Personal plot style.
"""
import sys, glob
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import selection as sel

SCRATCH = "/exp/dune/data/users/liangliu/prd_scratch/t05"
KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss"]
# panel -> (axis label, (lo, hi), nbins, cut-key-in-CUTS-or-None)
PANELS = [
    ("El",      r"E$_{e'}$  [GeV]",        (1.70, 1.75),  50, "El"),
    ("theta_e", r"$\theta_{e'}$  [deg]",   (30.5, 33.5),  50, "theta_e"),
    ("Tp",      r"T$_p$  [GeV]",           (0.50, 0.95),  50, "Tp"),
    ("theta_p", r"$\theta_p$  [deg]",      (32.0, 56.0),  50, "theta_p"),
    ("Q2",      r"Q$^2$  [(GeV/c)$^2$]",   (1.05, 1.55),  50, None),
    ("E_miss",  r"E$_m$  [MeV]",           (-20., 140.),  55, None),
    ("p_miss",  r"p$_m$  [MeV/c]",         (0., 400.),    50, None),
]

def collect(cfg):
    """Return (vars dict of stage-1 arrays, stage-2 bool mask within stage-1)."""
    store = {k: [] for k in KEYS}
    s2 = []
    for f in sorted(glob.glob(f"{SCRATCH}/*GEM26_{cfg}_05_000*.gst.root")):
        ev = sel.load_events(f)
        m1 = sel.select_electron(ev)
        m2 = sel.select(ev)
        for k in KEYS:
            store[k].append(ev[k][m1])
        s2.append(m2[m1])
    return {k: np.concatenate(v) for k, v in store.items()}, np.concatenate(s2)

dataL = collect("11a")
dataS = collect("22a")

def make_fig(out, use_stage2, stage_label):
    apply_style()
    fig, axes = new_panels(ncols=4, nrows=2, sharey=False)
    for ax, (key, lab, rng, nb, cutkey) in zip(axes, PANELS):
        bins = np.linspace(rng[0], rng[1], nb)
        for (vrs, s2), col, name in [(dataL, "C0", "LFG"), (dataS, "C1", "SF")]:
            x = vrs[key][s2] if use_stage2 else vrs[key]
            ax.hist(x, bins=bins, histtype="step", linewidth=1.6, color=col, label=name)
        if cutkey:                                   # mark the acceptance window
            c, hw = sel.CUTS[cutkey]
            for v in (c - hw, c + hw):
                ax.axvline(v, color="0.5", ls="--", lw=1.0)
        style_axis(ax, title=None, xlabel=lab, logx=False, logy=False, ymin=None)
        ax.set_ylabel("events / bin", fontsize=FS_LABEL)
    axes[7].axis("off")
    axes[0].legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    nL = int(dataL[1].sum()) if use_stage2 else len(dataL[0]["El"])
    nS = int(dataS[1].sum()) if use_stage2 else len(dataS[0]["El"])
    fig.suptitle(f"(e,e'p) distributions after {stage_label}  —  e⁻ on C12, Q²=1.28 (t05), SF vs LFG\n"
                 f"grey dashed = acceptance window · selected  LFG N={nL}, SF N={nS}",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)

make_fig("results/prd-analyzer/dists_stage1_electron.png", False,
         "stage 1 (electron cut: El ∧ θ_e)")
make_fig("results/prd-analyzer/dists_stage2_full.png", True,
         "stage 2 (full: El ∧ θ_e ∧ T_p ∧ θ_p)")

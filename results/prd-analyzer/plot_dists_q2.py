"""(e,e'p) distributions with ONLY the Q^2 window — no electron/proton cuts.

Reads cache/q2window/<model>.npz (build_cache_q2.py: |Q^2/1.28 - 1| <= 5 %,
nothing else) and overlays the 7 analysis variables — El, theta_e', T_p,
theta_p, Q^2, E_miss, p_miss — for the 5 QE-EM models, area-normalized.
This is the uncut counterpart of the plot_dists.py cut-stage figures: what the
models look like in the Q^2 = 1.28 slice before any spectrometer selection.

Proton-dependent panels (T_p, theta_p, E_miss, p_miss) implicitly drop the
~21 % of events with no final-state proton (leading-proton columns are NaN
there); El/theta_e/Q2 panels include all selected events. E_miss = omega - T_p
(heavy-recoil convention of selection.py, no T_rec). Personal plot style.
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)
import samples as S

Q2_CENTER, Q2_FRAC = 1.28, 0.05
Q2_LO, Q2_HI = Q2_CENTER * (1 - Q2_FRAC), Q2_CENTER * (1 + Q2_FRAC)
OUT = "results/prd-analyzer/dists_q2window.png"

# panel -> (cache key, axis label, (lo, hi), nbins)  — ranges cover ~p1-p99
PANELS = [
    ("El",      r"E$_{e'}$  [GeV]",       (1.0, 2.2),    60),
    ("theta_e", r"$\theta_{e'}$  [deg]",  (28.0, 40.0),  60),
    ("Tp",      r"T$_p$  [GeV]",          (0.0, 1.2),    60),
    ("theta_p", r"$\theta_p$  [deg]",     (0.0, 140.0),  56),
    ("Q2",      r"Q$^2$  [(GeV/c)$^2$]",  (1.20, 1.36),  56),
    ("E_miss",  r"E$_m$  [MeV]",          (-20., 200.),  55),
    ("p_miss",  r"p$_m$  [MeV/c]",        (0., 800.),    60),
]

cache = {m: S.load_cache(m, cache_dir=f"{S.CACHE_DIR}/q2window") for m in S.MODELS}

apply_style()
fig, axes = new_panels(ncols=4, nrows=2, sharey=False)
for ax, (key, lab, rng, nb) in zip(axes, PANELS):
    bins = np.linspace(rng[0], rng[1], nb)
    for m in S.MODELS:
        x = cache[m][key]
        x = x[np.isfinite(x)]
        ax.hist(x, bins=bins, histtype="step", linewidth=S.lw(m), color=S.color(m),
                density=True, label=S.label(m), zorder=S.zorder(m))
    if key == "Q2":                                  # the only applied cut
        for v in (Q2_LO, Q2_HI):
            ax.axvline(v, color="0.5", ls="--", lw=1.0)
    style_axis(ax, title=None, xlabel=lab, logx=False, logy=False, ymin=None)
    ax.set_ylabel("normalized / bin", fontsize=FS_LABEL)

axes[7].axis("off")
handles, labels = axes[0].get_legend_handles_labels()
axes[7].legend(handles, labels, title="QE-EM model", loc="center",
               fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
ns = {m: len(cache[m]["Q2"]) for m in S.MODELS}
fig.suptitle("(e,e'p) distributions, Q² = 1.28 ± 5 % only — no e′/p cuts  —  e⁻ on C12 (t05)\n"
             "grey dashed = the Q² window · selected N: "
             + ",  ".join(f"{m} {ns[m]}" for m in S.MODELS),
             fontsize=FS_SUPTITLE)
fig.tight_layout()
fig.savefig(OUT, dpi=130)
print("wrote", OUT)
for m in S.MODELS:
    c = cache[m]
    print(f"  {m:15s} N={ns[m]:7d} of ntot={int(c['ntot'][0])}  "
          f"has_p={100*np.mean(c['has_p']):.1f}%")

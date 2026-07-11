"""Four-stage generator-workflow ladder of the missing MOMENTUM -- the p_m
companion of plot_em_ladder_fig9.py.

Same convention transposed: occupancy scale y = Z*hist(p_m; 0 <= E_m < 80)
/(N_p*20 MeV), proton channel, no cuts. Stage 1 is the input-table k-marginal
n_{E<80}(k) = Z*int_{E<80} 4pi k^2 P dE, overlaid dashed in the event-record
panels as the undistorted reference.

No external data here by design: the digitized Dutta Fig. 6 momentum
distributions use a shell-window, Q^2-1.8-anchored normalization that is
still unresolved (papers/nucl-ex_0303011/open_questions.md) -- overlaying
them now would put an arbitrary scale next to meaningful ones. Deferred.

The strict 0 <= E_m < 80 window means SuSAv2 has NO stage-2 curve (its
on-shell record nucleon has E2 < 0 for every event -- see the E_m ladder);
its n(k) still shows at stages 3/4 through the reconstruction.

Reads cache/ladder/<model>.npz (build_cache_ladder.py).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, EM_MAX, PM_MAX

OUT = "results/prd-analyzer-v0/pm_ladder.png"
P_EDGES = np.arange(0.0, 620.0, 20.0)
P_BINW = 20.0

# ---- stage 1: input-table k-marginals (E<80) --------------------------------------
tabs = F.load_input_tables()
y_in = {}
for key, (k, E, P, dk, dE) in tabs.items():
    nk = F.n_restricted(k, E, P, dE, emax=EM_MAX)          # (MeV/c)^-1, x Z
    y_in[key] = F.rebin(k, nk, dk, P_EDGES)                # bin-average onto P_EDGES

caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}


def stage_hist(c, s):
    nh = float(c["n_hitp"][0])
    Es = c[f"E{s}"]
    win = (Es >= 0.0) & (Es < EM_MAX)
    cnt, _ = np.histogram(c[f"p{s}"][win], bins=P_EDGES)
    return Z * cnt / (nh * P_BINW)


# ---- bookkeeping printout ---------------------------------------------------------
print("p_m ladder occupancy bookkeeping (integrals over p_m<600, 0<=E_m<80; x Z/N_p):")
for m in S.MODELS:
    c = caches[m]
    I = {s: stage_hist(c, s).sum() * P_BINW for s in (2, 3, 4)}
    w2 = (c["E2"] >= 0) & (c["E2"] < EM_MAX)
    p50 = np.percentile(c["p2"][w2], 50) if w2.any() else float("nan")
    print(f"  {m:15s} I2 = {I[2]:6.3f}  I3 = {I[3]:6.3f}  I4 = {I[4]:6.3f}"
          f"   p2 median = {p50:6.1f} MeV/c")
for key, lab in (("old", "Benhar"), ("new", "2024")):
    print(f"  {'input ' + lab:15s} I  = {(y_in[key] * P_BINW).sum():6.3f}  (E<80)")

# ---- figure -----------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=2, nrows=2, sharey=False)

TITLES = [r"1 — input tables  $\tilde n_{E<80}(k)$",
          "2 — struck nucleon (record)",
          "3 — pre-FSI primary proton",
          "4 — post-FSI leading proton"]

# panel 1: inputs only
ax = axes[0]
ax.stairs(y_in["old"], P_EDGES, color=S.color("SF"), linewidth=2.0, zorder=4,
          label="Benhar SF (22a/22b input)")
ax.stairs(y_in["new"], P_EDGES, color=S.color("UnifiedQEL2024"), linewidth=2.0,
          zorder=5, label="SF 2024 (33b input)")
ax.legend(fontsize=FS_LEGEND - 3, title="LFG / SuSAv2: no input table",
          title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")
ax.annotate("fig9 window\n$p_m<300$", xy=(0.53, 0.30), xycoords="axes fraction",
            fontsize=FS_LEGEND - 4, color="0.5", ha="left")

# panels 2-4: model curves, inputs dashed as reference
ymax = max(max(y_in[k].max() for k in y_in),
           max(stage_hist(caches[m], s).max() for m in S.MODELS for s in (2, 3, 4)))
for i, s in zip((1, 2, 3), (2, 3, 4)):
    ax = axes[i]
    for key in ("old", "new"):
        ax.stairs(y_in[key], P_EDGES, linewidth=1.0, linestyle="--", zorder=2,
                  color=S.color("SF" if key == "old" else "UnifiedQEL2024"))
    for m in S.MODELS:
        ax.stairs(stage_hist(caches[m], s), P_EDGES, color=S.color(m),
                  linewidth=S.lw(m, base=1.6), zorder=S.zorder(m),
                  label=S.label(m) if i == 3 else None)
axes[1].annotate("SuSAv2: $E_2<0$ for all events\n(on-shell record nucleon)"
                 "\n$\\rightarrow$ no entries in the $E_m$ window",
                 xy=(0.42, 0.60), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color=S.color("SuSAv2"))
axes[3].legend(fontsize=FS_LEGEND - 3, title="generator (Q$^2\\geq$1.18 sample)",
               title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

for i, ax in enumerate(axes):
    style_axis(ax, title=TITLES[i], xlabel=r"$p_m$  (MeV/$c$)" if i >= 2 else None,
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 600)
    ax.set_ylim(0, 1.15 * ymax)
    ax.axvline(PM_MAX, color="0.75", linestyle=":", linewidth=1.0, zorder=1)
    if i % 2 == 0:
        ax.set_ylabel(r"$Z\cdot$ d$N/$d$p_m\,/\,N_p$   ((MeV/$c$)$^{-1}$)",
                      fontsize=FS_LABEL)

fig.suptitle("generator-workflow ladder: missing momentum — occupancy scale\n"
             r"input table $\rightarrow$ record $\rightarrow$ pre-FSI $\rightarrow$ post-FSI;"
             "  proton channel, no cuts, $0\\leq E_m<80$ MeV",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

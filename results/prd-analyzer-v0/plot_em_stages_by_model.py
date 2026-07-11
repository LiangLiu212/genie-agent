"""Per-model view of the generator-workflow ladder: one panel per model, the
three event-record stages overlaid (record / pre-FSI / post-FSI), plus the
model's own input table where it has one and the Dutta Fig. 9 data.

Same convention as plot_em_ladder_fig9.py (occupancy scale, proton channel,
p_m < 300, no cuts): this is the "what does THIS implementation do to the
spectral function" view. Stages 2 and 3 coincide exactly for the a- and
b-chains (the dotted stage-2 curve hides under the dashed stage-3 one);
SuSAv2 is the exception -- its on-shell record nucleon has E2 < 0, off
scale (annotated), while its stage 3 is the chain's own energy balance.

Reads cache/ladder/<model>.npz (build_cache_ladder.py).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from matplotlib.lines import Line2D
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, EDGES, BINW, PM_MAX

OUT = "results/prd-analyzer-v0/em_stages_by_model.png"

STAGE_STYLE = {2: dict(linestyle=":", linewidth=1.6),
               3: dict(linestyle="--", linewidth=1.6),
               4: dict(linestyle="-", linewidth=2.2)}

# which input table backs which model (None = no table analogue)
INPUT_OF = {"LFG": None, "SF": "old", "SuSAv2": None,
            "UnifiedQEL2024": "new", "UnifiedQEL": "old"}

# ---- inputs + data ---------------------------------------------------------------
tabs = F.load_input_tables()
y_in = {}
for key, (k, E, P, dk, dE) in tabs.items():
    y_in[key] = F.rebin(E, F.f_restricted(k, P, dk), dE, EDGES)
dem, dsf, dstat, dtot = F.load_dutta()

caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}


def stage_hist(c, s):
    nh = float(c["n_hitp"][0])
    win = c[f"p{s}"] < PM_MAX
    cnt, _ = np.histogram(c[f"E{s}"][win], bins=EDGES)
    return Z * cnt / (nh * BINW)


# ---- figure ----------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=3, nrows=2, sharey=False)

for i, m in enumerate(S.MODELS):
    ax = axes[i]
    c = caches[m]
    tab = INPUT_OF[m]
    if tab is not None:
        ax.stairs(y_in[tab], EDGES, color="0.45", linewidth=1.2, linestyle="-.",
                  zorder=2)
    for s in (2, 3, 4):
        ax.stairs(stage_hist(c, s), EDGES, color=S.color(m), zorder=3 + s,
                  **STAGE_STYLE[s])
    ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=2.5,
                alpha=0.8, zorder=8)
    ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=3.5, color="black", capsize=2,
                zorder=9)
    if m == "SuSAv2":
        ax.annotate("record (2): on-shell,\n$E_2<0$ off scale",
                    xy=(0.52, 0.72), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 3, color=S.color(m))
    style_axis(ax, title=S.label(m), xlabel=r"$E_m$  (MeV)" if i >= 2 else None,
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 1.3)
    if i % 3 == 0:
        ax.set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)",
                      fontsize=FS_LABEL)

# legend panel
ax = axes[5]
ax.axis("off")
handles = [Line2D([], [], color="0.3", **STAGE_STYLE[2], label="2  struck nucleon (record)"),
           Line2D([], [], color="0.3", **STAGE_STYLE[3], label="3  pre-FSI proton (= 2 for a/b chains)"),
           Line2D([], [], color="0.3", **STAGE_STYLE[4], label="4  post-FSI leading proton"),
           Line2D([], [], color="0.45", linestyle="-.", linewidth=1.2,
                  label="input table (where one exists)"),
           Line2D([], [], color="black", marker="s", markersize=4, linestyle="none",
                  label="Dutta Fig. 9 (occupancy-norm.)")]
ax.legend(handles=handles, loc="center", fontsize=FS_LEGEND - 1,
          title="stages (model color per panel)", title_fontsize=FS_LEGEND_TITLE - 1,
          frameon=False)

fig.suptitle("workflow impact per implementation — $E_m$ at each generator stage vs Dutta Fig. 9\n"
             r"occupancy scale, proton channel, no cuts, $p_m<300$ MeV/$c$;"
             "  stages 2 and 3 coincide exactly except for SuSAv2",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

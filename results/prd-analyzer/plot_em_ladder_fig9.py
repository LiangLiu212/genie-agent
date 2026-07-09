"""Four-stage generator-workflow ladder of the missing energy vs Dutta Fig. 9.

One panel per stage, every panel in the identical fig9 convention (occupancy
scale y = Z*hist(E_m; p_m<300)/(N_p*5 MeV), no cuts, proton channel):

  1  input SF tables            f_{k<300}(E) x Z          (no GENIE at all)
  2  struck nucleon (record)    E2 = M_p - En - T_rec     (cache/ladder)
  3  pre-FSI primary proton     E3 = w - T_p - T_rec      (== prefsi cache)
  4  post-FSI leading proton    E4, same reconstruction   (hA2018 transport)

Stage 2 == 3 event-by-event for the a- and b-chains (verified < 3e-12 MeV:
the old a-tune chain writes the SAME on-shell-remnant closure into the record
that it gives the outgoing proton -- the sampled f(E) never reaches the
record; the b-tune chain conserves energy at the vertex exactly). SuSAv2 is
the exception: its record nucleon is exactly on-shell (En = sqrt(M_p^2+pn^2),
residual < 1e-5 MeV), so E2 = -(T_N + T_rec) < 0 -- off the fig9 axis
(annotated in panel 2) -- while its outgoing proton carries the chain's own
energy balance (median E3 - E2 = 29 MeV).

Reads cache/ladder/<model>.npz (build_cache_ladder.py). The data overlay is
FSI-distorted in shape and occupancy-rescaled -- directly comparable to stage
4 in shape, to nothing in absolute scale except via the 1.11 correlation
factor (see README section 10).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, EDGES, BINW, PM_MAX

OUT = "results/prd-analyzer/em_ladder_fig9.png"

# ---- stage 1: input tables -------------------------------------------------------
tabs = F.load_input_tables()
k_o, E_o, P_o, dk_o, dE_o = tabs["old"]
k_n, E_n, P_n, dk_n, dE_n = tabs["new"]
y_in_old = F.rebin(E_o, F.f_restricted(k_o, P_o, dk_o), dE_o, EDGES)
y_in_new = F.rebin(E_n, F.f_restricted(k_n, P_n, dk_n), dE_n, EDGES)

# ---- data ------------------------------------------------------------------------
dem, dsf, dstat, dtot = F.load_dutta()

# ---- event-record stages ---------------------------------------------------------
caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}


def stage_hist(c, s):
    nh = float(c["n_hitp"][0])
    win = c[f"p{s}"] < PM_MAX
    cnt, _ = np.histogram(c[f"E{s}"][win], bins=EDGES)
    return Z * cnt / (nh * BINW)


# ---- bookkeeping printout --------------------------------------------------------
print("ladder occupancy bookkeeping (integrals over E_m<80, p_m<300; x Z/N_p):")
print(f"  {'model':15s} {'I2':>6s} {'I3':>6s} {'I4':>6s} {'I4/I3':>6s} "
      f"{'surv%':>7s} {'med|E2-E3|':>11s} {'f(E3<0)%':>9s} {'f(E4<0)%':>9s}")
for m in S.MODELS:
    c = caches[m]
    nh = float(c["n_hitp"][0])
    I = {s: stage_hist(c, s).sum() * BINW for s in (2, 3, 4)}
    d23 = float(np.nanmedian(np.abs(c["E2"] - c["E3"])))
    surv = 100.0 * float(np.isfinite(c["E4"]).mean())
    neg3 = 100.0 * float(np.mean(c["E3"][c["p3"] < PM_MAX] < 0))
    e4 = c["E4"][(c["p4"] < PM_MAX) & np.isfinite(c["E4"])]
    neg4 = 100.0 * float(np.mean(e4 < 0))
    print(f"  {m:15s} {I[2]:6.3f} {I[3]:6.3f} {I[4]:6.3f} {I[4]/I[3]:6.3f} "
          f"{surv:7.2f} {d23:11.3f} {neg3:9.2f} {neg4:9.2f}")
print(f"  {'inputs':15s} old {y_in_old.sum()*BINW:.3f} / 2024 {y_in_new.sum()*BINW:.3f}"
      f"  (k<300, E_m<80);  data 6.08 (occupancy scale)")

# ---- figure ----------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=2, nrows=2, sharey=False)

TITLES = ["1 — input tables  $f_{k<300}(E)$",
          "2 — struck nucleon (record)",
          "3 — pre-FSI primary proton",
          "4 — post-FSI leading proton"]


def draw_data(ax, with_label=False):
    ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                alpha=0.8, zorder=8)
    ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                zorder=9, label="Dutta Fig. 9 (occupancy-norm.)" if with_label else None)


# panel 1: inputs only
ax = axes[0]
ax.stairs(y_in_old, EDGES, color=S.color("SF"), linewidth=2.0, zorder=4,
          label="Benhar SF (22a/22b input)")
ax.stairs(y_in_new, EDGES, color=S.color("UnifiedQEL2024"), linewidth=2.0, zorder=5,
          label="SF 2024 (33b input)")
draw_data(ax, with_label=True)
ax.legend(fontsize=FS_LEGEND - 3, title="LFG / SuSAv2: no input table",
          title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

# panels 2-4: model curves
for i, s in zip((1, 2, 3), (2, 3, 4)):
    ax = axes[i]
    for m in S.MODELS:
        ax.stairs(stage_hist(caches[m], s), EDGES, color=S.color(m),
                  linewidth=S.lw(m, base=1.6), zorder=S.zorder(m),
                  label=S.label(m) if i == 3 else None)
    draw_data(ax)
axes[1].annotate("SuSAv2: record nucleon on-shell\n$E_2<0$, off scale (median $-13$ MeV)",
                 xy=(0.35, 0.62), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color=S.color("SuSAv2"))
axes[1].annotate("LFG & SF: $\\delta$ at $S_p=16.0$ MeV\n(= their pre-FSI, panel 3)",
                 xy=(0.35, 0.44), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color="0.35")
axes[3].legend(fontsize=FS_LEGEND - 3, title="generator (Q$^2\\geq$1.18 sample)",
               title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

for i, ax in enumerate(axes):
    style_axis(ax, title=TITLES[i], xlabel=r"$E_m$  (MeV)" if i >= 2 else None,
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 1.3)
    if i % 2 == 0:
        ax.set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)",
                      fontsize=FS_LABEL)

fig.suptitle("generator-workflow ladder: missing energy vs Dutta Fig. 9 — occupancy scale\n"
             r"input table $\rightarrow$ record $\rightarrow$ pre-FSI $\rightarrow$ post-FSI;"
             "  proton channel, no cuts, $p_m<300$ MeV/$c$",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

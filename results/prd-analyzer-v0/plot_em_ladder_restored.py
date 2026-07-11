"""Four-stage ladder on the RESTORED (removal-energy) axis: E_m + T_rec.

Adding the recoil term back to each stage's missing energy,

  stage 2:  E2 + T_rec(p_n)  =  m_N - E_n        (the section-10b1 "restored")
  stage 3:  E3 + T_rec(p_m)  =  omega - T_p      (pre-FSI primary proton)
  stage 4:  E4 + T_rec(p_m)  =  omega - T_p      (post-FSI leading proton)

removes the recoil bookkeeping entirely and lands on the axis the input SF
tables are natively defined on (section 10b2: the tables' E is the mass-based,
recoil-free removal energy). On this axis the b-chain record must reproduce
the sampled table exactly (section 10b1) -- panels 2-4 overlay the two input
tables as thin dashed restoration targets. Stage 4 minus stage 3 is exactly
T_p(pre) - T_p(post), the section-10c FSI energy loss, with no recoil
mis-attribution possible.

Same events and windows as the section-10 ladder (p_s < 300 per stage; only
the E_m value changes); everything derives from cache/ladder, no rebuild.
Caveat for the data overlay: the published Dutta E_m is recoil-SUBTRACTED, so
on this axis the data sit low by an event-wise T_rec <= 4.4 MeV inside
p_m < 300 (sub-bin at the 5-MeV binning) -- shape reference only.
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, EDGES, BINW, PM_MAX
from acceptance import M_REC

OUT = "results/prd-analyzer-v0/em_ladder_restored.png"
M_MEV = M_REC * 1000.0               # 11B nuclear mass [MeV]

# ---- stage 1: input tables (native axis) ------------------------------------------
tabs = F.load_input_tables()
k_o, E_o, P_o, dk_o, dE_o = tabs["old"]
k_n, E_n, P_n, dk_n, dE_n = tabs["new"]
y_in_old = F.rebin(E_o, F.f_restricted(k_o, P_o, dk_o), dE_o, EDGES)
y_in_new = F.rebin(E_n, F.f_restricted(k_n, P_n, dk_n), dE_n, EDGES)

# ---- data (recoil-subtracted axis: shape reference only, see docstring) -----------
dem, dsf, dstat, dtot = F.load_dutta()

# ---- event-record stages, restored ------------------------------------------------
caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}
for c in caches.values():
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):          # E_s + p_s^2/(2 M_11B): stage 2 -> m_N - E_n,
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * M_MEV)  # 3/4 -> w - T_p


def occ_hist(c, E, p, nh):
    win = p < PM_MAX
    cnt, _ = np.histogram(E[win], bins=EDGES)
    return Z * cnt / (nh * BINW)


# ---- bookkeeping printout ----------------------------------------------------------
IB = 3                               # EDGES index of the [15,20) bin
print("restored ladder bookkeeping (E<80; windows p_s<300 unchanged; MeV):")
print(f"  {'model':15s} {'I2r':>6s} {'I3r':>6s} {'I4r':>6s} {'I4r/I3r':>8s} "
      f"{'f2<15%':>7s} {'f3<15%':>7s} {'med Trec2':>10s} {'[15,20) s2':>11s}")
for m in S.MODELS:
    c = caches[m]
    nh = float(c["n_hitp"][0])
    h2 = occ_hist(c, c["E2r"], c["p2"], nh)
    I = {2: h2.sum() * BINW,
         3: occ_hist(c, c["E3r"], c["p3"], nh).sum() * BINW,
         4: occ_hist(c, c["E4r"], c["p4"], nh).sum() * BINW}
    w2 = c["p2"] < PM_MAX
    f2 = 100.0 * float(np.mean(c["E2r"][w2] < 15.0))
    w3 = c["p3"] < PM_MAX
    f3 = 100.0 * float(np.mean(c["E3r"][w3] < 15.0))
    trec2 = float(np.median(c["p2"][w2] ** 2 / (2.0 * M_MEV)))
    print(f"  {m:15s} {I[2]:6.3f} {I[3]:6.3f} {I[4]:6.3f} {I[4]/I[3]:8.3f} "
          f"{f2:7.3f} {f3:7.3f} {trec2:10.2f} {h2[IB]:11.3f}")
print(f"  {'inputs':15s} old {y_in_old.sum()*BINW:.3f} / 2024 {y_in_new.sum()*BINW:.3f}"
      f"  (k<300, E<80);  [15,20) bin: old {y_in_old[IB]:.3f} / 2024 {y_in_new[IB]:.3f};"
      f"  data 6.08 (recoil-subtracted axis)")

# ---- figure ------------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=2, nrows=2, sharey=False)

TITLES = ["1 — input tables  $f_{k<300}(E)$",
          "2 — struck nucleon (record),  $m_N-E_n$",
          "3 — pre-FSI primary proton,  $\\omega-T_p$",
          "4 — post-FSI leading proton,  $\\omega-T_p$"]

def draw_data(ax, with_label=False):
    ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                alpha=0.8, zorder=8)
    ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                zorder=9, label="Dutta Fig. 9 (occupancy-norm.)" if with_label else None)


def draw_inputs(ax, dashed=True):
    ls, lw_, a = ("--", 1.0, 0.8) if dashed else ("-", 2.0, 1.0)
    ax.stairs(y_in_old, EDGES, color=S.color("SF"), linewidth=lw_, linestyle=ls,
              alpha=a, zorder=2)
    ax.stairs(y_in_new, EDGES, color=S.color("UnifiedQEL2024"), linewidth=lw_,
              linestyle=ls, alpha=a, zorder=3)


# panel 1: inputs only
ax = axes[0]
ax.stairs(y_in_old, EDGES, color=S.color("SF"), linewidth=2.0, zorder=4,
          label="Benhar SF (22a/22b input)")
ax.stairs(y_in_new, EDGES, color=S.color("UnifiedQEL2024"), linewidth=2.0, zorder=5,
          label="SF 2024 (33b input)")
draw_data(ax, with_label=True)
ax.legend(fontsize=FS_LEGEND - 3, title="table axis = restored axis",
          title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

# panels 2-4: restored model curves + input tables as dashed restoration targets
for i, s in zip((1, 2, 3), (2, 3, 4)):
    ax = axes[i]
    draw_inputs(ax)
    for m in S.MODELS:
        c = caches[m]
        ax.stairs(occ_hist(c, c[f"E{s}r"], c[f"p{s}"], float(c["n_hitp"][0])), EDGES,
                  color=S.color(m), linewidth=S.lw(m, base=1.6), zorder=S.zorder(m),
                  label=S.label(m) if i == 3 else None)
    draw_data(ax)
axes[1].annotate("SuSAv2: $m_N-E_n=-T_N<0$,\nstill off scale (median $-17$ MeV)",
                 xy=(0.35, 0.62), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color=S.color("SuSAv2"))
axes[1].annotate("b-tunes land ON the dashed tables\n(sec. 10b1 restoration); a-tune "
                 "$\\delta$ smears\nup by $T_{rec}(k)\\leq4.4$ MeV",
                 xy=(0.35, 0.40), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color="0.35")
axes[3].legend(fontsize=FS_LEGEND - 3,
               title="thin dashed: input tables\n(data axis: $-T_{rec}$, sub-bin)",
               title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

for i, ax in enumerate(axes):
    style_axis(ax, title=TITLES[i], xlabel=r"$E_m+T_{rec}$  (MeV)" if i >= 2 else None,
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 1.3)
    if i % 2 == 0:
        ax.set_ylabel(r"$Z\cdot$ d$N/$d$(E_m+T_{rec})\,/\,N_p$   (MeV$^{-1}$)",
                      fontsize=FS_LABEL)

fig.suptitle("generator-workflow ladder on the restored (removal-energy) axis — "
             r"$E_m+T_{rec}$"
             "\nrecord $m_N-E_n$, protons $\\omega-T_p$ — proton channel, no cuts, "
             "$p_m<300$ MeV/$c$",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

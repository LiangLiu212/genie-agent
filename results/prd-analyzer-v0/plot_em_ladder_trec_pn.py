"""Four-stage ladder with the missing energy defined via the VERTEX recoil:

    E_m = omega - T_p - T_rec,   T_rec = p_n^2 / (2 M(11B))

i.e. the recoil kinetic energy of the 11B remnant evaluated at the struck
nucleon's true momentum p_n (the remnant recoils with -p_n at the QEL vertex),
instead of the section-10 reconstruction convention T_rec = p_m^2/(2 M(11B))
with p_m = |q - p_p| re-measured from the outgoing proton at each stage.

For an energy-momentum-conserving 2-body vertex the definitions coincide at
stages 2 and 3 (p_m == p_n) and only stage 4 moves: after FSI the
reconstructed p_m no longer equals the vertex recoil, and the p_m-based T_rec
mis-attributes part of the proton's FSI energy loss to remnant recoil. The
a- and b-chains satisfy the identity to double precision; SuSAv2 does NOT --
its pre-FSI proton is not 2-body-consistent with the recorded struck nucleon
(|q - p_p| != p_n for ~97 % of events), so its stage 3 moves too. Panels 3-4
overlay both definitions (solid: T_rec(p_n); dashed: section-10 T_rec(p_m)).

Everything derives from cache/ladder/<model>.npz (build_cache_ladder.py) --
p2 stores p_n, so E_s' = E_s + (p_s^2 - p_n^2)/(2 M(11B)); no rebuild. The
E_m-panel window stays the section-10 reconstructed p_s < 300 MeV/c at every
stage (same events, only the E_m value redefined); the pn-window variant of
the stage-4 integral is printed for reference, not plotted.
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

OUT = "results/prd-analyzer-v0/em_ladder_trec_pn.png"
M_MEV = M_REC * 1000.0               # 11B nuclear mass [MeV]

# ---- stage 1: input tables -------------------------------------------------------
tabs = F.load_input_tables()
k_o, E_o, P_o, dk_o, dE_o = tabs["old"]
k_n, E_n, P_n, dk_n, dE_n = tabs["new"]
y_in_old = F.rebin(E_o, F.f_restricted(k_o, P_o, dk_o), dE_o, EDGES)
y_in_new = F.rebin(E_n, F.f_restricted(k_n, P_n, dk_n), dE_n, EDGES)

# ---- data ------------------------------------------------------------------------
dem, dsf, dstat, dtot = F.load_dutta()

# ---- event-record stages, both T_rec conventions ---------------------------------
caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}
for c in caches.values():
    with np.errstate(invalid="ignore"):
        for s in (3, 4):             # E_s' = E_s + (p_s^2 - p_n^2)/(2 M_11B)
            c[f"E{s}p"] = c[f"E{s}"] + (c[f"p{s}"] ** 2 - c["p2"] ** 2) / (2.0 * M_MEV)
    c["E2p"] = c["E2"]               # stage 2 already uses p_n


def occ_hist(c, E, p, nh):
    win = p < PM_MAX
    cnt, _ = np.histogram(E[win], bins=EDGES)
    return Z * cnt / (nh * BINW)


# ---- bookkeeping printout --------------------------------------------------------
print("vertex-recoil ladder bookkeeping (E_m<80; window p_s<300 unchanged; MeV):")
print(f"  {'model':15s} {'f3mov%':>7s} {'I3\'':>6s} {'I3(s10)':>7s} {'I4\'':>6s} "
      f"{'I4(s10)':>7s} {'I4\'/I3\'':>8s} {'f4mov%':>7s} {'med dE4|mov':>12s} "
      f"{'p90':>7s} {'I4\'(pn win)':>12s}")
for m in S.MODELS:
    c = caches[m]
    nh = float(c["n_hitp"][0])
    I3n = occ_hist(c, c["E3p"], c["p3"], nh).sum() * BINW
    I3o = occ_hist(c, c["E3"], c["p3"], nh).sum() * BINW
    I4n = occ_hist(c, c["E4p"], c["p4"], nh).sum() * BINW
    I4o = occ_hist(c, c["E4"], c["p4"], nh).sum() * BINW
    d3 = c["E3p"] - c["E3"]                        # nonzero only if p_m != p_n
    f3 = 100.0 * float((np.abs(d3) > 0.01).mean())
    d4 = c["E4p"] - c["E4"]
    fin = np.isfinite(d4)
    mov = fin & (np.abs(d4) > 0.01)
    fmov = 100.0 * mov.sum() / fin.sum()
    med = float(np.median(d4[mov])) if mov.any() else 0.0
    p90 = float(np.percentile(d4[mov], 90)) if mov.any() else 0.0
    winp = np.isfinite(c["E4p"]) & (c["p2"] < PM_MAX)
    I4pn = Z * np.histogram(c["E4p"][winp], bins=EDGES)[0].sum() / nh
    print(f"  {m:15s} {f3:7.2f} {I3n:6.3f} {I3o:7.3f} {I4n:6.3f} {I4o:7.3f} "
          f"{I4n/I3n:8.3f} {fmov:7.2f} {med:12.2f} {p90:7.2f} {I4pn:12.3f}")
print(f"  {'inputs':15s} old {y_in_old.sum()*BINW:.3f} / 2024 {y_in_new.sum()*BINW:.3f}"
      f"  (k<300, E_m<80);  data 6.08 (occupancy scale)")

# the vertex non-closure is a SuSAv2-only effect -- quantify it once
c = caches["SuSAv2"]
dp = c["p3"] - c["p2"]
d3 = c["E3p"] - c["E3"]
mov = np.abs(d3) > 0.01
print(f"  SuSAv2 vertex non-closure (|q-p_p| != p_n pre-FSI): "
      f"{100.0*mov.mean():.2f}% of events; dp = p_m - p_n med {np.median(dp[mov]):+.1f}, "
      f"p05/p95 {np.percentile(dp[mov],5):+.1f}/{np.percentile(dp[mov],95):+.1f} MeV/c; "
      f"|dE3|>1 MeV: {100.0*float((np.abs(d3)>1).mean()):.1f}%")

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

# panel 2: T_rec(p_n) is the section-10 definition already -- unchanged
ax = axes[1]
for m in S.MODELS:
    c = caches[m]
    ax.stairs(occ_hist(c, c["E2p"], c["p2"], float(c["n_hitp"][0])), EDGES,
              color=S.color(m), linewidth=S.lw(m, base=1.6), zorder=S.zorder(m))
draw_data(ax)
ax.annotate("SuSAv2: record nucleon on-shell\n$E_2<0$, off scale (median $-13$ MeV)",
            xy=(0.35, 0.62), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
            color=S.color("SuSAv2"))
ax.annotate("$T_{rec}(p_n)$ = the sec.-10 definition here:\npanel 2 unchanged",
            xy=(0.35, 0.44), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
            color="0.35")

# panels 3-4: solid = vertex-recoil definition, dashed = section-10 reconstruction
for i, s in zip((2, 3), (3, 4)):
    ax = axes[i]
    for m in S.MODELS:
        c = caches[m]
        nh = float(c["n_hitp"][0])
        ax.stairs(occ_hist(c, c[f"E{s}"], c[f"p{s}"], nh), EDGES, color=S.color(m),
                  linewidth=1.0, linestyle="--", alpha=0.7, zorder=S.zorder(m) - 3)
        ax.stairs(occ_hist(c, c[f"E{s}p"], c[f"p{s}"], nh), EDGES, color=S.color(m),
                  linewidth=S.lw(m, base=1.6), zorder=S.zorder(m),
                  label=S.label(m) if i == 3 else None)
    draw_data(ax)
axes[2].annotate("$p_m\\equiv p_n$ exactly for LFG/SF/UQEL\n"
                 "(dashed under solid); SuSAv2: vertex\nnon-closure, "
                 "$p_m\\neq p_n$ for 97% of events",
                 xy=(0.35, 0.50), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color="0.35")
axes[3].legend(fontsize=FS_LEGEND - 3,
               title="solid: $T_{rec}(p_n)$   dashed: $T_{rec}(p_m)$ (sec. 10)",
               title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

for i, ax in enumerate(axes):
    style_axis(ax, title=TITLES[i], xlabel=r"$E_m$  (MeV)" if i >= 2 else None,
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, 1.3)
    if i % 2 == 0:
        ax.set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)",
                      fontsize=FS_LABEL)

fig.suptitle("generator-workflow ladder, vertex-recoil missing energy — "
             r"$E_m=\omega-T_p-p_n^2/2M(^{11}\mathrm{B})$"
             "\nproton channel, no cuts, window $p_m<300$ MeV/$c$ as in section 10",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

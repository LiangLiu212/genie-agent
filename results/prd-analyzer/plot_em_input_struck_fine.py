"""Input tables vs the struck nucleon (record) in FINE E_m bins -- what the
5-MeV fig9 binning hides inside the first populated bin (the p-shell peak).

Same occupancy convention as the ladder (y = Z*hist(E_2; p_m<300)/(N_p*binw),
proton channel, no cuts), but with sub-MeV binning:

  left   5-35 MeV, 0.25-MeV bins -- the whole p-shell region;
  right  13.5-22 MeV, 0.1-MeV bins -- the 2024 table's fine segment
         (0.025-MeV grid, NIKHEF quasiparticle peaks).

What fine binning resolves (all invisible at 5 MeV):
  - LFG & SF (a-tunes): the entire ground-state energy information collapsed
    into a single ~keV-wide line at S_p = 15.957 MeV (the FermiMover
    on-shell-11B closure) -- height ~ Z/binw on this scale;
  - SF + UnifiedQEL (b-tune): the sampled Benhar f(E), which is natively
    5-MeV coarse -- the generator reproduces its flat-step structure;
  - SF(2024) + UnifiedQEL: whether TH2::GetRandom2 sampling preserves the
    2024 table's resolved quasiparticle peaks (it samples bin-uniformly, so
    the record should show them at table granularity x sigma weighting);
  - SuSAv2: nothing -- its on-shell record nucleon has E_2 < 0 (annotated).
The Dutta data (grey, 5-MeV steps) show the experimental resolution scale.

Reads cache/ladder/<model>.npz (build_cache_ladder.py).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, PM_MAX

OUT = "results/prd-analyzer/em_input_struck_fine.png"

PANELS = [dict(lo=5.0, hi=40.0, bw=0.25, title="p-shell region  (0.25-MeV bins)"),
          dict(lo=13.5, hi=22.0, bw=0.10, title="2024 fine segment  (0.1-MeV bins)")]

# ---- inputs + data ---------------------------------------------------------------
tabs = F.load_input_tables()
dem, dsf, dstat, dtot = F.load_dutta()

caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}


def input_native(key):
    """f_{k<300}(E) on the table's own (possibly non-uniform) grid -> (f, edges)."""
    k, E, P, dk, dE = tabs[key]
    f = F.f_restricted(k, P, dk)
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    edges = np.concatenate([[E[0] - dE[0] / 2.0], E - dE / 2.0 + dE])
    return f, edges


def struck_hist(m, edges, bw):
    c = caches[m]
    nh = float(c["n_hitp"][0])
    win = c["p2"] < PM_MAX
    cnt, _ = np.histogram(c["E2"][win], bins=edges)
    return Z * cnt / (nh * bw)


# ---- bookkeeping printout --------------------------------------------------------
print("struck-nucleon (stage 2) fine structure, p_m<300:")
for m in S.MODELS:
    c = caches[m]
    e2 = c["E2"][c["p2"] < PM_MAX]
    if m == "SuSAv2":
        print(f"  {m:15s} all E2 < 0 (on-shell record); median = {np.median(e2):.2f} MeV")
        continue
    edges = np.arange(10.0, 30.0, 0.1)
    h, _ = np.histogram(e2, bins=edges)
    pk = h.argmax()
    print(f"  {m:15s} peak bin [{edges[pk]:.2f},{edges[pk+1]:.2f}) MeV"
          f"   frac in [15,20) = {np.mean((e2 >= 15) & (e2 < 20)):.3f}"
          f"   frac within +-0.05 of 15.957 = {np.mean(np.abs(e2 - 15.957) < 0.05):.3f}")

# ---- figure ----------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=2, nrows=1, sharey=False)

f_old, e_old = input_native("old")
f_new, e_new = input_native("new")

for ax, spec in zip(axes, PANELS):
    edges = np.arange(spec["lo"], spec["hi"] + spec["bw"] / 2, spec["bw"])
    # data (5-MeV native) for the resolution contrast
    ax.stairs(dsf, F.EDGES, color="0.75", linewidth=1.4, zorder=1,
              label="Dutta Fig. 9 (5-MeV bins)")
    # input tables on their own native grids
    ax.stairs(f_old, e_old, color=S.color("SF"), linewidth=1.2, linestyle="--",
              zorder=3, label="Benhar input (native 5-MeV steps)")
    ax.stairs(f_new, e_new, color=S.color("UnifiedQEL2024"), linewidth=1.0,
              linestyle="--", zorder=4, label="2024 input (native 0.025/0.1 MeV)")
    # struck nucleon per model
    for m in S.MODELS:
        if m == "SuSAv2":
            continue
        ax.stairs(struck_hist(m, edges, spec["bw"]), edges, color=S.color(m),
                  linewidth=S.lw(m, base=1.5), zorder=S.zorder(m),
                  label=f"{S.label(m)} — struck")
    style_axis(ax, title=spec["title"], xlabel=r"$E_m$  (MeV)",
               logx=False, logy=True, ymin=None)
    ax.set_xlim(spec["lo"], spec["hi"])
    ax.set_ylim(5e-3, 150)
axes[0].set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)", fontsize=FS_LABEL)
axes[0].legend(fontsize=FS_LEGEND - 3, loc="upper right",
               title="stage 1 (input) vs stage 2 (record)",
               title_fontsize=FS_LEGEND_TITLE - 3)
axes[0].annotate("LFG & SF: one ~keV line\nat $S_p=15.957$ MeV\n(height $= Z\\,/\\,$binw)",
                 xy=(0.63, 0.34), xycoords="axes fraction",
                 fontsize=FS_LEGEND - 3, color="0.25")
axes[1].annotate("SuSAv2: $E_2<0$, off scale", xy=(0.03, 0.03),
                 xycoords="axes fraction", fontsize=FS_LEGEND - 3,
                 color=S.color("SuSAv2"))

fig.suptitle("input tables vs sampled struck nucleon — fine $E_m$ binning\n"
             r"occupancy scale, hitnuc$\,$=$\,$p, no cuts, $p_m<300$ MeV/$c$",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

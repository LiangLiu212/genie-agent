"""Missing energy at Q^2 = 1.28 through the HMS x SOS acceptance, overlaid on
Dutta et al. Fig. 9 (nucl-ex/0303011, C12 E_m spectral function).

GENIE side: the 5 QE-EM models, events selected by the spectrometer-acceptance
boxes of acceptance.py (arm-frame delta/yptar/xptar about the Q^2 = 1.28
central settings, from report/simc-eep-normalization.md Section 4.5), cache
built by build_cache_acceptance.py. E_m = omega - T_p - T_rec (paper
definition), histogrammed in the data's own 5-MeV bins over the paper window
(E_m < 80 MeV, p_m < 300 MeV/c).

Data side: data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat -- Em | S | Em/200
| stat error. Inner bars = the file's statistical errors; outer light bars =
total point-to-point uncertainty per papers/nucl-ex_0303011/open_questions.md
(stat (+) 2 % point-to-point syst (+) 5 % model dependence, with the two
p-shell bins overridden by the published pixel-measured bars 8.1 % / 4.7 %).

Normalization: the data are on the full-occupancy (IPSM) scale -- their
integral is Sum(S)*5 MeV = 6.08 ~ Z(C) = 6, NOT the raw absorbed yield (see
open_questions.md). Each GENIE histogram is therefore scaled to the same
integral over E_m in [0, 80) (shape + occupancy comparison; GENIE's absolute
rate is not used).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S

DATA = "data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat"
OUT = "results/prd-analyzer/em_dutta_fig9_q1p28.png"
BINW = 5.0                                   # data binning [MeV]
EDGES = np.arange(0.0, 80.0 + BINW, BINW)    # 16 bins, matches the .dat grid
PM_MAX = 300.0                               # paper integration window [MeV/c]

# --- Dutta Fig. 9 data + uncertainty model (open_questions.md prescription) ---
em, sf, _, stat = np.loadtxt(DATA, unpack=True)
tot = np.sqrt(stat**2 + (0.02 * sf) ** 2 + (0.05 * sf) ** 2)
tot[np.isclose(em, 17.5)] = 0.081 * sf[np.isclose(em, 17.5)]   # published bar (pixel-measured)
tot[np.isclose(em, 22.5)] = 0.047 * sf[np.isclose(em, 22.5)]   # published bar (pixel-measured)
I_DATA = sf.sum() * BINW                     # 6.08 ~ Z(C): occupancy-scale integral

apply_style()
fig, (ax,) = new_panels(ncols=1, sharey=False)
fig.set_size_inches(7.5, 6.5)

chi2_lines = []
offscale = []
for m in S.MODELS:
    c = S.load_cache(m, cache_dir=f"{S.CACHE_DIR}/acceptance")
    win = (c["E_miss"] >= EDGES[0]) & (c["E_miss"] < EDGES[-1]) & (c["p_miss"] < PM_MAX)
    n = int(win.sum())
    cnt, _ = np.histogram(c["E_miss"][win], bins=EDGES)
    yield_mc = cnt * (I_DATA / (n * BINW))               # occupancy-normalized [MeV^-1]
    err_mc = np.sqrt(cnt) * (I_DATA / (n * BINW))
    ax.stairs(yield_mc, EDGES, color=S.color(m), linewidth=S.lw(m, base=1.8),
              zorder=S.zorder(m), label=f"{S.label(m)}  (N={n})")
    if yield_mc.max() > 0.7:                             # clipped by the paper's y-range
        k = int(np.argmax(yield_mc))
        offscale.append((m, 0.5 * (EDGES[k] + EDGES[k + 1]), yield_mc.max()))
    nz = sf > 0
    chi2 = float(np.sum((yield_mc[nz] - sf[nz]) ** 2 / (tot[nz] ** 2 + err_mc[nz] ** 2)))
    chi2_lines.append(f"{m:15s} N={n:7d}  chi2/ndf = {chi2:7.1f}/{int(nz.sum())}")

ax.errorbar(em, sf, yerr=tot, fmt="none", ecolor="0.6", elinewidth=3, alpha=0.8,
            zorder=8, label="total p2p uncert. (open_questions)")
ax.errorbar(em, sf, yerr=stat, fmt="s", ms=5, color="black", capsize=2,
            zorder=9, label="Dutta Fig. 9 (stat errors)")

style_axis(ax, title=r"$^{12}$C(e,e'p),  $Q^2 = 1.28$ (GeV/$c$)$^2$",
           xlabel=r"$E_m$  (MeV)",
           logx=False, logy=False, ymin=None)
ax.set_ylabel(r"$\int S^{D}(E_m, p_m)\,d^3p_m$   (MeV$^{-1}$)", fontsize=FS_LABEL)
ax.set_xlim(0, 85)
ax.set_ylim(0, 0.7)
for m, x, peak in offscale:                       # e.g. LFG's delta-like removal energy
    ax.annotate(f"{S.label(m)} peak: {peak:.1f} MeV$^{{-1}}$ (off scale)",
                xy=(x + 1.5, 0.45), xytext=(x + 6, 0.33), color=S.color(m),
                fontsize=FS_LEGEND - 1,
                arrowprops=dict(arrowstyle="->", color=S.color(m)))
ax.legend(title="HMS×SOS acceptance, occupancy-normalized",
          fontsize=FS_LEGEND - 1, title_fontsize=FS_LEGEND_TITLE - 1)
fig.suptitle("(e,e'p) missing energy vs Dutta Fig. 9 — spectrometer acceptance\n"
             r"e$^-$ on C12, 2.445 GeV · arm-frame $\delta$/y′/x′ boxes · "
             rf"models scaled to $\int$data = {I_DATA:.2f}",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)
print("\nchi2 vs data (total p2p errors ⊕ MC stat), 13 nonzero bins:")
for line in chi2_lines:
    print(" ", line)

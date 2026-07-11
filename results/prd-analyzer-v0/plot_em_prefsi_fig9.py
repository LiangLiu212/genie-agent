"""PRE-FSI missing energy, no cuts, occupancy-normalized, vs Dutta Fig. 9.

Event-level pre-FSI E_m (build_cache_prefsi.py: primary proton, hitnuc == p,
no selection beyond the sample's t05 generation cut) on the occupancy scale:

    y(E_m) = Z * hist(E_m; p_m < 300) / (N_hitp * 5 MeV)

Every sampled proton has a removal energy, so the full-p_m, full-E_m integral
is exactly Z = 6 per model by construction; the plotted p_m < 300 restriction
matches the fig9 observable. This is the generator-sampled ground state --
input table x cross-section (E,p) weighting -- so:
  - SF + Rosenbluth should closely reproduce the Benhar input f(E) (dashed):
    the factorized Rosenbluth model carries f(E) through unchanged (up to the
    Q^2 >= 1.18 kinematic sculpting of the sampling);
  - the SF + UnifiedQEL variants show the De Forest off-shell reshaping;
  - LFG / SuSAv2 show the Fermi-gas removal-energy prescriptions.
The input-table curves (k < 300, x Z) and the occupancy-normalized data are
overlaid for the like-for-like chain: input -> sampled (pre-FSI) -> S^D (FSI).
"""
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
from plot_spectral_function import find_sf_data
from plot_spectral_function_2024 import load_2024, load_old, Z

DATA = "data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat"
OUT = "results/prd-analyzer-v0/em_prefsi_fig9.png"
PM_MAX = 300.0
EDGES = np.arange(0.0, 85.0, 5.0)
BINW = 5.0


def f_restricted(k, P, dk, kmax=PM_MAX):
    sel = (k + dk / 2.0) <= kmax + 1e-9
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def rebin(E, f, dE, edges):
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (E >= lo) & (E < hi)
        out[i] = (f[m] * dE[m]).sum() / (hi - lo)
    return out


# ---- input tables (as in plot_sf_input_em_fig9.py) -----------------------------
k_o, E_o, P_o, dk_o, dE_o = load_old(find_sf_data())
k_n, E_n, P_n, dk_n, dE_n, _ = load_2024(Path("data/pke12_2024.table"))
y_in_old = rebin(E_o, f_restricted(k_o, P_o, dk_o), dE_o, EDGES)
y_in_new = rebin(E_n, f_restricted(k_n, P_n, dk_n), dE_n, EDGES)

# ---- data -----------------------------------------------------------------------
dem, dsf, _, dstat = np.loadtxt(DATA, unpack=True)
dtot = np.sqrt(dstat**2 + (0.02 * dsf)**2 + (0.05 * dsf)**2)
dtot[np.isclose(dem, 17.5)] = 0.081 * dsf[np.isclose(dem, 17.5)]
dtot[np.isclose(dem, 22.5)] = 0.047 * dsf[np.isclose(dem, 22.5)]

# ---- figure ---------------------------------------------------------------------
apply_style()
fig, (ax,) = new_panels(ncols=1, sharey=False)
fig.set_size_inches(7.5, 6.5)

print("pre-FSI occupancy bookkeeping (full integral = 6 by construction):")
for m in S.MODELS:
    c = dict(np.load(f"{S.CACHE_DIR}/prefsi/{m}.npz"))
    nh = float(c["n_hitp"][0])
    win = c["p_miss"] < PM_MAX
    cnt, _ = np.histogram(c["E_miss"][win], bins=EDGES)
    y = Z * cnt / (nh * BINW)
    ax.stairs(y, EDGES, color=S.color(m), linewidth=S.lw(m, base=1.8),
              zorder=S.zorder(m), label=f"{S.label(m)}")
    I = (y * BINW).sum()
    Em = c["E_miss"][win]
    print(f"  {m:15s} frac(pm<300) = {win.mean():.3f}   integral (Em<80) = {I:.3f}"
          f"   Em p5/p50/p95 = {np.percentile(Em,5):.1f}/{np.percentile(Em,50):.1f}/"
          f"{np.percentile(Em,95):.1f}")
print(f"  {'inputs':15s} old 5.25 / 2024 5.23 (k<300, Em<80);  data 6.08")

ax.stairs(y_in_old, EDGES, color=S.color("SF"), linewidth=1.2, linestyle="--",
          zorder=2, label="Benhar input f(E) (dashed)")
ax.stairs(y_in_new, EDGES, color=S.color("UnifiedQEL2024"), linewidth=1.2,
          linestyle="--", zorder=2, label="2024 input f(E) (dashed)")

ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
            alpha=0.8, zorder=8)
ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black", capsize=2,
            zorder=9, label="Dutta Fig. 9 (occupancy-normalized)")

style_axis(ax, title=r"pre-FSI $E_m$, no cuts,  $p_m<300$ MeV/$c$,  $\times Z/N_p$",
           xlabel=r"$E_m$  (MeV)", logx=False, logy=False, ymin=None)
ax.set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)", fontsize=FS_LABEL)
ax.set_xlim(0, 85)
ax.set_ylim(0, 1.3)      # the Rosenbluth-pair delta at Em = 16.0 MeV tops at 1.2
ax.legend(fontsize=FS_LEGEND - 2, title="sampled ground state (pre-INTRANUKE)",
          title_fontsize=FS_LEGEND_TITLE - 2)
fig.suptitle("pre-FSI missing energy vs Dutta Fig. 9 — occupancy scale\n"
             "generator-sampled removal energy (input × σ weighting), no detector cuts",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

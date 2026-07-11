"""Input (undistorted) removal-energy marginals of the two SF ground states,
overlaid on Dutta Fig. 9.

f_{k<300}(E) = Z * int_{k<300} 4pi k^2 P(k,E) dk -- the energy marginal of the
INPUT spectral-function tables, restricted to the paper's |p_m| < 300 MeV/c
integration window and put on the occupancy scale (x Z = 6), i.e. the same
normalization convention as the fig9 data (integral ~ Z; see
papers/nucl-ex_0303011/open_questions.md). No FSI, no cross-section weighting,
no acceptance: this isolates what the ground-state input ALONE looks like
against the (FSI-distorted in shape, occupancy-rescaled) measurement.

- SF        old Benhar `pke12_tot.data` (input of GEM26_22a/22b): native
            5-MeV E grid, exactly aligned with the data bins.
- SF(2024)  Ankowski-Benhar-Sakuda `data/pke12_2024.table` (input of
            GEM26_33b): 0.025/0.1 MeV grid; drawn bin-averaged into the data's
            5-MeV bins, plus the faint continuous curve showing the resolved
            NIKHEF quasiparticle peaks (clipped by the fig9 axis range).
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
OUT = "results/prd-analyzer-v0/sf_input_em_fig9.png"
PM_MAX = 300.0                       # the paper's |p_m| integration window [MeV/c]
EDGES = np.arange(0.0, 85.0, 5.0)    # data binning


def f_restricted(k, P, dk, kmax=PM_MAX):
    """Z * int_{k<kmax} 4pi k^2 P dk  -> occupancy-scale f(E) [MeV^-1]."""
    sel = (k + dk / 2.0) <= kmax + 1e-9          # bins fully below the window edge
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def rebin(E, f, dE, edges):
    """Bin-average a (possibly non-uniform-grid) f(E) into 5-MeV bins."""
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (E >= lo) & (E < hi)
        out[i] = (f[m] * dE[m]).sum() / (hi - lo)
    return out


# ---- inputs -------------------------------------------------------------------
old_path = find_sf_data()
k_o, E_o, P_o, dk_o, dE_o = load_old(old_path)
k_n, E_n, P_n, dk_n, dE_n, _ = load_2024(Path("data/pke12_2024.table"))

f_o = f_restricted(k_o, P_o, dk_o)
f_n = f_restricted(k_n, P_n, dk_n)
y_o = rebin(E_o, f_o, dE_o, EDGES)
y_n = rebin(E_n, f_n, dE_n, EDGES)

dem, dsf, _, dstat = np.loadtxt(DATA, unpack=True)
dtot = np.sqrt(dstat**2 + (0.02 * dsf)**2 + (0.05 * dsf)**2)
dtot[np.isclose(dem, 17.5)] = 0.081 * dsf[np.isclose(dem, 17.5)]
dtot[np.isclose(dem, 22.5)] = 0.047 * dsf[np.isclose(dem, 22.5)]

for name, E, f, dE, y in (("SF (pke12_tot)", E_o, f_o, dE_o, y_o),
                          ("SF(2024)", E_n, f_n, dE_n, y_n)):
    dEv = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    full = (f * dEv).sum()
    win = (f * dEv * ((E >= 0) & (E < 80))).sum()
    print(f"{name:16s} k<300: full integral = {full:.3f} protons; "
          f"E<80 window = {win:.3f}  (data occupancy integral 6.08)")

# ---- figure -------------------------------------------------------------------
apply_style()
fig, (ax,) = new_panels(ncols=1, sharey=False)
fig.set_size_inches(7.5, 6.5)

ax.stairs(y_o, EDGES, color=S.color("SF"), linewidth=2.0, zorder=4,
          label="Benhar SF")
fine = E_n <= 85.0
ax.plot(E_n[fine], f_n[fine], color=S.color("UnifiedQEL2024"), lw=1.0,
        alpha=0.55, zorder=3, label="SF 2024")
ax.stairs(y_n, EDGES, color=S.color("UnifiedQEL2024"), linewidth=2.0, zorder=5,
          label="SF 2024 rebin")

ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
            alpha=0.8, zorder=8)
ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black", capsize=2,
            zorder=9, label="Dutta data")

style_axis(ax, title=r"$^{12}$C input spectral functions vs data,  $k<300$ MeV/$c$",
           xlabel=r"$E_m$  (MeV)", logx=False, logy=False, ymin=None)
ax.set_ylabel(r"$Z\,\int_{k<300} 4\pi k^2 P(k,E)\,dk$   (MeV$^{-1}$)",
              fontsize=FS_LABEL)
ax.set_xlim(0, 85)
ax.set_ylim(0, 0.7)
ax.legend(fontsize=FS_LEGEND - 1, title="input tables",
          title_fontsize=FS_LEGEND_TITLE - 1)
fig.suptitle("ground-state inputs vs Dutta Fig. 9 — both on the occupancy scale\n"
             "(data are FSI-distorted in shape; inputs are the undistorted tables)",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

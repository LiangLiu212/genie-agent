"""Ar40 ground-state overview (2x2): momentum, removal energy, and 2D P(|p|,E).

One canvas, four panels comparing the two tunes that differ only in the Ar40
ground-state model:
  - LFG26_10a_00_000 : Local Fermi Gas   (LocalFGM)
  - SF26_10a_00_000  : spectral function (SpectralFunc)
Both: numu on Ar40, MicroBooNE flux, CC-inclusive, INCL FSI, 50k events.

  top-left   : 1D initial-nucleon momentum |p_n|              (LFG vs SF)
  top-right  : 1D removal energy E_rm = M_N - E_n             (LFG vs SF)
  bottom-left: 2D P(|p_n|, E_rm)  LFG
  bottom-right:2D P(|p_n|, E_rm)  SF   (shared log color scale)

Removal energy uses the M_N - E_n definition consistently (rest mass minus the
stored hit-nucleon energy). M_N from shared/pdg.json (proton/neutron by hitnuc).
Single-nucleon initial states only (hitnuc=p/n; excludes MEC di-nucleon
clusters); every distribution area-normalized (fraction/bin). Personal plot
style (results/template/plot_style.py).
"""
import sys, json
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, style_axis, PANEL_SIZE,
                        FS_LABEL, FS_TITLE, FS_TICK, FS_LEGEND,
                        FS_LEGEND_TITLE, FS_SUPTITLE)

BASE = "/exp/dune/data/users/liangliu/runarea/INCL/FEB02/LL25_20"
GST = "{base}/{tag}/14_1000180400_CC-INC_vINCL_{tag}.gst.root"
SERIES = [("LFG26_10a_00_000", "LFG  (LocalFGM)",    "C0"),
          ("SF26_10a_00_000",  "SF  (SpectralFunc)", "C1")]

MASS = {n["code"]: n["mass_gev"] * 1000.0
        for n in json.load(open("shared/pdg.json"))["nucleons"].values()}

# axis ranges shared between the 1D and 2D panels
PBINS = np.linspace(0.0, 500.0, 51)   # |p_n|   [MeV/c]  (1D x, 2D y)
EBINS = np.linspace(0.0, 150.0, 51)   # E_rm    [MeV]    (1D x, 2D x)


def load(tag):
    d = uproot.open(GST.format(base=BASE, tag=tag))["gst"].arrays(
        ["pxn", "pyn", "pzn", "En", "hitnuc"], library="np")
    keep = np.isin(d["hitnuc"], [2112, 2212])
    p = np.sqrt(d["pxn"]**2 + d["pyn"]**2 + d["pzn"]**2)[keep] * 1000.0
    En = d["En"][keep] * 1000.0
    M = np.array([MASS[c] for c in d["hitnuc"][keep]])
    return p, M - En


DATA = {tag: load(tag) for tag, _, _ in SERIES}

# 2D histograms (area-normalized) with a shared color range
H2D, vmax = {}, 0.0
for tag, _, _ in SERIES:
    p, erm = DATA[tag]
    H, _, _ = np.histogram2d(erm, p, bins=[EBINS, PBINS])
    H = H / H.sum()
    H2D[tag] = H
    vmax = max(vmax, H.max())

apply_style()
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
w, h = PANEL_SIZE
fig, axes = plt.subplots(2, 2, figsize=(w * 2.3, h * 2.0), layout="constrained")
(ax_p, ax_e), (ax2_lfg, ax2_sf) = axes

# --- top-left: 1D momentum -------------------------------------------------
for tag, label, color in SERIES:
    p, _ = DATA[tag]
    ax_p.hist(p, bins=PBINS, weights=np.full(p.shape, 1.0 / p.size),
              histtype="step", linewidth=1.8, color=color, label=label)
style_axis(ax_p, title="initial nucleon momentum",
           xlabel=r"|p$_n$|  [MeV/c]", logx=False, logy=False)
ax_p.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)
ax_p.legend(title="ground-state model", fontsize=FS_LEGEND,
            title_fontsize=FS_LEGEND_TITLE)

# --- top-right: 1D removal energy -----------------------------------------
for tag, label, color in SERIES:
    _, erm = DATA[tag]
    ax_e.hist(erm, bins=EBINS, weights=np.full(erm.shape, 1.0 / erm.size),
              histtype="step", linewidth=1.8, color=color, label=label)
style_axis(ax_e, title="removal energy",
           xlabel=r"E$_\mathrm{rm}$ = M$_N-$E$_n$  [MeV]", logx=False, logy=False)
ax_e.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)

# --- bottom row: 2D P(|p|,E) ----------------------------------------------
norm = LogNorm(vmin=vmax * 1e-4, vmax=vmax)
Xe, Ye = np.meshgrid(EBINS, PBINS, indexing="ij")
pc = None
for ax, (tag, label, _) in zip((ax2_lfg, ax2_sf), SERIES):
    Z = np.ma.masked_less_equal(H2D[tag], 0.0)
    pc = ax.pcolormesh(Xe, Ye, Z, cmap="viridis", norm=norm)
    ax.set_title(label, fontsize=FS_TITLE)
    ax.set_xlabel(r"E$_\mathrm{rm}$ = M$_N-$E$_n$  [MeV]", fontsize=FS_LABEL)
    ax.set_ylabel(r"|p$_n$|  [MeV/c]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
cb = fig.colorbar(pc, ax=(ax2_lfg, ax2_sf), pad=0.02, fraction=0.046)
cb.set_label("fraction of events / bin", fontsize=FS_TITLE)

fig.suptitle("$^{40}$Ar ground state: spectral function vs Local Fermi Gas\n"
             r"$\nu_\mu$ on $^{40}$Ar, CC-inclusive, INCL FSI "
             "$-$ single-nucleon initial states",
             fontsize=FS_SUPTITLE)
out = "results/groundstate_panel_incl_ar40_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

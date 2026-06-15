"""2D ground state P(|p|,E): spectral function vs Local Fermi Gas (INCL, Ar40).

Event-level realization of the nuclear ground state sampled by GENIE: struck-
nucleon momentum |p_n| vs removal energy E_rm, for the two tunes differing only
in the Ar40 ground-state model:
  - LFG26_10a_00_000 : Local Fermi Gas   (LocalFGM)  -> tight E(p) band
  - SF26_10a_00_000  : spectral function (SpectralFunc) -> broad 2D, SRC tail
Both: numu on Ar40, MicroBooNE flux, CC-inclusive, INCL FSI, 50k events.

From the gst hit-nucleon 4-momentum (pxn,pyn,pzn,En):
  |p_n|  = 1000*sqrt(pxn^2+pyn^2+pzn^2)            [MeV/c]
  E_rm   = sqrt(p_n^2 + M_N^2) - E_n                [MeV]   (on-shell - off-shell)
M_N from shared/pdg.json (proton/neutron by hitnuc). Restricted to single-nucleon
initial states (hitnuc=p/n; excludes MEC di-nucleon clusters). Each model is
area-normalized (fraction/bin) and shown on a shared log color scale, in the same
(E, k) orientation as results/prd-analyzer/spectral_function_c12.png.
"""
import sys, json
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import apply_style, FS_LABEL, FS_TITLE, FS_TICK, FS_SUPTITLE, PANEL_SIZE

BASE = "/exp/dune/data/users/liangliu/runarea/INCL/FEB02/LL25_20"
GST = "{base}/{tag}/14_1000180400_CC-INC_vINCL_{tag}.gst.root"
SERIES = [("LFG26_10a_00_000", "LFG  (LocalFGM)"),
          ("SF26_10a_00_000",  "SF  (SpectralFunc)")]

# nucleon masses [MeV] from the shared PDG table (no hardcoding)
_nuc = json.load(open("shared/pdg.json"))["nucleons"]
MASS = {n["code"]: n["mass_gev"] * 1000.0 for n in _nuc.values()}


def load(tag):
    d = uproot.open(GST.format(base=BASE, tag=tag))["gst"].arrays(
        ["pxn", "pyn", "pzn", "En", "hitnuc"], library="np")
    keep = np.isin(d["hitnuc"], [2112, 2212])
    p = np.sqrt(d["pxn"]**2 + d["pyn"]**2 + d["pzn"]**2)[keep] * 1000.0
    En = d["En"][keep] * 1000.0
    M = np.array([MASS[c] for c in d["hitnuc"][keep]])
    Erm = np.sqrt(p**2 + M**2) - En
    return p, Erm


EBINS = np.linspace(0.0, 150.0, 51)    # removal energy E  [MeV]   (x)
PBINS = np.linspace(0.0, 500.0, 51)    # |p_n|             [MeV/c] (y)

# precompute normalized 2D histograms + shared color range
HISTS, vmax = [], 0.0
for tag, label in SERIES:
    p, Erm = load(tag)
    H, _, _ = np.histogram2d(Erm, p, bins=[EBINS, PBINS])
    H = H / H.sum()                      # fraction / bin
    HISTS.append((label, H, len(p)))
    vmax = max(vmax, H.max())
    print(f"{tag}: N={len(p)}  <|p_n|>={p.mean():.1f} MeV/c  <E_rm>={Erm.mean():.1f} MeV")

apply_style()
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
w, h = PANEL_SIZE
fig, axes = plt.subplots(1, 2, figsize=(w * 2.4, h), sharey=True,
                         layout="constrained")
norm = LogNorm(vmin=vmax * 1e-4, vmax=vmax)
Xe, Ye = np.meshgrid(EBINS, PBINS, indexing="ij")
for ax, (label, H, n) in zip(axes, HISTS):
    Z = np.ma.masked_less_equal(H, 0.0)
    pc = ax.pcolormesh(Xe, Ye, Z, cmap="viridis", norm=norm)
    ax.set_title(f"{label}   (N={n})", fontsize=FS_TITLE)
    ax.set_xlabel("removal energy  E  [MeV]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
axes[0].set_ylabel(r"|p$_n$|  [MeV/c]", fontsize=FS_LABEL)
cb = fig.colorbar(pc, ax=axes, pad=0.02, fraction=0.046)
cb.set_label("fraction of events / bin", fontsize=FS_TITLE)

fig.suptitle("Ground-state P(|p|,E): spectral function vs Local Fermi Gas\n"
             r"$\nu_\mu$ on $^{40}$Ar, CC-inclusive, INCL FSI "
             "$-$ single-nucleon initial states",
             fontsize=FS_SUPTITLE)
out = "results/groundstate2d_incl_ar40_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

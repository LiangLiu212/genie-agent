"""Removal energy E_rm = M_N - E_n: spectral function vs Local Fermi Gas (INCL, Ar40).

Removal energy defined as the nucleon rest mass minus the stored initial-state
hit-nucleon energy:  E_rm = M_N - E_n   (NOT sqrt(p^2+M^2)-E_n; that variant adds
the on-shell kinetic term and is used in make_groundstate2d_incl_sf_lfg.py).

Two tunes differing only in the Ar40 ground-state model:
  - LFG26_10a_00_000 : Local Fermi Gas   (LocalFGM)
  - SF26_10a_00_000  : spectral function (SpectralFunc)
Both: numu on Ar40, MicroBooNE flux, CC-inclusive, INCL FSI, 50k events.

M_N from shared/pdg.json (proton/neutron by hitnuc). Restricted to single-nucleon
initial states (hitnuc=p/n; excludes MEC di-nucleon clusters), area-normalized.
Personal plot style (results/template/plot_style.py).

One figure, two views of the same E_rm:
  - left  : linear y, 0-100 MeV  (bulk; LFG edge vs SF)
  - right : log y,    0-350 MeV  (SF removal-energy tail vs LFG cutoff)
"""
import sys, json
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

BASE = "/exp/dune/data/users/liangliu/runarea/INCL/FEB02/LL25_20"
GST = "{base}/{tag}/14_1000180400_CC-INC_vINCL_{tag}.gst.root"
SERIES = [("LFG26_10a_00_000", "LFG  (LocalFGM)",    "C0"),
          ("SF26_10a_00_000",  "SF  (SpectralFunc)", "C1")]

MASS = {n["code"]: n["mass_gev"] * 1000.0
        for n in json.load(open("shared/pdg.json"))["nucleons"].values()}


def load(tag):
    d = uproot.open(GST.format(base=BASE, tag=tag))["gst"].arrays(
        ["En", "hitnuc"], library="np")
    keep = np.isin(d["hitnuc"], [2112, 2212])
    En = d["En"][keep] * 1000.0
    M = np.array([MASS[c] for c in d["hitnuc"][keep]])
    return M - En  # removal energy [MeV]


LOADED = []
for tag, label, color in SERIES:
    erm = load(tag)
    LOADED.append((label, color, erm))
    print(f"{tag}: N={erm.size}  <E_rm>={erm.mean():.1f}  max={erm.max():.1f} MeV")

EBINS_LIN = np.linspace(0.0, 100.0, 51)   # 2 MeV bins
EBINS_LOG = np.linspace(0.0, 350.0, 71)   # 5 MeV bins

apply_style()
fig, axes = new_panels(ncols=2, sharey=False)
axlin, axlog = axes
for label, color, erm in LOADED:
    w = np.full(erm.shape, 1.0 / erm.size)  # area-normalize: fraction / bin
    axlin.hist(erm, bins=EBINS_LIN, weights=w, histtype="step",
               linewidth=1.8, color=color, label=label)
    axlog.hist(erm, bins=EBINS_LOG, weights=w, histtype="step",
               linewidth=1.8, color=color, label=label)

style_axis(axlin, title="removal energy",
           xlabel=r"E$_\mathrm{rm}$ = M$_N-$E$_n$  [MeV]", logx=False, logy=False)
style_axis(axlog, title="removal-energy tail (log y)",
           xlabel=r"E$_\mathrm{rm}$ = M$_N-$E$_n$  [MeV]", logx=False, logy=True,
           ymin=1e-5)
axlin.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)
axlog.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)
axlin.legend(title="ground-state model", fontsize=FS_LEGEND,
             title_fontsize=FS_LEGEND_TITLE)

fig.suptitle("Removal energy  M$_N-$E$_n$: spectral function vs Local Fermi Gas\n"
             r"$\nu_\mu$ on $^{40}$Ar, CC-inclusive, INCL FSI "
             "$-$ single-nucleon initial states",
             fontsize=FS_SUPTITLE)
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = "results/groundstate_removalE_incl_ar40_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

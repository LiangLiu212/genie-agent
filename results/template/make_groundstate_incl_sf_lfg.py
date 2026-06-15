"""Initial-state nucleon momentum: spectral function vs Local Fermi Gas (INCL, Ar40).

Two tunes differing only in the Ar40 ground-state nuclear model:
  - LFG26_10a_00_000 : Local Fermi Gas   (LocalFGM)
  - SF26_10a_00_000  : spectral function (SpectralFunc)
Both: numu on Ar40, MicroBooNE flux (hEnumu_cv), CC-inclusive, INCL FSI, 50k events
(see runarea/INCL/FEB02/LL25_20/run_gevgen.sh).

Plots the struck-nucleon momentum |p_n| = sqrt(pxn^2+pyn^2+pzn^2) from the gst
trees. Restricted to SINGLE-NUCLEON initial states (hitnuc = p/n), excluding MEC
di-nucleon clusters (hitnuc 2000000200/201) whose pn is a pair momentum, so this
is the genuine single-nucleon distribution n(|p|). Each model is area-normalized
(fraction of events / bin) for a fair shape comparison. Personal plot style
(results/template/plot_style.py).

One figure, two views of the same |p_n|:
  - left  : linear y, 0-600 MeV/c  (bulk shape; LFG Fermi edge vs SF)
  - right : log y,    0-1000 MeV/c (SF short-range-correlation tail vs LFG cutoff)
"""
import sys
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

BASE = "/exp/dune/data/users/liangliu/runarea/INCL/FEB02/LL25_20"
GST = "{base}/{tag}/14_1000180400_CC-INC_vINCL_{tag}.gst.root"

# tune dir -> (legend label, color)
SERIES = [
    ("LFG26_10a_00_000", "LFG  (LocalFGM)",    "C0"),
    ("SF26_10a_00_000",  "SF  (SpectralFunc)", "C1"),
]
NUCLEONS = {2112, 2212}  # single-nucleon initial states (exclude MEC clusters)


def load(tag):
    d = uproot.open(GST.format(base=BASE, tag=tag))["gst"].arrays(
        ["pxn", "pyn", "pzn", "hitnuc"], library="np")
    pmag = np.sqrt(d["pxn"]**2 + d["pyn"]**2 + d["pzn"]**2) * 1000.0  # MeV/c
    keep = np.isin(d["hitnuc"], list(NUCLEONS))
    return pmag[keep], keep.sum(), len(keep)


LOADED = []
for tag, label, color in SERIES:
    pmag, nkeep, ntot = load(tag)
    LOADED.append((label, color, pmag))
    print(f"{tag}: {nkeep}/{ntot} single-nucleon events  "
          f"<|p_n|>={pmag.mean():.1f}  max={pmag.max():.1f} MeV/c")

PBINS_LIN = np.linspace(0.0, 600.0, 61)    # 10 MeV/c bins
PBINS_LOG = np.linspace(0.0, 1000.0, 101)  # 10 MeV/c bins

apply_style()
fig, axes = new_panels(ncols=2, sharey=False)
axlin, axlog = axes
for label, color, pmag in LOADED:
    w = np.full(pmag.shape, 1.0 / pmag.size)  # area-normalize: fraction / bin
    axlin.hist(pmag, bins=PBINS_LIN, weights=w, histtype="step",
               linewidth=1.8, color=color, label=label)
    axlog.hist(pmag, bins=PBINS_LOG, weights=w, histtype="step",
               linewidth=1.8, color=color, label=label)

style_axis(axlin, title="struck-nucleon momentum",
           xlabel=r"|p$_n$|  [MeV/c]", logx=False, logy=False)
style_axis(axlog, title="high-momentum tail (log y)",
           xlabel=r"|p$_n$|  [MeV/c]", logx=False, logy=True, ymin=1e-5)
axlin.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)
axlog.set_ylabel("fraction of events / bin", fontsize=FS_LABEL)
axlin.legend(title="ground-state model", fontsize=FS_LEGEND,
             title_fontsize=FS_LEGEND_TITLE)

fig.suptitle("Initial nucleon momentum: spectral function vs Local Fermi Gas\n"
             r"$\nu_\mu$ on $^{40}$Ar, CC-inclusive, INCL FSI "
             "$-$ single-nucleon initial states",
             fontsize=FS_SUPTITLE)
fig.tight_layout(rect=(0, 0, 1, 0.95))
out = "results/groundstate_incl_ar40_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

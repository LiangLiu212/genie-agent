#!/usr/bin/env python
"""Total cross section of the rc-v380 spline products (all 8 tune/target sets).

Reads gspl2root's `xsec_graphs-<Target>.root` next to each merged product:
per probe directory (nu_mu_<T>, nu_mu_bar_<T>) the `tot_cc` and `tot_nc`
graphs, GENIE's own sum of all channel splines on a 1000-point grid, in
1e-38 cm^2 per nucleus. Plots sigma_total / (A E) (per nucleon, per GeV) vs E,
one panel per probe, one series per product; points at/above each product's
Emax are dropped (gspl2root evaluates to 0 outside the spline range). Lines
only: the 1000 grid points are gspl2root's evaluation grid, not spline knots.
House style (results/template/plot_style.py).
"""
import sys, re
from pathlib import Path
import numpy as np, uproot
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_style import apply_style, new_panels, style_axis, FLOOR, FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI

BASE = Path("/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380")
OUT = Path("results/rc-v380-splines/total_xsec_rc-v380.png")
A = {"C12": 12, "Ar40": 40, "Fe56": 56}
# (sample, tune, target, Emax)
PRODUCTS = [("A", "G18_10a_02_11b", "Ar40", 10), ("B", "AR23_20m_00_000", "Ar40", 10),
            ("C", "AR23_20n_00_000", "Ar40", 10), ("D", "G24_12a_00_000", "C12", 5),
            ("D", "G24_12a_00_000", "Ar40", 5), ("E", "AR25_20i_00_000", "C12", 3),
            ("E", "AR25_20i_00_000", "Ar40", 3), ("G", "G18_10a_02_11b", "Fe56", 50)]
PROBES = [("nu_mu", r"$\nu_\mu$"), ("nu_mu_bar", r"$\bar{\nu}_\mu$")]
COLORS8 = [f"C{i}" for i in range(8)]

def total(f, probe, target, emax):
    d = f"{probe}_{target}"
    cc, nc = f[f"{d}/tot_cc"], f[f"{d}/tot_nc"]
    E = cc.values(axis="x"); y = cc.values(axis="y") + nc.values(axis="y")
    assert np.allclose(E, nc.values(axis="x"))
    keep = E < 0.999 * emax
    return E[keep], y[keep] / A[target] / E[keep]

apply_style()
fig, axes = new_panels(ncols=2)
for ax, (probe, plabel) in zip(axes, PROBES):
    for i, (sample, tune, target, emax) in enumerate(PRODUCTS):
        f = uproot.open(BASE / tune / f"xsec_graphs-{target}.root")
        E, y = total(f, probe, target, emax)
        ax.plot(E, y, "-", lw=1.8, color=COLORS8[i],
                label=f"{sample}: {tune} {target} (to {emax} GeV)")
    style_axis(ax, title=plabel, xlabel="E [GeV]", logx=True)
    ax.set_xlim(0.05, 60); ax.set_ylim(0, None)
axes[0].set_ylabel(r"$\sigma_{\rm tot}\,/\,E$ per nucleon  [$10^{-38}$ cm$^2$/GeV]", fontsize=FS_LABEL)
axes[0].legend(title="sample: tune target", fontsize=FS_LEGEND - 3, title_fontsize=FS_LEGEND_TITLE - 1, loc="lower right")
fig.suptitle("rc-v380 spline products: total (CC+NC) cross section / E per nucleon", fontsize=FS_SUPTITLE)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

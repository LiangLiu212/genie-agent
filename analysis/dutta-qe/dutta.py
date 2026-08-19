"""Dutta E91-013 author data (PRC figs 6/7/9/11) with the resolved conventions.

Conventions established in results/normalization/README.md and
report/dutta-e91013-figures.md:

- E_m spectra (figs 9/11): f(E_m) [MeV^-1] on the published scales
  (fig 9 renormalized to full occupancy ~ Z; fig 11 = in-window IPSM
  strength, NOT a Z-normalization). Column 4 = statistical errors; the
  total-error model adds 2% pt-to-pt (+) 5% model, with fig 9's two
  p-shell peak bins overridden by the pixel-measured published bars.
- p_m sets (figs 6/7): y(p_m) = int S^D dE_m [MeV^-3] on a SIGNED axis
  carrying HALF the |p_m| density per side. Folding (y(+p) + y(-p) = 2y(+p),
  the files are exactly symmetrized) restores the full density: 2 x fig 7
  equals fig 11's strength to 0.03%. Folded errors are 2 x the stat column
  (the sides are duplicated, not independent).
- Only the Q^2 = 1.28 files are used quantitatively; the Q^2 = 0.64 files
  are anomalous (x1.35 high, report S3) and excluded.

All loaders return MeV-based arrays ready for the plots.
"""
import numpy as np

from config import DUTTA_DIR


def load_fig9():
    """C12 E_m spectrum -> (em, sf, stat, tot)."""
    dem, dsf, _, dstat = np.loadtxt(DUTTA_DIR / "fig9_q1p2.dat", unpack=True)
    dtot = np.sqrt(dstat ** 2 + (0.02 * dsf) ** 2 + (0.05 * dsf) ** 2)
    dtot[np.isclose(dem, 17.5)] = 0.081 * dsf[np.isclose(dem, 17.5)]
    dtot[np.isclose(dem, 22.5)] = 0.047 * dsf[np.isclose(dem, 22.5)]
    return dem, dsf, dstat, dtot


def load_fig11():
    """Fe56 E_m spectrum -> (em, sf, stat, tot)."""
    dem, dsf, _, dstat = np.loadtxt(DUTTA_DIR / "fig11_q1p2.dat", unpack=True)
    dtot = np.sqrt(dstat ** 2 + (0.02 * dsf) ** 2 + (0.05 * dsf) ** 2)
    return dem, dsf, dstat, dtot


def load_em(target):
    return {"C12": load_fig9, "Fe56": load_fig11}[target]()


def load_folded_pm(target):
    """Folded (L+R summed) |p_m| density -> (p, y, err) [MeV/c, MeV^-3].

    C12: fig 6 top+bottom summed (E_m 10-25 (+) 30-50 MeV) then folded;
    Fe56: fig 7 (E_m < 80 MeV) folded. Q^2 = 1.28 files only.
    """
    if target == "C12":
        x, y_p, _, e_p = np.loadtxt(DUTTA_DIR / "fig6_top_q1p2.dat", unpack=True)
        _, y_s, _, e_s = np.loadtxt(DUTTA_DIR / "fig6_bot_q1p2.dat", unpack=True)
        y, e = y_p + y_s, np.sqrt(e_p ** 2 + e_s ** 2)
    else:
        x, y, _, e = np.loadtxt(DUTTA_DIR / "fig7_q1p2.dat", unpack=True)
    m = x > 0
    return x[m], 2.0 * y[m], 2.0 * e[m]

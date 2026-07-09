"""Shared constants + helpers for the Dutta Fig. 9 occupancy-scale comparisons.

Single home for the pieces duplicated between plot_sf_input_em_fig9.py and
plot_em_prefsi_fig9.py (those originals are left untouched): the digitized
fig9 data + its error model, the input-table loaders, and the restricted
marginals of the SF tables. Used by the generator-workflow-ladder scripts
(plan: .claude/plans/generator-workflow-ladder.md).

Callers run from the repo root with results/template and results/prd-analyzer
on sys.path (the house pattern; plot_spectral_function* handle the
plot_style import path themselves).
"""
from pathlib import Path

import numpy as np

from plot_spectral_function import find_sf_data
from plot_spectral_function_2024 import load_2024, load_old, Z  # noqa: F401  (Z re-exported)

DATA = "data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat"
PM_MAX = 300.0                       # the paper's |p_m| integration window [MeV/c]
BINW = 5.0                           # data bin width [MeV]
EDGES = np.arange(0.0, 85.0, 5.0)    # data binning [MeV]
EM_MAX = 80.0                        # the paper's E_m integration window [MeV]


def load_dutta(path=DATA):
    """Digitized fig9 -> (em, sf, stat, tot).

    stat = the file's statistical-only bars; tot = stat (+) 2% pt-to-pt (+) 5%
    model, with the two p-shell peak bins overridden by the pixel-measured
    published bars (see papers/nucl-ex_0303011/open_questions.md).
    """
    dem, dsf, _, dstat = np.loadtxt(path, unpack=True)
    dtot = np.sqrt(dstat**2 + (0.02 * dsf)**2 + (0.05 * dsf)**2)
    dtot[np.isclose(dem, 17.5)] = 0.081 * dsf[np.isclose(dem, 17.5)]
    dtot[np.isclose(dem, 22.5)] = 0.047 * dsf[np.isclose(dem, 22.5)]
    return dem, dsf, dstat, dtot


def load_input_tables():
    """Both input SF grids -> {"old": (k, E, P, dk, dE), "new": (k, E, P, dk, dE)}.

    old = Benhar pke12_tot.data resolved from the active installation
    (GEM26_22a/22b input); new = the 2024 Ankowski-Benhar-Sakuda table
    (GEM26_33b input). P is per-proton; k, E in MeV; dE scalar (old) or
    per-bin vector (new).
    """
    k_o, E_o, P_o, dk_o, dE_o = load_old(find_sf_data())
    k_n, E_n, P_n, dk_n, dE_n, _ = load_2024(Path("data/pke12_2024.table"))
    return {"old": (k_o, E_o, P_o, dk_o, dE_o),
            "new": (k_n, E_n, P_n, dk_n, dE_n)}


def f_restricted(k, P, dk, kmax=PM_MAX):
    """Z * int_{k<kmax} 4pi k^2 P dk  -> occupancy-scale f(E) [MeV^-1]."""
    sel = (k + dk / 2.0) <= kmax + 1e-9          # bins fully below the window edge
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def n_restricted(k, E, P, dE, emax=EM_MAX):
    """Z * int_{E<emax} 4pi k^2 P dE  -> occupancy-scale n-tilde(k) [(MeV/c)^-1].

    The k-marginal companion of f_restricted, restricted to the paper's
    E_m < 80 MeV window (dE scalar or per-bin vector).
    """
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    sel = (E + dE / 2.0) <= emax + 1e-9
    w = 4.0 * np.pi * (k[:, None] ** 2) * P[:, sel]
    return Z * (w * dE[sel]).sum(axis=1)


def rebin(E, f, dE, edges):
    """Bin-average a (possibly non-uniform-grid) f(E) into the data bins."""
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (E >= lo) & (E < hi)
        out[i] = (f[m] * dE[m]).sum() / (hi - lo)
    return out

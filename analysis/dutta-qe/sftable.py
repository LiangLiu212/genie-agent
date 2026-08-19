"""GENIE 2D spectral-function tables: parser + windowed marginals.

Parses the pke tables exactly as genie::SpectralFunc::LoadSFDataFile does
(copied from results/template/make_sf2d_table.py) and provides the two
occupancy-scale projections used against the Dutta data:

    f(E_m)  = Z * int_{p<pmax} 4pi k^2 P dk    [MeV^-1]      (vs figs 9/11)
    n(p_m)  = Z * int_{E win}  4pi k^2 P dE    [(MeV/c)^-1]  (vs figs 6/7)

with P area-normalized first (int 4pi k^2 P dk dE = 1), so the marginals
integrate to (the in-window fraction of) Z regardless of the table's own
N*P scale.
"""
import numpy as np

from config import TARGETS, sf_table_path


def read_pke_table(path):
    """Parse a pke table -> (p_centers, E_centers, p_edges, E_edges, S)."""
    tok = path.read_text().split()
    n_E, n_p = int(tok[0]), int(tok[1])
    E_min, p_min = float(tok[2]), float(tok[3])
    E_max, p_max = float(tok[4]), float(tok[5])
    body = np.array(tok[6:], dtype=float)
    assert body.size == n_p * (1 + 2 * n_E), f"token count mismatch in {path}"
    blocks = body.reshape(n_p, 1 + 2 * n_E)
    p_centers = blocks[:, 0]                            # [MeV/c]
    E_centers = blocks[0, 1::2]                         # [MeV]
    assert np.allclose(blocks[:, 1::2], E_centers), "E grid varies"
    S = blocks[:, 2::2]                                 # [MeV^-4], (n_p, n_E)
    p_edges = np.linspace(p_min, p_max, n_p + 1)
    E_edges = np.linspace(E_min, E_max, n_E + 1)
    return p_centers, E_centers, p_edges, E_edges, S


def load_table(target):
    """Area-normalized table -> (stem, dict(k, E, k_edges, E_edges, P, dk, dE))."""
    path = sf_table_path(target)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    print(f"input table {path.name}: raw 4pi k^2 integral = {raw:.3f} "
          f"(N*P convention); occupancy scale Z={TARGETS[target]['Z']}")
    return path.stem, dict(k=k, E=E, k_edges=k_edges, E_edges=E_edges,
                           P=S / raw, dk=dk, dE=dE)


def f_restricted(tab, Z, pmax):
    """f(E) = Z * int_{p<pmax} 4pi k^2 P dk on the table's native E grid."""
    sel = (tab["k"] + tab["dk"] / 2.0) <= pmax + 1e-9
    w = 4.0 * np.pi * (tab["k"][sel, None] ** 2) * tab["P"][sel, :]
    return Z * (w * tab["dk"]).sum(axis=0)


def n_windowed(tab, Z, e_windows):
    """n(k) = Z * int_{E win} 4pi k^2 P dE, partial E bins clipped exactly."""
    E, dE = tab["E"], tab["dE"]
    ov = np.zeros_like(E)
    for lo, hi in e_windows:
        ov += np.clip(np.minimum(E + dE / 2.0, hi)
                      - np.maximum(E - dE / 2.0, lo), 0.0, None)
    return Z * 4.0 * np.pi * (tab["k"] ** 2) * (tab["P"] * ov[None, :]).sum(axis=1)


def rebin(E, f, dE, edges):
    """Spread each native E column uniformly over its bin into `edges`."""
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        ov = np.clip(np.minimum(E + dE / 2.0, hi) - np.maximum(E - dE / 2.0, lo),
                     0.0, None)
        out[i] = (f * ov).sum() / (hi - lo)
    return out

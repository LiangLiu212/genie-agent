"""Cache access + the study's derived quantities and window masks.

A cache (built by build_cache.py) holds, per target/tune, the events passing

    qel && hitnuc==2212 && |Q^2/1.28 - 1| <= 5%

as arrays [MeV, MeV/c]: E2/p2 (struck-nucleon record m_N - E_n, |p_n|),
E3/p3 (pre-FSI primary proton omega - T_p, |p_p - q|), E4/p4 (post-FSI
unique proton of N_p = 1 events; NaN where no unique proton), plus
ntot/n_sel. This module adds the restored E axis and the window masks.
"""
import numpy as np

from config import CACHE_DIR, M_REC


def load_cache(target, tune):
    """-> (cache dict with E{2,3,4}r added, n_sel). Raises if missing."""
    path = CACHE_DIR / target.lower() / f"{tune}.npz"
    if not path.exists():
        raise SystemExit(f"missing cache {path} — run build_cache.py first "
                         "(--seed-from-v03 or --stream)")
    c = dict(np.load(path))
    m_rec_mev = M_REC[target] * 1000.0
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):          # restored axis: E_s + p_s^2 / (2 M_rec)
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec_mev)
    return c, float(c["n_sel"][0])


def in_windows(Er, e_windows):
    """Mask: finite Er inside any of the [lo, hi) windows."""
    m = np.zeros(Er.shape, dtype=bool)
    for lo, hi in e_windows:
        m |= (Er >= lo) & (Er < hi)
    return m & np.isfinite(Er)


def occ_hist(vals, edges, n_sel, Z):
    """Occupancy density Z * dN/dx / N_sel (area = in-window nucleon count)."""
    cnt, _ = np.histogram(vals[np.isfinite(vals)], bins=edges)
    return Z * cnt / (n_sel * float(np.diff(edges).mean()))


def unit_hist(vals, edges):
    """Shape: histogram normalized by its own in-range count (unit integral).

    -> (density, N_in_range)."""
    v = vals[np.isfinite(vals)]
    v = v[(v >= edges[0]) & (v < edges[-1])]
    cnt, _ = np.histogram(v, bins=edges)
    n = int(cnt.sum())
    return cnt / max(n, 1) / float(np.diff(edges).mean()), n


def strength(y, edges, xmax):
    """Windowed integral of a density histogram up to xmax (edge-aligned)."""
    sel = edges[1:] <= xmax + 1e-9
    return float((y[sel] * np.diff(edges)[sel]).sum())

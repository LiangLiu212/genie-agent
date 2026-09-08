"""Occupancy-normalization counts for the (e,e'p) ladder scripts.

Two conventions for the count N in the occupancy scale Z * hist / (N * binw):

  windowed  (v0.2-v1.1)  N_sel = qel && hit p && analysis window, the
                         cache's own `n_sel` -- every pre-FSI stage then
                         integrates to Z by construction.
  total-qe  (v1.2+)      N_QE  = ALL generated QE events of the sample
                         (qel, both hit-nucleon species, no Q^2 / E_m / p_m
                         window), so the windowed stages carry the fraction
                         of the generated QE phase space that the analysis
                         selection keeps.

N_QE is read from the v0.1 kinematics cache
results/prd-analyzer-v0.1/cache/kin_qel_<target>/<tune>.npz, whose entries
are exactly the `qel` events of the full-EM t05 sample (make_kin_qel.py:
selection "qel only", both species, no window), plus its `ntot`.
"""
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
KIN_CACHE_ROOT = REPO / "results/prd-analyzer-v0.1/cache"
NORMS = ("windowed", "total-qe")
NORM_LABELS = {"windowed": r"N_{sel}", "total-qe": r"N_{QE}"}


def total_qe_count(target, tune):
    """(n_qe, ntot) of the full-EM sample from the v0.1 kinematics cache."""
    path = KIN_CACHE_ROOT / f"kin_qel_{target.lower()}" / f"{tune}.npz"
    if not path.exists():
        raise SystemExit(f"--norm total-qe needs the v0.1 kinematics cache "
                         f"{path} (results/template/make_kin_qel.py)")
    c = np.load(path)
    return int(len(c["Q2"])), int(c["ntot"][0])


def norm_count(norm, target, tune, cache):
    """(count, one-line description) for the chosen convention."""
    if norm == "windowed":
        return float(cache["n_sel"][0]), (
            f"N_sel = qel && hit p && window = {int(cache['n_sel'][0]):,}")
    n_qe, ntot = total_qe_count(target, tune)
    if int(cache["ntot"][0]) != ntot:
        print(f"  WARNING: ladder cache ntot {int(cache['ntot'][0]):,} != "
              f"kinematics cache ntot {ntot:,}")
    return float(n_qe), (f"N_QE = all generated qel events (both species, "
                         f"no window) = {n_qe:,} of ntot {ntot:,}")

"""Normalization integrals of the pke* spectral-function tables.

Computes  I = sum 4*pi*k^2 P(k,E) dk dE  for every pke* table in the active
GENIE installation's data/evgen/nucl/spectral_functions/, handling both layouts:

  - GENIE uniform format (pke*_tot.data, pke12_2024.table), the layout
    SpectralFunc::LoadSFDataFile reads: header nE np / Emin pmin / Emax pmax,
    then np blocks {k_center, nE (E_center, P) pairs}. dk, dE come from the
    header edge ranges -- exactly the bin widths GENIE's TH2D uses.
  - 2024 origin format (pke12_2024.table.origin, and the repo copy
    data/pke12_2024.table): header n_k dk / n1 dE1 n2 dE2, then n_k blocks
    {k, (n1+n2) (E, P) pairs}; per-segment dE (fine + coarse energy grids).

The tables are tabulated in GENIE's "N*P" convention (SpectralFunc divides by
targetN at read time), so I should equal the nucleon count of the tabulated
species: Z for proton SFs, N for the Ar40 neutron table.

The parse/integrate helpers are imported by make_sf2d_all.py (2D figures).

Usage:
  pixi run python results/normalization/integrate_all_pke.py [data_dir]
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]

# expected nucleon count of the tabulated species, keyed by filename stem
EXPECTED = {
    "pke12_tot.data": ("C12 p", 6),
    "pke12_2024.table": ("C12 p", 6),
    "pke12_2024.table.origin": ("C12 p", 6),
    "pke16_tot.data": ("O16 p", 8),
    "pke40p_tot.data": ("Ar40 p", 18),
    "pke40n_tot.data": ("Ar40 n", 22),
    "pke56_tot.data": ("Fe56 p", 26),
}


def default_data_dir() -> Path:
    cfg = json.load(open(REPO / "genie-agent" / "config" / "genie_env.json"))
    inst = cfg["installations"][cfg["active_installation"]]
    return (Path(inst["genie_bin_dir"]).parent
            / "data" / "evgen" / "nucl" / "spectral_functions")


def parse_uniform(tok):
    n_E, n_p = int(tok[0]), int(tok[1])
    E_min, p_min, E_max, p_max = tok[2], tok[3], tok[4], tok[5]
    if tok.size != 6 + n_p * (1 + 2 * n_E):
        return None
    body = tok[6:].reshape(n_p, 1 + 2 * n_E)
    k = body[:, 0]
    P = body[:, 2::2]
    dk = (p_max - p_min) / n_p
    dE = (E_max - E_min) / n_E
    k_edges = np.linspace(p_min, p_max, n_p + 1)
    E_edges = np.linspace(E_min, E_max, n_E + 1)
    dk_w = np.full(n_p, dk)
    dE_w = np.full(n_E, dE)
    grid = (f"{n_p} k x {n_E} E  (k [{p_min:.0f},{p_max:.0f}] dk={dk:g}, "
            f"E [{E_min:.0f},{E_max:.0f}] dE={dE:g})")
    return k, P, k_edges, E_edges, dk_w, dE_w, grid


def parse_origin(tok):
    n_k, dk = int(tok[0]), tok[1]
    n1, d1, n2, d2 = int(tok[2]), tok[3], int(tok[4]), tok[5]
    n_E = n1 + n2
    if tok.size != 6 + n_k * (1 + 2 * n_E):
        return None
    body = tok[6:].reshape(n_k, 1 + 2 * n_E)
    k = body[:, 0]
    P = body[:, 2::2]
    dk_w = np.full(n_k, dk)
    dE_w = np.concatenate([np.full(n1, d1), np.full(n2, d2)])
    k_edges = np.concatenate([k - dk / 2, [k[-1] + dk / 2]])
    E0 = body[0, 1] - d1 / 2
    E_edges = np.concatenate([[E0], E0 + np.cumsum(dE_w)])
    grid = (f"{n_k} k x {n_E} E  (dk={dk:g}, "
            f"E segments {n1}x{d1:g} + {n2}x{d2:g} MeV)")
    return k, P, k_edges, E_edges, dk_w, dE_w, grid


def parse_table(path: Path):
    """Returns (k, P, k_edges, E_edges, dk_widths, dE_widths, grid_str) or None."""
    tok = np.fromstring(path.read_text(), sep=" ")
    return parse_uniform(tok) or parse_origin(tok)


def integral(k, P, dk_w, dE_w) -> float:
    return float((4.0 * np.pi * k[:, None] ** 2 * P
                  * dk_w[:, None] * dE_w[None, :]).sum())


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_data_dir()
    print(f"data dir: {data_dir}\n")
    print(f"{'file':30s} {'species':8s} {'integral':>12s} {'expect':>6s} "
          f"{'I/N':>10s}   grid")
    for f in sorted(data_dir.glob("pke*")):
        if f.suffix == ".py" or f.is_dir():
            continue
        res = parse_table(f)
        if res is None:
            print(f"{f.name:30s} UNRECOGNIZED FORMAT")
            continue
        k, P, _, _, dk_w, dE_w, grid = res
        I = integral(k, P, dk_w, dE_w)
        species, n_exp = EXPECTED.get(f.name, ("?", None))
        ratio = f"{I / n_exp:10.6f}" if n_exp else f"{'-':>10s}"
        exp_s = f"{n_exp:6d}" if n_exp else f"{'-':>6s}"
        print(f"{f.name:30s} {species:8s} {I:12.6f} {exp_s} {ratio}   {grid}")


if __name__ == "__main__":
    main()

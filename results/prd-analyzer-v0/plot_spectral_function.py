"""Benhar C12 spectral function P(k,E) in (missing energy, missing momentum).

Reads GENIE's tabulated Benhar 2D spectral function for C12 straight from
data/evgen/nucl/spectral_functions/pke12_tot.data and plots it in the same
(missing energy E, missing momentum k) plane the event-level prd-analyzer plots
use. This is the *input* ground state both SF+Rosenbluth (GEM26_22a) and
SF+UnifiedQEL (GEM26_22b) sample from: SF+Rosenbluth reproduces the full
removal-energy marginal f(E) below; SF+UnifiedQEL reshapes it lower via the
De Forest off-shell weighting.

File format (verified against GENIE Physics/NuclearState/SpectralFunc.cxx:273-330):
  header:  num_E_bins num_p_bins      ->  80 40
           E_min      p_min           ->   0  0      (MeV)
           E_max      p_max           -> 400 800     (MeV)
  body:    40 momentum blocks; each = momentum value k, then 80 (E, P) pairs.
  P is the density P(k,E) in MeV^-4, tabulated as N*P (N = nucleon count); the
  physically sampled weight per bin is 4*pi*k^2 * P(k,E) dk dE.

Personal plot style (results/template/plot_style.py).
"""
import sys
import json
from pathlib import Path

import numpy as np

sys.path.insert(0, "results/template")
from plot_style import (apply_style, style_axis, PANEL_SIZE, DPI,
                        FS_LABEL, FS_SUPTITLE, FS_TITLE)

TARGET_N = 6  # C12 protons (file folds in the nucleon count; GENIE divides it out)


def find_sf_data():
    """Resolve pke12_tot.data from the active genie-agent installation."""
    rel = "data/evgen/nucl/spectral_functions/pke12_tot.data"
    cfg = Path("genie-agent/config/genie_env.json")
    if cfg.is_file():
        d = json.loads(cfg.read_text())
        active = d.get("active_installation")
        inst = d.get("installations", {}).get(active, {})
        bindir = inst.get("genie_bin_dir")
        if bindir:
            cand = Path(bindir).parent / rel   # <Generator>/bin -> <Generator>/data/...
            if cand.is_file():
                return cand
    # fallback: known genie_inclxx path
    fb = Path("/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator") / rel
    if fb.is_file():
        return fb
    raise FileNotFoundError("could not locate pke12_tot.data")


def load_spectral_function(path):
    """Return (k_centers, E_centers, P) with P[ik, iE] the density in MeV^-4."""
    tok = np.fromstring(path.read_text().replace("E", "e"), sep=" ")
    # NB: 'E'->'e' so FORTRAN exponents parse; header ints survive as floats.
    num_E, num_p = int(tok[0]), int(tok[1])
    E_min, p_min = tok[2], tok[3]
    E_max, p_max = tok[4], tok[5]
    body = tok[6:]

    block = 1 + 2 * num_E           # momentum value + num_E (E, P) pairs
    body = body[:num_p * block].reshape(num_p, block)

    k_centers = body[:, 0]                       # MeV
    pairs = body[:, 1:].reshape(num_p, num_E, 2)
    E_centers = pairs[0, :, 0]                   # MeV (same grid for every k)
    P = pairs[:, :, 1] / TARGET_N                # MeV^-4, per-nucleon

    # bin widths (equally spaced per the file format)
    dk = (p_max - p_min) / num_p                 # 20 MeV
    dE = (E_max - E_min) / num_E                 # 5 MeV
    return k_centers, E_centers, P, dk, dE


def main():
    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    path = find_sf_data()
    print(f"reading {path}")
    k, E, P, dk, dE = load_spectral_function(path)

    # Physically sampled weight n(k,E) = 4 pi k^2 P(k,E)   [MeV^-2]
    w = 4.0 * np.pi * (k[:, None] ** 2) * P              # [num_p, num_E]

    # Marginals (probability per MeV)
    f_E = (w * dk).sum(axis=0)        # removal-energy spectrum f(E) = sum_k 4pi k^2 P dk
    n_k = (w * dE).sum(axis=1)        # momentum spectrum     n(k) = sum_E 4pi k^2 P dE
    norm = float((w * dk * dE).sum()) # should be ~1
    print(f"normalization  sum 4pi k^2 P dk dE = {norm:.4f}")
    print(f"<E> = {np.average(E, weights=f_E):.1f} MeV   "
          f"<k> = {np.average(k, weights=n_k):.1f} MeV/c   "
          f"f(E) peak @ {E[f_E.argmax()]:.1f} MeV   n(k) peak @ {k[n_k.argmax()]:.0f} MeV/c")

    # ---- figure: 2D map + two marginals -------------------------------------
    w_in, h_in = PANEL_SIZE
    fig, axes = plt.subplots(1, 3, figsize=(w_in * 3.2, h_in), dpi=DPI)
    ax2d, axE, axk = axes

    # populated window for the 2D map
    Emax_plot, kmax_plot = 150.0, 500.0
    iE = E <= Emax_plot
    ik = k <= kmax_plot
    # bin edges for pcolormesh
    Eedges = np.concatenate([E[iE] - dE / 2, [E[iE][-1] + dE / 2]])
    kedges = np.concatenate([k[ik] - dk / 2, [k[ik][-1] + dk / 2]])
    Z = np.ma.masked_less_equal(w[np.ix_(ik, iE)], 0.0)

    vmax = Z.max()
    pc = ax2d.pcolormesh(Eedges, kedges, Z, cmap="viridis",
                        norm=LogNorm(vmin=vmax * 1e-5, vmax=vmax))
    cb = fig.colorbar(pc, ax=ax2d, pad=0.02)
    cb.set_label(r"$4\pi k^2\,P(k,E)$  [MeV$^{-2}$]", fontsize=FS_TITLE)
    ax2d.set_xlabel("missing energy  E  [MeV]", fontsize=FS_LABEL)
    ax2d.set_ylabel("missing momentum  k  [MeV/c]", fontsize=FS_LABEL)
    ax2d.set_title("Benhar SF  $P(k,E)$  (C12)", fontsize=FS_TITLE)

    # removal-energy marginal
    axE.step(E, f_E, where="mid", color="C0")
    style_axis(axE, title="removal-energy spectrum",
               xlabel="missing energy  E  [MeV]",
               ylabel=r"$f(E)=\int 4\pi k^2 P\,dk$  [MeV$^{-1}$]",
               logx=False, logy=False)
    axE.set_xlim(0, Emax_plot)
    axE.set_ylim(0, None)

    # momentum marginal
    axk.step(k, n_k, where="mid", color="C1")
    style_axis(axk, title="momentum distribution",
               xlabel="missing momentum  k  [MeV/c]",
               ylabel=r"$n(k)=\int 4\pi k^2 P\,dE$  [(MeV/c)$^{-1}$]",
               logx=False, logy=False)
    axk.set_xlim(0, kmax_plot)
    axk.set_ylim(0, None)

    fig.suptitle("C12 Benhar spectral function  (pke12_tot.data)", fontsize=FS_SUPTITLE)
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    out = Path("results/prd-analyzer-v0/spectral_function_c12.png")
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

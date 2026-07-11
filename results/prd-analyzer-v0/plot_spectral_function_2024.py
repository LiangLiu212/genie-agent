"""2024 Ankowski-Benhar-Sakuda C12 proton spectral function P(k,E).

Plots ./data/pke12_2024.table (Ankowski, Benhar & Sakuda, "Determination of the
proton spectral function of 12C from (e,e'p) data", suppl. material 2024-11-03)
in the (missing energy, missing momentum) plane, and overlays it against the
older pke12_tot.data already used by GENIE. The 2024 table fits the
high-resolution NIKHEF (e,e'p) data (Van der Steenhoven 1988) in the p-shell
region 13 < E < 21.5 MeV (0.025 MeV bins) and matches the Benhar model
(Saclay + nuclear matter) for 21.5 < E < 300 MeV (0.1 MeV bins).

File format (verified against suppl_mat_ankowski_et_al.pdf):
  line 1:  n_k  dk            -> 40  20.000   (momentum: 40 bins, 20 MeV wide)
  line 2:  n1 d1 n2 d2        -> 340 0.025 2785 0.100  (energy grid, two segments)
  body:    40 blocks; each = |k| then 3125 (E, P) pairs.
  P(|k|,E) in MeV^-4, normalised to Z=6 (int 4pi k^2 P dk dE = 6).

Personal plot style (results/template/plot_style.py).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "results/template")
from plot_style import (apply_style, style_axis, PANEL_SIZE, DPI,
                        FS_LABEL, FS_SUPTITLE, FS_TITLE, FS_LEGEND)

Z = 6  # C12 protons; both tables are normalised to the proton number


def load_2024(path):
    """Parse pke12_2024.table -> (k, E, P[ik,iE], dk, dE_vec, edges).

    P is per-proton density [MeV^-4]; dE_vec is the per-energy-bin width vector
    (0.025 in the fine segment, 0.1 in the coarse segment); edges is the
    non-uniform energy bin-edge array for pcolormesh.
    """
    tok = np.fromstring(path.read_text(), sep=" ")
    n_k, dk = int(tok[0]), tok[1]
    n1, d1, n2, d2 = int(tok[2]), tok[3], int(tok[4]), tok[5]
    n_E = n1 + n2
    block = 1 + 2 * n_E
    body = tok[6:6 + n_k * block].reshape(n_k, block)

    k = body[:, 0]                 # MeV/c
    E = body[0, 1::2]              # MeV (same grid every block)
    P = body[:, 2::2] / Z          # MeV^-4, per proton
    dE = np.concatenate([np.full(n1, d1), np.full(n2, d2)])

    # non-uniform energy bin edges (fine then coarse)
    e_lo = 13.0
    fine_edges = e_lo + np.arange(n1 + 1) * d1            # 13 .. 21.5
    coarse_edges = fine_edges[-1] + np.arange(1, n2 + 1) * d2  # 21.6.. 300
    edges = np.concatenate([fine_edges, coarse_edges])
    return k, E, P, dk, dE, edges


def load_old(path):
    """Parse the older pke12_tot.data (uniform 5 MeV E grid) -> (k, E, P, dk, dE)."""
    tok = np.fromstring(path.read_text(), sep=" ")
    num_E, num_p = int(tok[0]), int(tok[1])
    E_min, p_min, E_max, p_max = tok[2], tok[3], tok[4], tok[5]
    body = tok[6:6 + num_p * (1 + 2 * num_E)].reshape(num_p, 1 + 2 * num_E)
    k = body[:, 0]
    pairs = body[:, 1:].reshape(num_p, num_E, 2)
    E = pairs[0, :, 0]
    P = pairs[:, :, 1] / Z
    dk = (p_max - p_min) / num_p
    dE = (E_max - E_min) / num_E
    return k, E, P, dk, dE


def marginals(k, E, P, dk, dE):
    """Return f(E), n(k), normalization for a (per-proton) SF grid.

    dE may be a scalar (uniform) or a per-bin vector (non-uniform).
    """
    dE = np.asarray(dE)
    w = 4.0 * np.pi * (k[:, None] ** 2) * P      # [n_k, n_E], MeV^-2
    f_E = (w * dk).sum(axis=0)                   # sum over k
    n_k = (w * dE).sum(axis=1)                   # sum over E (vector dE ok)
    norm = float((w * dk * dE).sum())
    return f_E, n_k, norm


def main():
    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    new_path = Path("data/pke12_2024.table")
    old_path = Path("/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator/"
                    "data/evgen/nucl/spectral_functions/pke12_tot.data")

    print(f"reading {new_path}")
    k, E, P, dk, dE, edges = load_2024(new_path)
    f_E, n_k, norm = marginals(k, E, P, dk, dE)
    print(f"[2024] norm = {norm:.4f}   <E> = {np.average(E, weights=f_E):.1f} MeV   "
          f"f(E) peak @ {E[f_E.argmax()]:.2f} MeV   n(k) peak @ {k[n_k.argmax()]:.0f} MeV/c")

    # ---- Figure 1: 3-panel standalone ---------------------------------------
    w_in, h_in = PANEL_SIZE
    fig, (ax2d, axE, axk) = plt.subplots(1, 3, figsize=(w_in * 3.2, h_in), dpi=DPI)

    kmax_plot = 500.0
    ik = k <= kmax_plot
    kedges = np.concatenate([k[ik] - dk / 2, [k[ik][-1] + dk / 2]])
    wgrid = 4.0 * np.pi * (k[:, None] ** 2) * P
    Zc = np.ma.masked_less_equal(wgrid[ik, :], 0.0)
    vmax = Zc.max()
    pc = ax2d.pcolormesh(edges, kedges, Zc, cmap="viridis",
                        norm=LogNorm(vmin=vmax * 1e-6, vmax=vmax))
    cb = fig.colorbar(pc, ax=ax2d, pad=0.02)
    cb.set_label(r"$4\pi k^2\,P(k,E)$  [MeV$^{-2}$]", fontsize=FS_TITLE)
    ax2d.set_xlim(13, 300)
    ax2d.set_xlabel("missing energy  E  [MeV]", fontsize=FS_LABEL)
    ax2d.set_ylabel("missing momentum  k  [MeV/c]", fontsize=FS_LABEL)
    ax2d.set_title("Ankowski-Benhar-Sakuda 2024  $P(k,E)$  (C12)", fontsize=FS_TITLE)

    axE.step(E, f_E, where="mid", color="C0")
    style_axis(axE, title="removal-energy spectrum",
               xlabel="missing energy  E  [MeV]",
               ylabel=r"$f(E)=\int 4\pi k^2 P\,dk$  [MeV$^{-1}$]",
               logx=False, logy=False)
    axE.set_xlim(13, 300)
    axE.set_ylim(0, None)
    axE.axvline(21.5, color="0.6", ls="--", lw=1)  # fine/coarse segment boundary

    axk.step(k, n_k, where="mid", color="C1")
    style_axis(axk, title="momentum distribution",
               xlabel="missing momentum  k  [MeV/c]",
               ylabel=r"$n(k)=\int 4\pi k^2 P\,dE$  [(MeV/c)$^{-1}$]",
               logx=False, logy=False)
    axk.set_xlim(0, kmax_plot)
    axk.set_ylim(0, None)

    fig.suptitle("C12 proton spectral function  (pke12_2024.table)", fontsize=FS_SUPTITLE)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out1 = Path("results/prd-analyzer-v0/spectral_function_c12_2024.png")
    fig.savefig(out1, dpi=DPI, bbox_inches="tight")
    print(f"wrote {out1}")

    # ---- Figure 2: 2024 vs old overlay --------------------------------------
    print(f"reading {old_path}")
    ko, Eo, Po, dko, dEo = load_old(old_path)
    f_Eo, n_ko, normo = marginals(ko, Eo, Po, dko, dEo)
    print(f"[old ] norm = {normo:.4f}   <E> = {np.average(Eo, weights=f_Eo):.1f} MeV   "
          f"f(E) peak @ {Eo[f_Eo.argmax()]:.1f} MeV   n(k) peak @ {ko[n_ko.argmax()]:.0f} MeV/c")

    fig2, (cE, ck) = plt.subplots(1, 2, figsize=(w_in * 2.2, h_in), dpi=DPI)

    cE.step(Eo, f_Eo, where="mid", color="0.5", lw=1.6, label="pke12_tot (old)")
    cE.step(E, f_E, where="mid", color="C3", lw=1.8, label="2024 (NIKHEF fit)")
    for xb in (13.0, 21.5):
        cE.axvline(xb, color="0.7", ls=":", lw=1)
    style_axis(cE, title=r"removal-energy spectrum  $f(E)$",
               xlabel="missing energy  E  [MeV]",
               ylabel=r"$f(E)$  [MeV$^{-1}$]", logx=False, logy=False)
    cE.set_xlim(13, 80)
    cE.set_ylim(0, None)
    cE.legend(fontsize=FS_LEGEND)

    ck.step(ko, n_ko, where="mid", color="0.5", lw=1.6, label="pke12_tot (old)")
    ck.step(k, n_k, where="mid", color="C3", lw=1.8, label="2024")
    style_axis(ck, title=r"momentum distribution  $n(k)$",
               xlabel="missing momentum  k  [MeV/c]",
               ylabel=r"$n(k)$  [(MeV/c)$^{-1}$]", logx=False, logy=False)
    ck.set_xlim(0, kmax_plot)
    ck.set_ylim(0, None)
    ck.legend(fontsize=FS_LEGEND)

    fig2.suptitle("C12 proton SF: 2024 (Ankowski-Benhar-Sakuda) vs old pke12_tot",
                  fontsize=FS_SUPTITLE)
    fig2.tight_layout(rect=(0, 0, 1, 0.95))
    out2 = Path("results/prd-analyzer-v0/spectral_function_c12_2024_vs_old.png")
    fig2.savefig(out2, dpi=DPI, bbox_inches="tight")
    print(f"wrote {out2}")


if __name__ == "__main__":
    main()

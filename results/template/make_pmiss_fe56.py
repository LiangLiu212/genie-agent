"""Fe56 1D missing momentum: input table vs the QEL struck nucleon (record).

Plot 4 of the electron-Fe56 series: the momentum companion of the restored
E_miss ladder. Unlike the removal energy (dropped by FermiMover for the
a-tunes), the struck-nucleon 3-momentum survives into the record for every
tune, so the record |p_n| distribution is meaningful for all four:

  - table curve: occupancy-scale k-marginal of pke56_tot.data,
        n(k) = Z * int 4pi k^2 P dE   (full E integral)  [ (MeV/c)^-1 ]
  - per tune: Z * hist(|p_n|) / (N_sel * dk) from the QEL struck-nucleon
    record (same caches as make_emiss_ladder_fe56.py: qel && hitnuc==2212,
    no other cuts).

Binning: the table's NATIVE k grid (20 MeV/c bins, edges 0..800 MeV/c) for
both curves -- no rebinning, no half-bin artifact (cf. the E_miss lesson).
Expected: 22a/22b sit on the table up to UnifiedQEL/Rosenbluth xsec weighting
and the Q^2 >= 1.18 acceptance; 11a/GEM21 show the LFG distribution (cut off
at the local Fermi momentum, no SRC tail).

Usage:
  pixi run python results/template/make_pmiss_fe56.py
Requires the ladder caches (run make_emiss_ladder_fe56.py --all-tunes first).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO / "results/prd-analyzer-v0.1/cache/ladder_fe56"
OUT = REPO / "results/prd-analyzer-v0.1/pmiss_struck_fe56_t05.png"

TUNES = {                             # tune -> (color, linestyle, ground state)
    "GEM26_11a_05_000": ("C0", "-",  "LocalFGM"),
    "GEM26_22a_05_000": ("C2", "-",  "SF"),
    "GEM26_22b_05_000": ("C3", "-",  "SF"),
    "GEM21_11a_05_000": ("C4", "--", "LocalFGM"),
}
Z = 26

# ---- table k-marginal on its native grid ------------------------------------------
k, E, k_edges, E_edges, S = read_pke_table(
    resolve_sf_table("GEM26_22a_05_000", 1000260560, 2212))
dk = float(np.diff(k_edges).mean())
dE = float(np.diff(E_edges).mean())
raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
P = S * (Z / raw) / Z                 # per-proton density (norm verified = 25.998)
n_k = Z * (4.0 * np.pi * (k[:, None] ** 2) * P * dE).sum(axis=1)  # [(MeV/c)^-1]
print(f"table n(k): full integral {float((n_k * dk).sum()):.3f} (= Z), "
      f"grid {len(k)} bins x {dk:.0f} MeV/c")

apply_style()
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8.5, 5.5), layout="constrained")
ax.stairs(n_k, k_edges, color="black", linewidth=2.6, linestyle="--", zorder=3,
          label="Benhar SF pke56_tot (22a/22b input)")

for tune, (color, ls, gs) in TUNES.items():
    c = np.load(CACHE_DIR / f"{tune}.npz")
    p2, n_sel = c["p2"], float(c["n_sel"][0])
    cnt, _ = np.histogram(p2, bins=k_edges)
    y = Z * cnt / (n_sel * dk)
    I = float((y * dk).sum())
    med = float(np.median(p2))
    print(f"{tune}: N_sel={int(n_sel):,}  integral {I:.3f}  "
          f"median |p_n| {med:.1f} MeV/c  P(p>250)={float(np.mean(p2 > 250)):.3f}")
    ax.stairs(y, k_edges, color=color, linewidth=1.8, linestyle=ls, zorder=5,
              label=f"{tune}  ({gs})")

style_axis(ax, title="QEL struck nucleon (record) vs input table",
           xlabel=r"$P_{\rm miss}$  [MeV/c]", logx=False, logy=True, ymin=None)
ax.set_xlim(0, 800)
ax.set_ylim(1e-6, 0.4)
ax.set_ylabel(r"$Z\cdot$ d$N/$d$P_{\rm miss}\,/\,N_{sel}$   [(MeV/c)$^{-1}$]",
              fontsize=FS_LABEL)
ax.annotate("22a $\\approx$ table (FermiMover samples k\nunweighted); 22b tail "
            "xsec-suppressed;\nLFG cut off at local $k_F$",
            xy=(0.40, 0.55), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
            color="0.35")
ax.legend(fontsize=FS_LEGEND - 4, title="qel && hit p, no cuts; 20 MeV/c bins",
          title_fontsize=FS_LEGEND_TITLE - 4, loc="upper right")
fig.suptitle("Fe56 $P_{\\rm miss}$ — table vs QEL struck-nucleon record\n"
             "e$^-$ 2.445 GeV, t05 tunes, occupancy scale (full integral = Z)",
             fontsize=FS_SUPTITLE - 3)
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

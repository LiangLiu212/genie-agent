"""C12 1D missing momentum: input table vs the QEL struck nucleon (record).

C12 sibling of make_pmiss_fe56.py for electron_c12_scattering.md. Reads the
surviving prd-analyzer-v0.1 ladder caches (the June-2026 C12 EMQE samples are
purged from scratch dCache; see make_emiss_ladder_c12.py for provenance and
the model-key -> tune mapping). Both curves on the pke12_tot native 20 MeV/c
grid, occupancy scale (full integral = Z = 6).

Usage: pixi run python results/template/make_pmiss_c12.py
"""
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_TITLE,
                        FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO / "results/prd-analyzer-v0.1/cache/ladder"
OUT = REPO / "results/prd-analyzer-v0.1/pmiss_struck_c12_t05.png"

TUNES = {   # tune -> (cache model key, color, linestyle, ground state)
    "GEM26_11a_05_000": ("LFG",        "C0", "-",  "LocalFGM"),
    "GEM26_22a_05_000": ("SF",         "C2", "-",  "SF"),
    "GEM26_22b_05_000": ("UnifiedQEL", "C3", "-",  "SF"),
    "GEM21_11a_05_000": ("SuSAv2",     "C4", "--", "LocalFGM"),
}
Z = 6

k, E, k_edges, E_edges, S = read_pke_table(
    resolve_sf_table("GEM26_22a_05_000", 1000060120, 2212))
dk = float(np.diff(k_edges).mean())
dE = float(np.diff(E_edges).mean())
raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
P = S * (Z / raw) / Z
n_k = Z * (4.0 * np.pi * (k[:, None] ** 2) * P * dE).sum(axis=1)
print(f"table n(k): full integral {float((n_k * dk).sum()):.3f} (= Z), "
      f"grid {len(k)} bins x {dk:.0f} MeV/c")

apply_style()
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8.5, 5.5), layout="constrained")
ax.stairs(n_k, k_edges, color="black", linewidth=2.6, linestyle="--", zorder=3,
          label="Benhar SF pke12_tot (22a/22b input)")

for tune, (model, color, ls, gs) in TUNES.items():
    c = np.load(CACHE_DIR / f"{model}.npz")
    p2, n_sel = c["p2"], float(c["n_hitp"][0])
    cnt, _ = np.histogram(p2, bins=k_edges)
    y = Z * cnt / (n_sel * dk)
    print(f"{tune}: N_sel={int(n_sel):,}  integral {float((y * dk).sum()):.3f}  "
          f"median |p_n| {float(np.median(p2)):.1f} MeV/c  "
          f"P(p>250)={float(np.mean(p2 > 250)):.3f}")
    ax.stairs(y, k_edges, color=color, linewidth=1.8, linestyle=ls, zorder=5,
              label=f"{tune}  ({gs})")

style_axis(ax, title="QEL struck nucleon (record) vs input table",
           xlabel=r"$P_{\rm miss}$  [MeV/c]", logx=False, logy=True, ymin=None)
ax.set_xlim(0, 800)
ax.set_ylim(1e-7, 0.1)
ax.set_ylabel(r"$Z\cdot$ d$N/$d$P_{\rm miss}\,/\,N_{sel}$   [(MeV/c)$^{-1}$]",
              fontsize=FS_LABEL)
ax.annotate("22a $\\approx$ table (FermiMover samples k\nunweighted); 22b tail "
            "xsec-suppressed;\nLFG cut off at local $k_F$",
            xy=(0.40, 0.55), xycoords="axes fraction", fontsize=FS_LEGEND - 3,
            color="0.35")
ax.legend(fontsize=FS_LEGEND - 4, title="EMQE, hit p, no cuts; 20 MeV/c bins",
          title_fontsize=FS_LEGEND_TITLE - 4, loc="upper right")
fig.suptitle("C12 $P_{\\rm miss}$ — table vs QEL struck-nucleon record\n"
             "e$^-$ 2.445 GeV, t05 tunes, occupancy scale (full integral = Z)",
             fontsize=FS_SUPTITLE - 3)
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

"""v0.2 1D missing momentum with the Dutta Q^2 cut: table vs struck-nucleon record.

Target-parameterized counterpart of make_pmiss_fe56.py / make_pmiss_c12.py for
prd-analyzer-v0.2: the occupancy-scale table k-marginal against the QEL
struck-nucleon record |p_n|, with the record now from the WINDOWED selection

    qel && hitnuc==2212 && |Q^2/1.28 - 1| <= 5 %

(reads the v0.2 ladder caches built by make_emiss_ladder_q2cut.py — run that
first). The table curve is selection-independent (theory input, full E
integral); differences vs the v0.1 figures isolate what the Q^2 slice does to
the sampled-momentum acceptance.

Binning: the table's NATIVE k grid (20 MeV/c). Figure:
results/prd-analyzer-v0.2/pmiss_struck_<target>_t05.png.

Usage:
  pixi run python results/template/make_pmiss_q2cut.py --target Fe56
  pixi run python results/template/make_pmiss_q2cut.py --target C12
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"

TUNES = {                             # tune -> (color, linestyle, ground state)
    "GEM26_11a_05_000": ("C0", "-",  "LocalFGM"),
    "GEM26_22a_05_000": ("C2", "-",  "SF"),
    "GEM26_22b_05_000": ("C3", "-",  "SF"),
    "GEM21_11a_05_000": ("C4", "--", "LocalFGM"),
}
TGT = {"Fe56": dict(Z=26, tgt_pdg=1000260560),
       "C12":  dict(Z=6,  tgt_pdg=1000060120)}


def main(target):
    cfg = TGT[target]
    Z = cfg["Z"]
    tlow = target.lower()
    cache_dir = CACHE_ROOT / f"ladder_{tlow}"

    table_path = resolve_sf_table("GEM26_22a_05_000", cfg["tgt_pdg"], 2212)
    k, E, k_edges, E_edges, S = read_pke_table(table_path)
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
    ax.stairs(n_k, k_edges, color="black", linewidth=2.6, linestyle="--",
              zorder=3, label=f"Benhar SF {table_path.stem} (22a/22b input)")

    for tune, (color, ls, gs) in TUNES.items():
        c = np.load(cache_dir / f"{tune}.npz")
        p2, n_sel = c["p2"], float(c["n_sel"][0])
        cnt, _ = np.histogram(p2, bins=k_edges)
        y = Z * cnt / (n_sel * dk)
        I = float((y * dk).sum())
        med = float(np.median(p2))
        print(f"{tune}: N_sel={int(n_sel):,}  integral {I:.3f}  "
              f"median |p_n| {med:.1f} MeV/c  "
              f"P(p>250)={float(np.mean(p2 > 250)):.3f}")
        ax.stairs(y, k_edges, color=color, linewidth=1.8, linestyle=ls,
                  zorder=5, label=f"{tune}  ({gs})")

    style_axis(ax, title="QEL struck nucleon (record) vs input table",
               xlabel=r"$P_{\rm miss}$  [MeV/c]", logx=False, logy=True,
               ymin=None)
    ax.set_xlim(0, 800)
    ax.set_ylim(1e-6, 0.4)
    ax.set_ylabel(r"$Z\cdot$ d$N/$d$P_{\rm miss}\,/\,N_{sel}$   [(MeV/c)$^{-1}$]",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 4,
              title="qel && hit p && $Q^2=1.28\\pm5\\%$; 20 MeV/c bins",
              title_fontsize=FS_LEGEND_TITLE - 4, loc="upper right")
    fig.suptitle(f"{target} $P_{{\\rm miss}}$ — table vs QEL struck-nucleon "
                 "record, $Q^2$ slice applied\n"
                 "e$^-$ 2.445 GeV, t05 tunes, occupancy scale "
                 "(table integral = Z)",
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"pmiss_struck_{tlow}_t05.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TGT))
    main(ap.parse_args().target)

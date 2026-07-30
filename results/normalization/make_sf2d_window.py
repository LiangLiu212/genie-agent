"""2D input tables with the Dutta E91-013 phase space marked in red.

One panel per Dutta-relevant table (pke12_tot, pke12_2024, pke56_tot):
the sampled density 4*pi*k^2*P(k,E) over the table's full native grid
(log color, same style as make_sf2d_all.py), with the measured window
E_m < 80 MeV, |p_m| < 300 MeV/c drawn as a red boundary and the in-window
strength fraction (from integrate_all_pke.windowed_integral) annotated.

Usage:
  pixi run python results/normalization/make_sf2d_window.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))
sys.path.insert(0, str(HERE))

import numpy as np
from plot_style import (apply_style, FS_LABEL, FS_TITLE, FS_TICK,
                        FS_SUPTITLE, PANEL_SIZE, DPI)          # noqa: E402
from integrate_all_pke import (default_data_dir, parse_table, integral,
                               windowed_integral, EXPECTED)    # noqa: E402

E_MAX, K_MAX = 80.0, 300.0             # the Dutta window


def main():
    data_dir = default_data_dir()
    names = ["pke12_tot.data", "pke12_2024.table", "pke56_tot.data"]

    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, 3, figsize=(w * 3.4, h), sharey=False,
                             layout="constrained")
    for ax, name in zip(axes, names):
        res = parse_table(data_dir / name)
        k, P, k_edges, E_edges, dk_w, dE_w, _ = res
        I = integral(k, P, dk_w, dE_w)
        Iw = windowed_integral(k, P, k_edges, E_edges,
                               (0.0, K_MAX), (0.0, E_MAX))
        D = 4.0 * np.pi * k[:, None] ** 2 * P
        Xe, Ye = np.meshgrid(k_edges, E_edges, indexing="ij")
        Dm = np.ma.masked_less_equal(D, 0.0)
        norm = LogNorm(vmin=Dm.max() * 1e-6, vmax=Dm.max())
        pc = ax.pcolormesh(Xe, Ye, Dm, cmap="viridis", norm=norm)
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)

        # Dutta window boundary: the grids start at (0, ~0), so the visible
        # boundary is the L of k = 300 (E < 80) and E = 80 (k < 300)
        ax.plot([K_MAX, K_MAX], [E_edges[0], E_MAX], color="red", lw=2.5)
        ax.plot([k_edges[0], K_MAX], [E_MAX, E_MAX], color="red", lw=2.5)
        ax.text(K_MAX + 15, E_MAX + 8,
                f"Dutta window\n{Iw / I:.1%} of strength",
                color="red", fontsize=FS_TICK + 1, va="bottom")

        species, _ = EXPECTED[name]
        ax.set_title(f"{name}  ({species})", fontsize=FS_TITLE - 2)
        ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
        ax.tick_params(labelsize=FS_TICK)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)

    fig.suptitle("Input tables, sampled density $4\\pi P_{\\rm miss}^2 P$ -- "
                 "Dutta E91-013 phase space in red "
                 r"($E_m$ < 80 MeV, $|p_m|$ < 300 MeV/c)",
                 fontsize=FS_SUPTITLE - 2)
    out = HERE / "sf2d_dutta_window.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

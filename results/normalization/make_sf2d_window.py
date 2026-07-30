"""2D input tables with the Dutta E91-013 phase space marked in red.

One panel per Dutta-relevant table (pke12_tot, pke12_2024, pke56_tot):
the sampled density 4*pi*k^2*P(k,E) over the table's full native grid
(log color, same style as make_sf2d_all.py), with the measured windows
drawn as red boxes and each in-window strength fraction annotated
(integrate_all_pke.windowed_integral):

  C12 panels : the fig 6 shell windows -- p-shell 10 < E_m < 25 MeV and
               s-shell 30 < E_m < 50 MeV, both with |p_m| < 300 MeV/c
  Fe56 panel : the full window E_m < 80 MeV, |p_m| < 300 MeV/c

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

K_MAX = 300.0                          # the Dutta |p_m| window
SHELLS = [((10.0, 25.0), "p-shell"), ((30.0, 50.0), "s-shell")]
FULL = [((0.0, 80.0), "Dutta window")]
WINDOWS = {"pke12_tot.data": SHELLS, "pke12_2024.table": SHELLS,
           "pke56_tot.data": FULL}


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
        D = 4.0 * np.pi * k[:, None] ** 2 * P
        Xe, Ye = np.meshgrid(k_edges, E_edges, indexing="ij")
        Dm = np.ma.masked_less_equal(D, 0.0)
        norm = LogNorm(vmin=Dm.max() * 1e-6, vmax=Dm.max())
        pc = ax.pcolormesh(Xe, Ye, Dm, cmap="viridis", norm=norm)
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)

        from matplotlib.patches import Rectangle
        for (E_lo, E_hi), label in WINDOWS[name]:
            Iw = windowed_integral(k, P, k_edges, E_edges,
                                   (0.0, K_MAX), (E_lo, E_hi))
            ax.add_patch(Rectangle((0.0, E_lo), K_MAX, E_hi - E_lo,
                                   fill=False, edgecolor="red", lw=2.5,
                                   zorder=5))
            ax.text(K_MAX + 15, 0.5 * (E_lo + E_hi),
                    f"{label}  {Iw / I:.1%}",
                    color="red", fontsize=FS_TICK + 1, va="center")
        ax.set_ylim(0, E_edges[-1])

        species, _ = EXPECTED[name]
        ax.set_title(f"{name}  ({species})", fontsize=FS_TITLE - 2)
        ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
        ax.tick_params(labelsize=FS_TICK)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)

    fig.suptitle("Input tables, sampled density $4\\pi P_{\\rm miss}^2 P$ -- "
                 "Dutta E91-013 phase space in red\n"
                 r"C12: fig 6 shell windows ($E_m$ 10-25 / 30-50 MeV); "
                 r"Fe56: $E_m$ < 80 MeV; all with $|p_m|$ < 300 MeV/c",
                 fontsize=FS_SUPTITLE - 2)
    out = HERE / "sf2d_dutta_window.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

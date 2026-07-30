"""2D views of every pke* spectral-function table (companions to the
normalization integrals in this folder's README).

One figure per table, same orientation and style as
results/template/make_sf2d_table.py (x = P_miss, y = E_miss, viridis, log
color over 6 decades):

  left  = P(P_miss, E_miss) as tabulated          [MeV^-4, N*P convention]
  right = 4*pi*P_miss^2*P / I, area-normalized    (the sampled density)

The right panel divides by this table's integral I and carries no bin-width
factor, so it is grid-independent: pke12_2024.table and its non-uniform
.origin render identically -- the visual counterpart of the lossless-
conversion check.

Usage:
  pixi run python results/normalization/make_sf2d_all.py [data_dir]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))
sys.path.insert(0, str(HERE))

import numpy as np
from plot_style import (apply_style, FS_LABEL, FS_TITLE, FS_TICK,
                        FS_SUPTITLE, PANEL_SIZE, DPI)          # noqa: E402
from integrate_all_pke import (default_data_dir, parse_table,
                               integral, EXPECTED)             # noqa: E402


def out_name(fname: str) -> str:
    stem = (fname.replace(".table.origin", "_origin")
                 .replace(".table", "").replace(".data", ""))
    return f"sf2d_{stem}.png"


def make_figure(path: Path) -> None:
    res = parse_table(path)
    if res is None:
        print(f"{path.name}: UNRECOGNIZED FORMAT -- skipped")
        return
    k, P, k_edges, E_edges, dk_w, dE_w, grid = res
    I = integral(k, P, dk_w, dE_w)
    species, n_exp = EXPECTED.get(path.name, ("?", None))
    D = 4.0 * np.pi * k[:, None] ** 2 * P / I

    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, 2, figsize=(w * 2.4, h), sharey=True,
                             layout="constrained")
    Xe, Ye = np.meshgrid(k_edges, E_edges, indexing="ij")
    panels = [
        (P, r"table density  P($P_{\rm miss}$, $E_{\rm miss}$)  [MeV$^{-4}$]"),
        (D, r"sampled density  4$\pi P_{\rm miss}^2\,P\,/\,I$  (norm.)"),
    ]
    for ax, (Z, label) in zip(axes, panels):
        Zm = np.ma.masked_less_equal(Z, 0.0)
        norm = LogNorm(vmin=Zm.max() * 1e-6, vmax=Zm.max())
        pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
        ax.set_title(label, fontsize=FS_TITLE - 2)
        ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
        ax.tick_params(labelsize=FS_TICK)
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)

    expect = f"  (expect {n_exp})" if n_exp else ""
    fig.suptitle(f"{path.name}  --  {species} spectral function\n"
                 rf"$\int 4\pi k^2 P\,dk\,dE$ = {I:.6f}{expect}",
                 fontsize=FS_SUPTITLE - 2)
    out = HERE / out_name(path.name)
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"wrote {out.name}   I={I:.6f}   {grid}")


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_data_dir()
    for f in sorted(data_dir.glob("pke*")):
        if f.suffix == ".py" or f.is_dir():
            continue
        make_figure(f)

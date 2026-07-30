"""Marginal profiles of every pke* spectral-function table.

Three panels, all tables overlaid, each normalized per nucleon (/I with I the
table integral from integrate_all_pke.py, so every curve integrates to 1):

  left   = f(E_miss) = int 4*pi*k^2 P dk / I    [MeV^-1], full range
  middle = the same, zoomed to E_miss < 60 MeV (the shell structure)
  right  = n(P_miss) = int 4*pi*k^2 P dE / I    [(MeV/c)^-1]

pke12_2024.table.origin is drawn dashed in the same color as the converted
pke12_2024.table: both marginals are invariant under the lossless rebinning,
so the dashed curve sits exactly on the solid one. Non-positive values are
clamped to the log floor (not physical).

Usage:
  pixi run python results/normalization/make_sf_profiles.py [data_dir]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))
sys.path.insert(0, str(HERE))

import numpy as np
from plot_style import (apply_style, new_panels, style_axis, FLOOR,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE,
                        FS_SUPTITLE, DPI)                      # noqa: E402
from integrate_all_pke import (default_data_dir, parse_table,
                               integral, EXPECTED)             # noqa: E402

# (filename, color, linestyle) -- origin dashed over its converted twin
SERIES = [
    ("pke12_tot.data",          "C0", "-"),
    ("pke12_2024.table",        "C1", "-"),
    ("pke12_2024.table.origin", "C1", "--"),
    ("pke16_tot.data",          "C2", "-"),
    ("pke40p_tot.data",         "C3", "-"),
    ("pke40n_tot.data",         "C4", "-"),
    ("pke56_tot.data",          "C5", "-"),
]


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_data_dir()
    apply_style()
    fig, (ax_E, ax_Ez, ax_k) = new_panels(ncols=3, sharey=False)

    for fname, color, ls in SERIES:
        path = data_dir / fname
        if not path.exists():
            print(f"{fname}: missing -- skipped")
            continue
        k, P, k_edges, E_edges, dk_w, dE_w, _ = parse_table(path)
        I = integral(k, P, dk_w, dE_w)
        w = 4.0 * np.pi * k[:, None] ** 2 * P / I
        f_E = (w * dk_w[:, None]).sum(axis=0)          # density in E [MeV^-1]
        n_k = (w * dE_w[None, :]).sum(axis=1)          # density in k [(MeV/c)^-1]
        E_c = 0.5 * (E_edges[:-1] + E_edges[1:])
        species = EXPECTED[fname][0]
        label = (fname.replace(".data", "").replace(".table", "")
                 .replace(".origin", " origin") + f"  ({species})")
        ax_E.plot(E_c, np.maximum(f_E, FLOOR), ls, color=color, label=label)
        ax_Ez.plot(E_c, np.maximum(f_E, FLOOR), ls, color=color)
        ax_k.plot(k, np.maximum(n_k, FLOOR), ls, color=color)
        print(f"{fname:26s} f(E) peak @ {E_c[f_E.argmax()]:8.4f} MeV   "
              f"n(k) peak @ {k[n_k.argmax()]:4.0f} MeV/c")

    style_axis(ax_E, logx=False, xlabel=r"$E_{\rm miss}$  [MeV]",
               ylabel=r"$f(E_{\rm miss}) = \int 4\pi k^2 P\,dk\,/\,I$   [MeV$^{-1}$]")
    style_axis(ax_Ez, logx=False, title="shell region",
               xlabel=r"$E_{\rm miss}$  [MeV]")
    ax_Ez.set_xlim(0, 60)
    style_axis(ax_k, logx=False, xlabel=r"$P_{\rm miss}$  [MeV/c]",
               ylabel=r"$n(P_{\rm miss}) = \int 4\pi k^2 P\,dE\,/\,I$   [(MeV/c)$^{-1}$]")
    ax_E.legend(title="SF table", fontsize=FS_LEGEND - 2,
                title_fontsize=FS_LEGEND_TITLE)
    fig.suptitle("pke SF table marginals, per nucleon (each curve integrates to 1)",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    out = HERE / "sf_profiles.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

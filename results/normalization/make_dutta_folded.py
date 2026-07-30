"""Folded |p_m| comparison: Dutta p_m data with left+right summed, overlaid
on the input tables.

The signed-axis p_m files tabulate HALF the |p_m| density on each side:
summing the two sides makes the iron fig 7 strength equal the fig 11 E_m
spectrum strength to 0.03% (2 x 9.1029 = 18.206 vs 18.200) -- same
measurement, same published scale. So the folded data compare DIRECTLY to
the table window density int_window P dE, with no factor-2 convention gap.

Panels (|p_m| axis, native 20-MeV/c table steps, log y):
  C12 p-shell (10-25 MeV) and s-shell (30-50 MeV) vs pke12_tot/pke12_2024,
  Fe56 (E_m < 80 MeV) vs pke56_tot.

Data: Q^2 = 1.28 files; folded value = y(+p)+y(-p) = 2 y(+p) (the files are
exactly symmetrized), error drawn as 2 x col-4 (the sides are duplicated,
not independent). Annotated ratios are folded-data/table strengths
(4pi p^2-weighted, |p_m| < 320 MeV/c).

Usage:
  pixi run python results/normalization/make_dutta_folded.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "results" / "template"))
sys.path.insert(0, str(HERE))

import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LEGEND, FS_TICK, FS_SUPTITLE, DPI)  # noqa: E402
from integrate_all_pke import default_data_dir, parse_table    # noqa: E402
from make_dutta_overlay import load_dutta, pm_native, pm_strength  # noqa: E402


def main():
    data_dir = default_data_dir()
    tables = {name: parse_table(data_dir / name) for name in
              ["pke12_tot.data", "pke12_2024.table", "pke56_tot.data"]}
    C12 = [("pke12_tot", tables["pke12_tot.data"], "C0"),
           ("pke12_2024", tables["pke12_2024.table"], "C1")]
    FE = [("pke56_tot", tables["pke56_tot.data"], "C2")]

    apply_style()
    fig, (ax_p, ax_s, ax_fe) = new_panels(ncols=3, sharey=False)

    for ax, stem, tabs, E_win, title, extra in [
        (ax_p, "fig6_top_q1p2", C12, (10.0, 25.0),
         "C12 p-shell (10-25 MeV)", ""),
        (ax_s, "fig6_bot_q1p2", C12, (30.0, 50.0),
         "C12 s-shell (30-50 MeV)", ""),
        (ax_fe, "fig7_q1p2", FE, (0.0, 80.0),
         r"Fe56 ($E_m$ < 80 MeV)",
         "\n" + r"2$\times$fig7 $\equiv$ fig11 (0.03%)"),
    ]:
        x, y, e = load_dutta(stem)
        m = x > 0
        s_data = 2.0 * 4.0 * np.pi * (y[m] * x[m] ** 2).sum() * 40.0
        ratios = []
        for name, res, color in tabs:
            ratios.append(f"{s_data / pm_strength(res, E_win):.2f}")
            nk, edges = pm_native(res, E_win)
            ax.stairs(nk, edges, color=color, lw=2.0, zorder=4, label=name)
        ax.errorbar(x[m], 2.0 * y[m], yerr=2.0 * e[m], fmt="s", ms=5,
                    color="black", capsize=2, zorder=9, label="Dutta L+R")
        ax.text(0.03, 0.03, f"folded data/table = {', '.join(ratios)}{extra}",
                transform=ax.transAxes, va="bottom", fontsize=FS_TICK)
        style_axis(ax, title=title, xlabel=r"$|p_m|$  [MeV/c]",
                   ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]"
                   if ax is ax_p else None,
                   logx=False, ymin=None)
        ax.set_xlim(0, 330)
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="upper right")

    fig.suptitle("Dutta p_m data folded (left+right summed) vs input tables, "
                 r"$Q^2$ = 1.28"
                 "\nfolded data = full $|p_m|$ density -- same scale as the "
                 "fig 9/11 $E_m$ spectra; tables at native N$\\cdot$P scale",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = HERE / "dutta_folded_pm.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

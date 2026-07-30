"""Combined view: E_m spectra AND folded |p_m| distributions vs the input
tables, one row per nucleus.

Top row (C12):  E_m spectrum vs fig 9   | folded p-shell vs fig 6 top
                                        | folded s-shell vs fig 6 bot
Bottom (Fe56):  E_m spectrum vs fig 11  | folded (E_m < 80) vs fig 7

Same conventions as make_dutta_overlay.py (E_m panels: tables bin-averaged
into the data's 5-MeV bins, k < 300, thin clipped curve = native 2024
structure, grey bars = stat + 2% + 5% with the fig 9 published-bar
overrides) and make_dutta_folded.py (p_m panels: folded data = y(+p)+y(-p),
error 2x stat, tables on their native 20-MeV/c grid). With the fold, all
five panels sit on one scale family: C12 = 1.06-1.16 x table, Fe56 = 0.80.

Usage:
  pixi run python results/normalization/make_dutta_em_folded.py
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
from make_dutta_overlay import (load_dutta, em_profile, em_native,
                                em_strength, pm_native, pm_strength,
                                E_BINS)                        # noqa: E402


def main():
    data_dir = default_data_dir()
    tables = {name: parse_table(data_dir / name) for name in
              ["pke12_tot.data", "pke12_2024.table", "pke56_tot.data"]}
    C12 = [("pke12_tot", tables["pke12_tot.data"], "C0"),
           ("pke12_2024", tables["pke12_2024.table"], "C1")]
    FE = [("pke56_tot", tables["pke56_tot.data"], "C2")]

    apply_style()
    fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
    ax_em_c, ax_psh, ax_ssh, ax_em_fe, ax_pm_fe, ax_off = axes
    ax_off.set_visible(False)

    # ---- E_m spectra (data binning, k < 300) ---------------------------------
    for ax, stem, tabs, bars, ymax, title in [
        (ax_em_c, "fig9_q1p2", C12, {17.5: 0.081, 22.5: 0.047}, 0.7,
         r"C12 $E_m$ spectrum vs fig 9"),
        (ax_em_fe, "fig11_q1p2", FE, {}, None,
         r"Fe56 $E_m$ spectrum vs fig 11"),
    ]:
        x, y, e = load_dutta(stem)
        tot = np.sqrt(e ** 2 + (0.02 * y) ** 2 + (0.05 * y) ** 2)
        for em, frac in bars.items():
            tot[np.isclose(x, em)] = frac * y[np.isclose(x, em)]
        ratios = []
        for name, res, color in tabs:
            v = em_profile(res, E_BINS)
            ax.stairs(v, E_BINS, color=color, lw=2.0, zorder=4, label=name)
            ratios.append(f"{(y.sum() * 5.0) / em_strength(res):.2f}")
        if stem == "fig9_q1p2":
            fE, edges = em_native(tables["pke12_2024.table"])
            E_c = 0.5 * (edges[:-1] + edges[1:])
            m = E_c <= 85.0
            ax.plot(E_c[m], fE[m], color="C1", lw=1.0, alpha=0.5, zorder=3)
        ax.errorbar(x, y, yerr=tot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(x, y, yerr=e, fmt="s", ms=5, color="black", capsize=2,
                    zorder=9, label="Dutta data")
        ax.text(0.35, 0.97, f"data/table = {', '.join(ratios)}",
                transform=ax.transAxes, va="top", fontsize=FS_TICK)
        style_axis(ax, title=title, xlabel=r"$E_m$  [MeV]",
                   ylabel=r"$\int_{k<300} 4\pi k^2 P\,dk$   [MeV$^{-1}$]",
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 85)
        ax.set_ylim(0, ymax)
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="center right")

    # ---- folded |p_m| (native table grid) ------------------------------------
    for ax, stem, tabs, E_win, title, extra in [
        (ax_psh, "fig6_top_q1p2", C12, (10.0, 25.0),
         "C12 folded p-shell (10-25 MeV)", ""),
        (ax_ssh, "fig6_bot_q1p2", C12, (30.0, 50.0),
         "C12 folded s-shell (30-50 MeV)", ""),
        (ax_pm_fe, "fig7_q1p2", FE, (0.0, 80.0),
         r"Fe56 folded ($E_m$ < 80 MeV)",
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
        ax.text(0.03, 0.03, f"data/table = {', '.join(ratios)}{extra}",
                transform=ax.transAxes, va="bottom", fontsize=FS_TICK)
        style_axis(ax, title=title, xlabel=r"$|p_m|$  [MeV/c]",
                   ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                   logx=False, ymin=None)
        ax.set_xlim(0, 330)
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="upper right")

    fig.suptitle("Dutta E91-013 vs GENIE input tables, $Q^2$ = 1.28 -- "
                 r"$E_m$ spectra and folded $|p_m|$ together"
                 "\none scale family: C12 data = 1.06-1.16 $\\times$ table, "
                 r"Fe56 = 0.80 $\times$ table, in every projection",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = HERE / "dutta_em_folded_pm.png"
    fig.savefig(out, dpi=DPI)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    main()

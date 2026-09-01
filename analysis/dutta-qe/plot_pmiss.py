"""Stage 2: p_miss figures per target/tune, vs the folded Dutta figs 6/7.

Three figures per tune (E_m windows matched to the data: Fe56 E_m < 80 MeV,
C12 the fig 6 shell windows 10-25 (+) 30-50 MeV):

  out/pmiss_ladder_<target>_<tune>.png
      four-stage occupancy ladder in |p_m| (native 20 MeV/c bins):
      1 input table n_win(k), 2 record |p_n|, 3 pre-FSI |p_p - q|,
      4 post-FSI (N_p = 1); folded data weighted 4pi p_m^2 onto the
      occupancy axis. Stage 2 also shows the unwindowed record (dotted).

  out/pmiss_density_<target>_<tune>.png
      the same stages in the Dutta files' NATIVE units int_win P dE_m
      [MeV^-3] (MC divided by 4pi p_c^2, data exactly as tabulated), log y.

  out/pmiss_shape_<target>_<tune>.png
      pre/post-FSI |p_m| shapes normalized by their own surviving in-window
      count (unit integral over [0, 320)) vs the unit-normalized data.

Usage:
  pixi run python analysis/dutta-qe/plot_pmiss.py --target Fe56 --all-tunes
  pixi run python analysis/dutta-qe/plot_pmiss.py --target C12  --tune GEM26_22b_05_000
"""
import argparse

import numpy as np

from config import (OUT_DIR, PM_BINW, PM_DATA_BINW, PM_EDGES, PM_PLOT,
                    PM_SUM, TARGETS, TUNES)
from dutta import load_folded_pm
from events import (in_windows, load_cache, occ_hist, strength,
                    tunes_with_cache, unit_hist)
from sftable import load_table, n_windowed
from style import (apply_style, new_panels, style_axis,
                   FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

TITLES = ["1 — input table  $n_{win}(k)$",
          "2 — struck nucleon (record),  $|p_n|$",
          "3 — pre-FSI primary proton,  $|\\vec{p}_p-\\vec{q}\\,|$",
          "4 — post-FSI proton (N$_p$=1),  $|\\vec{p}_p-\\vec{q}\\,|$"]


def make_figures(target, tune, table_stem, table, data):
    cfg = TARGETS[target]
    Z = cfg["Z"]
    tlow = target.lower()
    c, n_sel = load_cache(target, tune)
    dx, dy, de = data                       # folded density [MeV^-3]
    wgt = 4.0 * np.pi * dx ** 2             # onto the occupancy axis
    has_table = TUNES[tune][0]
    y_in = k_edges = None
    if has_table:
        y_in, k_edges = n_windowed(table, Z, cfg["e_windows_pm"]), table["k_edges"]

    h, h2_all = {}, occ_hist(c["p2"], PM_EDGES, n_sel, Z)
    for s in (2, 3, 4):
        win = in_windows(c[f"E{s}r"], cfg["e_windows_pm"])
        h[s] = occ_hist(np.where(win, c[f"p{s}"], np.nan), PM_EDGES, n_sel, Z)
    s_data = float((wgt * dy).sum() * PM_DATA_BINW)
    print(f"[{tune}] |p_m| ladder ({cfg['pm_win_label']}, |p_m|<{PM_SUM:.0f}):"
          + (f"  I1={strength(y_in, k_edges, PM_SUM):.3f}"
             if y_in is not None else "")
          + f"  I(data)={s_data:.3f}  "
          + "  ".join(f"I{s}={strength(h[s], PM_EDGES, PM_SUM):.3f}"
                      for s in (2, 3, 4))
          + f"  I4/I3={strength(h[4], PM_EDGES, PM_SUM) / max(strength(h[3], PM_EDGES, PM_SUM), 1e-12):.3f}")

    # ---- occupancy ladder ---------------------------------------------------
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)

    def draw_data(ax, y_curve, err, with_label=False):
        ax.errorbar(dx, y_curve, yerr=err, fmt="s", ms=4, color="black",
                    capsize=2, zorder=9,
                    label=cfg["pm_data_label"] + " (publ. scale)"
                    if with_label else None)

    ax = axes[0]
    if y_in is not None:
        ax.stairs(y_in, k_edges, color="C1", linewidth=2.0, zorder=4,
                  label=f"Benhar SF {table_stem} (input)")
    else:
        ax.annotate(f"{TUNES[tune][1]}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, wgt * dy, wgt * de, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="folded data = full $|p_m|$ density",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if y_in is not None:
            ax.stairs(y_in, k_edges, color="C1", linewidth=1.0,
                      linestyle="--", alpha=0.8, zorder=2)
        if s == 2:
            ax.stairs(h2_all, PM_EDGES, color="0.5", linewidth=1.2,
                      linestyle=":", zorder=3, label="record, no $E_m$ window")
            ax.legend(fontsize=FS_LEGEND - 3, loc="upper right")
        ax.stairs(h[s], PM_EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax, wgt * dy, wgt * de)
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title="thin dashed: input table" if y_in is not None else None,
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    plot_sel = PM_EDGES[1:] <= PM_PLOT
    ymax = 1.15 * max([h[s][plot_sel].max() for s in (2, 3, 4)]
                      + [(wgt * (dy + de)).max(), h2_all[plot_sel].max()]
                      + ([y_in[k_edges[1:] <= PM_PLOT].max()]
                         if y_in is not None else []))
    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$|p_m|$  [MeV/c]" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, PM_PLOT)
        ax.set_ylim(0, ymax)
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$|p_m|\,/\,N_{sel}$   [(MeV/c)$^{-1}$]",
                          fontsize=FS_LABEL)
    fig.suptitle(f"{target} $|p_m|$ ladder — {tune}  ({TUNES[tune][1]})\n"
                 "qel && hit p && $Q^2=1.28\\pm5\\%$ && N$_p$=1; "
                 + cfg["pm_win_label"],
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"pmiss_ladder_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("  wrote", out)

    # ---- Dutta-native-units (density) variant -------------------------------
    p_c = (PM_EDGES[:-1] + PM_EDGES[1:]) / 2.0
    inv = 1.0 / (4.0 * np.pi * p_c ** 2)
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    ax = axes[0]
    if y_in is not None:
        k_c = (k_edges[:-1] + k_edges[1:]) / 2.0
        yd_in = y_in / (4.0 * np.pi * k_c ** 2)
        ax.stairs(yd_in, k_edges, color="C1", linewidth=2.0, zorder=4,
                  label=f"Benhar SF {table_stem} (input)")
    else:
        yd_in = None
        ax.annotate(f"{TUNES[tune][1]}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, dy, de, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="data units: as tabulated",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="lower left")
    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if yd_in is not None:
            ax.stairs(yd_in, k_edges, color="C1", linewidth=1.0,
                      linestyle="--", alpha=0.8, zorder=2)
        if s == 2:
            ax.stairs(h2_all * inv, PM_EDGES, color="0.5", linewidth=1.2,
                      linestyle=":", zorder=3, label="record, no $E_m$ window")
            ax.legend(fontsize=FS_LEGEND - 3, loc="lower left")
        ax.stairs(h[s] * inv, PM_EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax, dy, de)
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title="thin dashed: input table" if yd_in is not None else None,
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="lower left")
    top = 1.5 * max([(h[s] * inv)[plot_sel].max() for s in (2, 3, 4)]
                    + [(dy + de).max(), (h2_all * inv)[plot_sel].max()]
                    + ([yd_in[k_edges[1:] <= PM_PLOT].max()]
                       if yd_in is not None else []))
    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$|p_m|$  [MeV/c]" if i >= 2 else None,
                   logx=False, logy=True, ymin=None)
        ax.set_xlim(0, PM_PLOT)
        ax.set_ylim(top / 1e3, top)
        if i % 2 == 0:
            ax.set_ylabel(r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                          fontsize=FS_LABEL)
    fig.suptitle(f"{target} $|p_m|$ ladder, Dutta units — {tune}  "
                 f"({TUNES[tune][1]})\n"
                 "qel && hit p && $Q^2=1.28\\pm5\\%$ && N$_p$=1; "
                 + cfg["pm_win_label"],
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"pmiss_density_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("  wrote", out)

    # ---- survivor-normalized shape ------------------------------------------
    import matplotlib.pyplot as plt
    edges = PM_EDGES[PM_EDGES <= PM_SUM + 1e-9]
    y, n = {}, {}
    for s in (3, 4):
        win = in_windows(c[f"E{s}r"], cfg["e_windows_pm"])
        y[s], n[s] = unit_hist(np.where(win, c[f"p{s}"], np.nan), edges)
    dnorm = 1.0 / ((wgt * dy).sum() * PM_DATA_BINW)

    fig, ax = plt.subplots(figsize=(8.0, 5.8), layout="constrained")
    ax.stairs(y[3], edges, color="C0", linewidth=1.6, linestyle="--",
              zorder=4, label=f"pre-FSI shape (N={n[3]:,})")
    ax.stairs(y[4], edges, color="C3", linewidth=2.0, zorder=5,
              label=f"post-FSI shape (N={n[4]:,})")
    ax.errorbar(dx, wgt * dy * dnorm, yerr=wgt * de * dnorm, fmt="s", ms=4,
                color="black", capsize=2, zorder=9,
                label=cfg["pm_data_label"] + " (unit-norm.)")
    style_axis(ax, title=None, xlabel=r"$|p_m|$  [MeV/c]",
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, PM_SUM)
    ax.set_ylim(0, 1.25 * max(y[4].max(), (wgt * dy * dnorm).max()))
    ax.set_ylabel(r"d$N/$d$|p_m|\,/\,N_{\rm surv}$   [(MeV/c)$^{-1}$]",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title=cfg["pm_win_label"] + ";\nunit integral over [0, 320)",
              title_fontsize=FS_LEGEND_TITLE - 3)
    fig.suptitle(f"{target} post-FSI $|p_m|$ shape — {tune}  "
                 f"({TUNES[tune][1]})\nnormalized to the surviving events",
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"pmiss_shape_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close("all")
    print("  wrote", out)


def main(target, tunes):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()
    table_stem, table = load_table(target)
    data = load_folded_pm(target)
    for tune in tunes:
        make_figures(target, tune, table_stem, table, data)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TARGETS))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNES))
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()
    main(args.target,
         tunes_with_cache(args.target) if args.all_tunes else [args.tune])

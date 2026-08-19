"""Stage 1: E_miss figures per target/tune, vs Dutta figs 9/11.

Two figures per tune:

  out/emiss_ladder_<target>_<tune>.png
      four-stage occupancy ladder on the restored axis E + T_rec, p_m < 300:
      1 input table f(E), 2 struck-nucleon record, 3 pre-FSI primary proton,
      4 post-FSI proton (N_p = 1); each stage Z*dN/dE/N_sel so area =
      in-window nucleon count; data at their published scale.

  out/emiss_shape_<target>_<tune>.png
      pre/post-FSI shapes normalized by their OWN surviving in-window count
      (unit integral over [0, 80)) vs the unit-normalized data — the pure
      FSI shape distortion, scale divided out.

Usage:
  pixi run python analysis/dutta-qe/plot_emiss.py --target C12  --all-tunes
  pixi run python analysis/dutta-qe/plot_emiss.py --target Fe56 --tune GEM26_22a_05_000
"""
import argparse

import numpy as np

from config import (EM_BINW, EM_EDGES, OUT_DIR, PM_MAX_EM, TARGETS, TUNES)
from dutta import load_em
from events import load_cache, occ_hist, unit_hist
from sftable import f_restricted, load_table, rebin
from style import (apply_style, new_panels, style_axis,
                   FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)


def make_figures(target, tune, table_stem, table, data):
    cfg = TARGETS[target]
    Z = cfg["Z"]
    tlow = target.lower()
    c, n_sel = load_cache(target, tune)
    dem, dsf, dstat, dtot = data
    has_table = TUNES[tune][0]
    y_in = None
    if has_table:
        y_in = rebin(table["E"], f_restricted(table, Z, PM_MAX_EM),
                     table["dE"], EM_EDGES)

    h = {}
    for s in (2, 3, 4):
        win = c[f"p{s}"] < PM_MAX_EM
        h[s] = occ_hist(np.where(win, c[f"E{s}r"], np.nan), EM_EDGES, n_sel, Z)
    print(f"[{tune}] E_m ladder (p_m<{PM_MAX_EM:.0f}):"
          + (f"  I1={y_in.sum() * EM_BINW:.3f}" if y_in is not None else "")
          + "  " + "  ".join(f"I{s}={h[s].sum() * EM_BINW:.3f}"
                             for s in (2, 3, 4))
          + f"  I4/I3={h[4].sum() / max(h[3].sum(), 1e-12):.3f}")

    # ---- ladder figure ------------------------------------------------------
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    TITLES = ["1 — input table  $f_{p<300}(E)$",
              "2 — struck nucleon (record)",
              "3 — pre-FSI primary proton",
              "4 — post-FSI proton (N$_p$=1)"]

    def draw_data(ax, with_label=False):
        ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6",
                    elinewidth=3, alpha=0.8, zorder=8)
        ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black",
                    capsize=2, zorder=9,
                    label=cfg["em_data_label"] + " (publ. scale)"
                    if with_label else None)

    ax = axes[0]
    if y_in is not None:
        ax.stairs(y_in, EM_EDGES, color="C1", linewidth=2.0, zorder=4,
                  label=f"Benhar SF {table_stem} (input)")
    else:
        ax.annotate(f"{TUNES[tune][1]}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="table axis = restored axis",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if y_in is not None:
            ax.stairs(y_in, EM_EDGES, color="C1", linewidth=1.0,
                      linestyle="--", alpha=0.8, zorder=2)
        ax.stairs(h[s], EM_EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax)
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title="thin dashed: input table" if y_in is not None else None,
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")
    axes[1].annotate("record/pre-FSI spikes\nmay run off scale",
                     xy=(0.05, 0.85), xycoords="axes fraction",
                     fontsize=FS_LEGEND - 3, color="0.35")

    # scale on the physics curves; record/pre-FSI delta spikes may clip
    ymax = 1.3 * max([h[4].max(), (dsf + dtot).max()]
                     + ([y_in.max()] if y_in is not None else []))
    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$E_m+T_{rec}$  (MeV)" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 80)
        ax.set_ylim(0, ymax)
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$(E_m+T_{rec})\,/\,N_{sel}$   (MeV$^{-1}$)",
                          fontsize=FS_LABEL)
    fig.suptitle(f"{target} restored E$_m$ ladder — {tune}  ({TUNES[tune][1]})\n"
                 "qel && hit p && $Q^2=1.28\\pm5\\%$ && N$_p$=1, "
                 "$p_m<300$ MeV/$c$",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"emiss_ladder_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("  wrote", out)

    # ---- survivor-normalized shape figure -----------------------------------
    import matplotlib.pyplot as plt
    y, n = {}, {}
    for s in (3, 4):
        win = c[f"p{s}"] < PM_MAX_EM
        y[s], n[s] = unit_hist(np.where(win, c[f"E{s}r"], np.nan), EM_EDGES)
    dnorm = 1.0 / (dsf.sum() * EM_BINW)

    fig, ax = plt.subplots(figsize=(8.0, 5.8), layout="constrained")
    ax.stairs(y[3], EM_EDGES, color="C0", linewidth=1.6, linestyle="--",
              zorder=4, label=f"pre-FSI shape (N={n[3]:,})")
    ax.stairs(y[4], EM_EDGES, color="C3", linewidth=2.0, zorder=5,
              label=f"post-FSI shape (N={n[4]:,})")
    ax.errorbar(dem, dsf * dnorm, yerr=dstat * dnorm, fmt="s", ms=4,
                color="black", capsize=2, zorder=9,
                label=cfg["em_data_label"] + " (unit-norm.)")
    style_axis(ax, title=None, xlabel=r"$E_m+T_{rec}$  (MeV)",
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 80)
    ax.set_ylim(0, 1.25 * max(y[4].max(), (dsf * dnorm).max()))
    ax.set_ylabel(r"d$N/$d$(E_m+T_{rec})\,/\,N_{\rm surv}$   (MeV$^{-1}$)",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title="unit integral over [0, 80)\n(pre-FSI spikes may clip)",
              title_fontsize=FS_LEGEND_TITLE - 3)
    fig.suptitle(f"{target} post-FSI E$_m$ shape — {tune}  ({TUNES[tune][1]})\n"
                 "normalized to the surviving events",
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"emiss_shape_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close("all")
    print("  wrote", out)


def main(target, tunes):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()
    table_stem, table = load_table(target)
    data = load_em(target)
    for tune in tunes:
        make_figures(target, tune, table_stem, table, data)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="C12", choices=list(TARGETS))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNES))
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()
    main(args.target, sorted(TUNES) if args.all_tunes else [args.tune])

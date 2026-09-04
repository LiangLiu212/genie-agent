"""Overlay the two INCL local-energy settings (lfon / lfnever) on the E_m and
|p_m| projections, pre- and post-FSI, against the Dutta C12 data.

Reads the ladder caches built by make_emiss_ladder_q2cut.py (v1.0 mode:
--proton-sel 1p --no-q2cut -> results/prd-analyzer-v1.0/cache/ladder_c12/)
and reuses that script's (and make_pmiss_ladder_q2cut.py's) axis, window and
data conventions, so every curve here is the same object as the matching
ladder panel. Occupancy scale: Z * dN/dx / N_sel.

Usage: pixi run python results/template/make_incl_onoff_overlay.py \
           [--tunes GEM26_44b_05_000_lfon GEM26_44b_05_000_lfnever] \
           [--labels "local energy on" never] [--out-dir results/prd-analyzer-v1.1]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "results/template"))
sys.path.insert(0, str(REPO / "results/prd-analyzer-v0"))
import make_emiss_ladder_q2cut as em    # noqa: E402
import make_pmiss_ladder_q2cut as pm    # noqa: E402
from plot_style import (apply_style, new_panels, style_axis, DPI,   # noqa: E402
                        FS_SUPTITLE, FS_LEGEND, FS_LEGEND_TITLE)

CACHE = REPO / "results/prd-analyzer-v1.0/cache/ladder_c12"
STYLES = [("C3", "-"), ("C2", "--"), ("C0", "-."), ("C1", ":")]


def load(tune, m_rec_gev):
    c = dict(np.load(CACHE / f"{tune}.npz"))
    for s in (2, 3, 4):
        c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec_gev * 1000.0)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tunes", nargs="+",
                    default=["GEM26_44b_05_000_lfon", "GEM26_44b_05_000_lfnever"])
    ap.add_argument("--labels", nargs="+", default=["local energy on", "never"])
    ap.add_argument("--out-dir", default=str(REPO / "results/prd-analyzer-v1.1"))
    ap.add_argument("--stem", default="incl_onoff_overlay_c12")
    args = ap.parse_args()
    assert len(args.tunes) == len(args.labels)
    apply_style()
    cfg_e, cfg_p = em.TGT["C12"], pm.TGT["C12"]
    Z = cfg_e["Z"]
    m_rec = em._m_rec_c12()
    dem, dsf, dstat, dtot = cfg_e["dutta"]()
    dx, dy, de = cfg_p["dutta"]()
    w = 4.0 * np.pi * dx ** 2

    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    for (tune, lab), (color, ls) in zip(zip(args.tunes, args.labels), STYLES):
        c = load(tune, m_rec)
        n_sel = int(c["n_sel"][0])
        hE = {s: em.occ_hist(c[f"E{s}r"], c[f"p{s}"], n_sel, Z) for s in (3, 4)}
        hP = {}
        for s in (3, 4):
            win = pm.in_windows(c[f"E{s}r"], cfg_p["e_windows"])
            hP[s] = pm.occ_hist(np.where(win, c[f"p{s}"], np.nan), n_sel, Z)
        print(f"[{tune}] n_sel={n_sel:,}  "
              f"I3r={hE[3].sum() * em.BINW:.3f} I4r={hE[4].sum() * em.BINW:.3f}  "
              f"I3={pm.strength(hP[3], pm.EDGES):.3f} I4={pm.strength(hP[4], pm.EDGES):.3f}")
        for ax, s in zip(axes[:2], (3, 4)):
            ax.stairs(hE[s], em.EDGES, color=color, linewidth=1.8, linestyle=ls,
                      zorder=5, label=f"{lab} ({tune})")
        for ax, s in zip(axes[2:], (3, 4)):
            ax.stairs(hP[s], pm.EDGES, color=color, linewidth=1.8, linestyle=ls,
                      zorder=5, label=f"{lab} ({tune})")
    for ax in axes[:2]:
        ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                    zorder=9, label=cfg_e["data_label"])
        ax.set_xlim(0, 80)
    for ax in axes[2:]:
        ax.errorbar(dx, w * dy, yerr=w * de, fmt="s", ms=4, color="black",
                    capsize=2, zorder=9, label=cfg_p["data_label"])
        ax.set_xlim(0, pm.PM_PLOT)
    style_axis(axes[0], title="pre-FSI primary proton,  $\\omega-T_p$",
               ylabel="$Z\\cdot$ d$N$/d$(E_m+T_{rec})\\,/\\,N_{sel}$  (MeV$^{-1}$)",
               logy=False, ymin=None)
    style_axis(axes[1], title="post-FSI proton,  $\\omega-T_p$", logy=False, ymin=None)
    style_axis(axes[2], title="pre-FSI primary proton,  $|\\vec{p}_p-\\vec{q}\\,|$",
               xlabel="$|p_m|$  [MeV/$c$]",
               ylabel="$Z\\cdot$ d$N$/d$|p_m|\\,/\\,N_{sel}$  [(MeV/$c$)$^{-1}$]",
               logy=False, ymin=None)
    style_axis(axes[3], title="post-FSI proton,  $|\\vec{p}_p-\\vec{q}\\,|$",
               xlabel="$|p_m|$  [MeV/$c$]", logy=False, ymin=None)
    for ax in axes[:2]:
        ax.set_xlabel("$E_m+T_{rec}$  (MeV)", fontsize=em.FS_LABEL)
    for ax in axes:
        ax.set_ylim(0, None)
    axes[3].set_ylim(0, 0.046)          # headroom for the legend above the data
    axes[1].legend(fontsize=FS_LEGEND - 2, loc="upper right")
    axes[3].legend(fontsize=FS_LEGEND - 2, loc="upper left",
                   title=cfg_p["win_label"], title_fontsize=FS_LEGEND_TITLE - 3)
    fig.suptitle("C12 e$^-$ 2.445 GeV, INCL-scheme vertex: local energy on vs never\n"
                 "qel && hit p && N$_p$=1, NO $Q^2$ cut; $E_m$ panels: $p_m<300$ MeV/$c$, "
                 "$|p_m|$ panels: shell windows",
                 fontsize=FS_SUPTITLE - 3)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = Path(args.out_dir) / f"{args.stem}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    main()

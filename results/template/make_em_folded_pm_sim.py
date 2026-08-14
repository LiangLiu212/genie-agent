"""Simulated E_m spectrum AND folded |p_m| in the dutta_em_folded_pm style — v1.0.

The results/normalization/dutta_em_folded_pm.png layout (C12 row: E_m
spectrum vs fig 9 | folded p-shell vs fig 6 top | folded s-shell vs fig 6
bot) with the curves = the SIMULATION instead of the input tables: the
pre-FSI (stage 3) and post-FSI (stage 4) proton of a single tune, read from
the v1.0 uncut ladder caches (qel && hitnuc==p && N_p=1, NO Q^2 cut; build
with make_emiss_ladder_q2cut.py --no-q2cut). The input table stays as a
thin dashed reference.

Units per panel match the normalization page exactly:
  E_m panel:  occupancy  Z*dN/d(E_m+T_rec)/N_sel  [MeV^-1], p_s < 300,
              data's 5-MeV bins; fig 9 at its published scale.
  p_m panels: 3D density  (Z*dN/d|p_m|/N_sel) / (4 pi p_c^2)  [MeV^-3],
              the fig 6 E_m window applied per shell, native 20-MeV/c
              grid; folded data y(+p)+y(-p) at the published scale
              (errors 2x stat -- the sides are duplicated).

Usage:
  pixi run python results/template/make_em_folded_pm_sim.py            # 22b
  pixi run python results/template/make_em_folded_pm_sim.py --tune GEM26_22a_05_000
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LEGEND, FS_TICK, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results/prd-analyzer-v1.0/cache/ladder_c12"
OUT_DIR = REPO / "results/prd-analyzer-v1.0"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"

Z = 6
PM_MAX = 300.0                   # E_m panel p_s window [MeV/c]
E_EDGES = np.arange(0.0, 85.0, 5.0)
DK = 20.0                        # native table k grid [MeV/c]
K_EDGES = np.arange(0.0, 820.0 + 1.0, DK)

TUNE_GS = {
    "GEM26_11a_05_000": "LocalFGM",
    "GEM26_22a_05_000": "SF + Rosenbluth",
    "GEM26_22b_05_000": "SF + UnifiedQEL",
    "GEM21_11a_05_000": "SuSAv2",
}


def _m_rec_c12():
    from acceptance import M_REC       # B11 [GeV], v0 value (matches caches)
    return M_REC


def load_table():
    """Occupancy-normalized (integral = Z) Benhar C12 table."""
    path = resolve_sf_table("GEM26_22a_05_000", 1000060120, 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    return path.stem, (k, E, k_edges, S / raw, dk, dE)


def table_em(table, edges, kmax=PM_MAX):
    """f_{k<kmax}(E) rebinned into `edges` (occupancy scale, MeV^-1)."""
    k, E, k_edges, P, dk, dE = table
    sel = (k + dk / 2.0) <= kmax + 1e-9
    f = Z * (4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :] * dk).sum(axis=0)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        ov = np.clip(np.minimum(E + dE / 2.0, hi)
                     - np.maximum(E - dE / 2.0, lo), 0.0, None)
        out[i] = (f * ov).sum() / (hi - lo)
    return out


def table_pm_density(table, e_win):
    """int_{E win} P dE on the native k grid (MeV^-3), partial bins clipped."""
    k, E, k_edges, P, dk, dE = table
    lo, hi = e_win
    ov = np.clip(np.minimum(E + dE / 2.0, hi)
                 - np.maximum(E - dE / 2.0, lo), 0.0, None)
    return Z * (P * ov[None, :]).sum(axis=1), k_edges


def load_cache(tune):
    path = CACHE / f"{tune}.npz"
    if not path.exists():
        raise SystemExit(f"missing v1.0 cache {path} — build it with "
                         "make_emiss_ladder_q2cut.py --target C12 "
                         "--all-tunes --proton-sel 1p --no-q2cut")
    c = dict(np.load(path))
    m_rec = _m_rec_c12()
    with np.errstate(invalid="ignore"):
        for s in (3, 4):
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)
    return c


def mc_em(c, s):
    """Occupancy E_m spectrum of stage s (p_s < 300), data 5-MeV bins."""
    n_sel = float(c["n_sel"][0])
    m = np.isfinite(c[f"E{s}r"]) & (c[f"p{s}"] < PM_MAX)
    cnt, _ = np.histogram(c[f"E{s}r"][m], bins=E_EDGES)
    return Z * cnt / (n_sel * 5.0)


def mc_pm_density(c, s, e_win):
    """3D-density |p_m| of stage s in the E_m window, 20-MeV/c bins."""
    n_sel = float(c["n_sel"][0])
    Er = c[f"E{s}r"]
    m = np.isfinite(Er) & (Er >= e_win[0]) & (Er < e_win[1])
    cnt, _ = np.histogram(c[f"p{s}"][m], bins=K_EDGES)
    occ = Z * cnt / (n_sel * DK)
    p_c = (K_EDGES[:-1] + K_EDGES[1:]) / 2.0
    return occ / (4.0 * np.pi * p_c ** 2)


def dutta_em():
    from fig9_common import load_dutta      # incl. published-bar overrides
    return load_dutta()


def dutta_pm(stem):
    x, y, _, e = np.loadtxt(DATA_DIR / f"{stem}.dat", unpack=True)
    m = x > 0
    return x[m], 2.0 * y[m], 2.0 * e[m]    # folded L+R, errors 2x stat


def strength_em(y):
    return float(y.sum() * 5.0)


def strength_pm(y_dens, edges):
    p_c = (edges[:-1] + edges[1:]) / 2.0
    sel = edges[1:] <= 320.0 + 1e-9
    return float((4.0 * np.pi * p_c[sel] ** 2 * y_dens[sel]).sum()
                 * np.diff(edges)[sel].mean())


def main(tune):
    apply_style()
    table_stem, table = load_table()
    c = load_cache(tune)

    fig, axes = new_panels(ncols=3, nrows=1, sharey=False)
    ax_em, ax_psh, ax_ssh = axes

    # ---- E_m spectrum vs fig 9 -------------------------------------------
    dem, dsf, dstat, dtot = dutta_em()
    y_tab = table_em(table, E_EDGES)
    y3, y4 = mc_em(c, 3), mc_em(c, 4)
    ax_em.stairs(y_tab, E_EDGES, color="C1", lw=1.0, linestyle="--",
                 alpha=0.8, zorder=3, label=f"table {table_stem}")
    ax_em.stairs(y3, E_EDGES, color="C0", lw=1.6, linestyle="--", zorder=4,
                 label="pre-FSI (stage 3)")
    ax_em.stairs(y4, E_EDGES, color="C3", lw=2.0, zorder=5,
                 label="post-FSI (stage 4)")
    ax_em.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6",
                   elinewidth=3, alpha=0.8, zorder=8)
    ax_em.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black",
                   capsize=2, zorder=9, label="Dutta fig 9")
    ax_em.text(0.35, 0.97,
               f"data/pre = {strength_em(dsf) / strength_em(y3):.2f}"
               f"   I4/I3 = {strength_em(y4) / strength_em(y3):.2f}",
               transform=ax_em.transAxes, va="top", fontsize=FS_TICK)
    style_axis(ax_em, title=r"C12 $E_m$ spectrum vs fig 9",
               xlabel=r"$E_m+T_{rec}$  [MeV]",
               ylabel=r"$Z\cdot$ d$N/$d$E\,/\,N_{sel}$   [MeV$^{-1}$]",
               logx=False, logy=False, ymin=None)
    ax_em.set_xlim(0, 85)
    ax_em.set_ylim(0, 0.7)
    ax_em.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="center right")

    # ---- folded |p_m| per shell ------------------------------------------
    for ax, stem, e_win, title in [
        (ax_psh, "fig6_top_q1p2", (10.0, 25.0),
         "C12 folded p-shell (10–25 MeV)"),
        (ax_ssh, "fig6_bot_q1p2", (30.0, 50.0),
         "C12 folded s-shell (30–50 MeV)"),
    ]:
        dx, dy, de = dutta_pm(stem)
        yt, k_edges = table_pm_density(table, e_win)
        y3, y4 = (mc_pm_density(c, 3, e_win), mc_pm_density(c, 4, e_win))
        ax.stairs(yt, k_edges, color="C1", lw=1.0, linestyle="--",
                  alpha=0.8, zorder=3, label=f"table {table_stem}")
        ax.stairs(y3, K_EDGES, color="C0", lw=1.6, linestyle="--", zorder=4,
                  label="pre-FSI (stage 3)")
        ax.stairs(y4, K_EDGES, color="C3", lw=2.0, zorder=5,
                  label="post-FSI (stage 4)")
        ax.errorbar(dx, dy, yerr=de, fmt="s", ms=5, color="black",
                    capsize=2, zorder=9, label="Dutta L+R")
        s_data = float((4.0 * np.pi * dx ** 2 * dy).sum() * 40.0)
        ax.text(0.03, 0.03,
                f"data/pre = {s_data / strength_pm(y3, K_EDGES):.2f}"
                f"   I4/I3 = "
                f"{strength_pm(y4, K_EDGES) / strength_pm(y3, K_EDGES):.2f}",
                transform=ax.transAxes, va="bottom", fontsize=FS_TICK)
        style_axis(ax, title=title, xlabel=r"$|p_m|$  [MeV/c]",
                   ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                   logx=False, ymin=None)
        ax.set_xlim(0, 330)
        plot_sel = K_EDGES[1:] <= 330.0
        top = 1.5 * max(y3[plot_sel].max(), y4[plot_sel].max(),
                        yt[k_edges[1:] <= 330.0].max(), (dy + de).max())
        ax.set_ylim(top / 1e3, top)     # 3 decades, as the dens ladder
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="upper right")
        print(f"  {title}: data/pre="
              f"{s_data / strength_pm(y3, K_EDGES):.3f}  "
              f"I4/I3={strength_pm(y4, K_EDGES) / strength_pm(y3, K_EDGES):.3f}")

    n_sel = int(c["n_sel"][0])
    fig.suptitle(f"Dutta E91-013 vs simulated {tune} ({TUNE_GS[tune]}) — "
                 r"$E_m$ spectrum and folded $|p_m|$"
                 "\nqel && hit p && N$_p$=1, NO $Q^2$ cut "
                 f"(N$_{{sel}}$ = {n_sel:,}); data at publ. scale, "
                 "table thin dashed",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"em_folded_pm_sim_c12_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22b_05_000",
                    choices=sorted(TUNE_GS))
    args = ap.parse_args()
    main(args.tune)

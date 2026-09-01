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

--nsel postfsi replaces the MC normalization denominator N_sel (all
qel && hit-p events) with the number of events AFTER FSI (a surviving
N_p = 1 proton, i.e. stage 4 exists) — the simulation-side analogue of the
data's renormalization, which scales the distorted yield back up. Writes
the `_nselpost` figure variant (em_folded_pm_sim_nselpost_...); table and
data are untouched.

--nsel postwin goes one step further than postfsi: the denominator is the
number of post-FSI events INSIDE the measurement window (E_m + T_rec in
[0, 80) MeV and p_m < 300 MeV/c) — the analogue of Dutta's full-occupancy
renormalization: the stage-4 curve then integrates to exactly Z over the
window, directly comparable to fig 9's 6.08. Writes the `_nselwin`
variant.

--proton-sel leading replaces the stage-4 definition N_p = 1 with the
LEADING final-state proton of any >=1p event (the v0.2 convention). Reads
the `ladder_c12_leading` uncut cache (build with
make_emiss_ladder_q2cut.py --proton-sel leading --no-q2cut --build-only)
and writes the `_leadp` figure variant.

--combo draws the mixed-normalization summary (needs BOTH caches): table
+ pre-FSI / N_sel (true occupancy) + post-FSI leading p / its post-FSI
event count + post-FSI N_p = 1 / its in-window count — the three
normalization conventions of the preceding variants in one figure
(`_combo`); --nsel/--proton-sel are ignored with it.

--combo --grid draws the combo content for ALL FOUR tunes in one
paper-style 8-panel figure (`_combo_grid`): rows = tunes, left column =
E_m spectrum, right column = folded |p_m| on the full E window. No
suptitle and no panel titles (the tune tag sits inside each E_m panel);
the |p_m| column shares one log scale so rows compare directly.

Usage:
  pixi run python results/template/make_em_folded_pm_sim.py            # 22b
  pixi run python results/template/make_em_folded_pm_sim.py --tune GEM26_22a_05_000
  pixi run python results/template/make_em_folded_pm_sim.py --nsel postfsi
  pixi run python results/template/make_em_folded_pm_sim.py --proton-sel leading
  pixi run python results/template/make_em_folded_pm_sim.py --combo
  pixi run python results/template/make_em_folded_pm_sim.py --combo --grid
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
CACHE_ROOT = REPO / "results/prd-analyzer-v1.0/cache"
OUT_DIR = REPO / "results/prd-analyzer-v1.0"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"

# per-target configuration; CFG is rebound from --target at entry
TGT = {
    "C12": dict(Z=6, tgt_pdg=1000060120, m_rec_gev=None,   # B11 from v0
                tlow="c12", em_ymax=0.7),
    "Fe56": dict(Z=26, tgt_pdg=1000260560,
                 m_rec_gev=51.1616880,                     # Mn55 (v0.1)
                 tlow="fe56", em_ymax=1.5),
}
CFG = TGT["C12"]

PM_MAX = 300.0                   # E_m panel p_s window [MeV/c]
E_EDGES = np.arange(0.0, 85.0, 5.0)
DK = 20.0                        # native table k grid [MeV/c]
K_EDGES = np.arange(0.0, 820.0 + 1.0, DK)

TUNE_GS = {
    "GEM26_11a_05_000": "LocalFGM",
    "GEM26_22a_05_000": "SF + Rosenbluth",
    "GEM26_22b_05_000": "SF + UnifiedQEL",
    "GEM21_11a_05_000": "SuSAv2",
    "GEM26_44b_05_000": "INCL++ GS+FSI",      # local C12 sample, no campaign
}
# row order of the --grid figure (= the notes' table order); --grid-tunes
# overrides it (with --tag naming the output), e.g. the five-row INCL grid
TUNE_ORDER = ["GEM26_11a_05_000", "GEM26_22a_05_000",
              "GEM26_22b_05_000", "GEM21_11a_05_000"]
GRID_TUNES = TUNE_ORDER
TAG = ""
# tunes whose ground state IS the 2D Benhar table (draw it as their input;
# for LFG/SuSA tunes the table curve is omitted)
TABLE_TUNES = {"GEM26_22a_05_000", "GEM26_22b_05_000"}


def _m_rec():
    if CFG["m_rec_gev"] is not None:
        return CFG["m_rec_gev"]
    from acceptance import M_REC       # B11 [GeV], v0 value (matches caches)
    return M_REC


def load_table():
    """Occupancy-normalized (integral = Z) Benhar table for the target."""
    path = resolve_sf_table("GEM26_22a_05_000", CFG["tgt_pdg"], 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    return path.stem, (k, E, k_edges, S / raw, dk, dE)


def table_em(table, edges, kmax=PM_MAX):
    """f_{k<kmax}(E) rebinned into `edges` (occupancy scale, MeV^-1)."""
    k, E, k_edges, P, dk, dE = table
    sel = (k + dk / 2.0) <= kmax + 1e-9
    f = CFG["Z"] * (4.0 * np.pi * (k[sel, None] ** 2)
                    * P[sel, :] * dk).sum(axis=0)
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
    return CFG["Z"] * (P * ov[None, :]).sum(axis=1), k_edges


def load_cache(tune, psel):
    tag = "" if psel == "1p" else "_leading"
    path = CACHE_ROOT / f"ladder_{CFG['tlow']}{tag}" / f"{tune}.npz"
    if not path.exists():
        raise SystemExit(f"missing v1.0 cache {path} — build it with "
                         "make_emiss_ladder_q2cut.py --target <target> "
                         f"--tune {tune} --proton-sel {psel} --no-q2cut "
                         "--build-only")
    c = dict(np.load(path))
    m_rec = _m_rec()
    with np.errstate(invalid="ignore"):
        for s in (3, 4):
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)
    return c


def mc_em(c, s, n_norm):
    """Occupancy E_m spectrum of stage s (p_s < 300), data 5-MeV bins."""
    m = np.isfinite(c[f"E{s}r"]) & (c[f"p{s}"] < PM_MAX)
    cnt, _ = np.histogram(c[f"E{s}r"][m], bins=E_EDGES)
    return CFG["Z"] * cnt / (n_norm * 5.0)


def mc_pm_density(c, s, e_win, n_norm):
    """3D-density |p_m| of stage s in the E_m window, 20-MeV/c bins."""
    Er = c[f"E{s}r"]
    m = np.isfinite(Er) & (Er >= e_win[0]) & (Er < e_win[1])
    cnt, _ = np.histogram(c[f"p{s}"][m], bins=K_EDGES)
    occ = CFG["Z"] * cnt / (n_norm * DK)
    p_c = (K_EDGES[:-1] + K_EDGES[1:]) / 2.0
    return occ / (4.0 * np.pi * p_c ** 2)


def dutta_em():
    from fig9_common import load_dutta      # incl. published-bar overrides
    return load_dutta()


def dutta_em_target():
    """(dem, dsf, dstat, dtot), label — the target's E_m spectrum data."""
    if CFG["tlow"] == "c12":
        return dutta_em(), "Dutta fig 9"
    dem, dsf, _, dstat = np.loadtxt(DATA_DIR / "fig11_q1p2.dat", unpack=True)
    dtot = np.sqrt(dstat ** 2 + (0.02 * dsf) ** 2 + (0.05 * dsf) ** 2)
    return (dem, dsf, dstat, dtot), "Dutta fig 11"


def dutta_pm(stem):
    x, y, _, e = np.loadtxt(DATA_DIR / f"{stem}.dat", unpack=True)
    m = x > 0
    return x[m], 2.0 * y[m], 2.0 * e[m]    # folded L+R, errors 2x stat


def pm_full_data(dem, dsf):
    """Folded |p_m| data on the FULL E window [0, 80): C12 = the fig 6
    shells summed and gap-filled from the fig 9 E_m shape; Fe56 = fig 7
    as-is. Returns (dx, dy, de, label)."""
    if CFG["tlow"] == "c12":
        dx, dyp, dep = dutta_pm("fig6_top_q1p2")
        _, dys, des = dutta_pm("fig6_bot_q1p2")
        m_sh = (((dem >= 10.0) & (dem < 25.0))
                | ((dem >= 30.0) & (dem < 50.0)))
        f_gap = float(dsf.sum() / dsf[m_sh].sum())
        print(f"  gap-fill from fig 9 shape: f = {f_gap:.3f} "
              f"(shell windows hold {100.0 / f_gap:.1f}% of [0,80))")
        return (dx, f_gap * (dyp + dys),
                f_gap * np.sqrt(dep ** 2 + des ** 2),
                f"Dutta p+s L+R $\\times$ {f_gap:.2f}")
    # fig 7 IS the E_m < 80 window — folded, no gap-fill
    dx, dy, de = dutta_pm("fig7_q1p2")
    return dx, dy, de, "Dutta fig 7 L+R"


def strength_em(y):
    return float(y.sum() * 5.0)


def strength_pm(y_dens, edges):
    p_c = (edges[:-1] + edges[1:]) / 2.0
    sel = edges[1:] <= 320.0 + 1e-9
    return float((4.0 * np.pi * p_c[sel] ** 2 * y_dens[sel]).sum()
                 * np.diff(edges)[sel].mean())


def main(tune, nsel_mode, psel):
    apply_style()
    table_stem, table = load_table()
    c = load_cache(tune, psel)
    p4lab = ("post-FSI (stage 4)" if psel == "1p"
             else "post-FSI leading p (stage 4)")
    n_sel = float(c["n_sel"][0])
    n_post = float(np.isfinite(c["E4"]).sum())
    with np.errstate(invalid="ignore"):
        m4win = (np.isfinite(c["E4r"]) & (c["E4r"] >= 0.0)
                 & (c["E4r"] < 80.0) & (c["p4"] < PM_MAX))
    n_win = float(m4win.sum())
    n_norm = {"sel": n_sel, "postfsi": n_post, "postwin": n_win}[nsel_mode]
    if nsel_mode == "postfsi":
        print(f"  N_sel -> post-FSI events: {int(n_post):,} of "
              f"{int(n_sel):,} ({n_post / n_sel:.3f})")
    elif nsel_mode == "postwin":
        print(f"  N_sel -> in-window post-FSI events (E<80, p<300): "
              f"{int(n_win):,} of {int(n_sel):,} ({n_win / n_sel:.3f})")

    fig, axes = new_panels(ncols=3, nrows=1, sharey=False)
    ax_em, ax_psh, ax_ssh = axes

    # ---- E_m spectrum vs fig 9 -------------------------------------------
    dem, dsf, dstat, dtot = dutta_em()
    y_tab = table_em(table, E_EDGES)
    y3, y4 = mc_em(c, 3, n_norm), mc_em(c, 4, n_norm)
    if tune in TABLE_TUNES:
        ax_em.stairs(y_tab, E_EDGES, color="C1", lw=1.0, linestyle="--",
                     alpha=0.8, zorder=3, label=f"table {table_stem}")
    ax_em.stairs(y3, E_EDGES, color="C0", lw=1.6, linestyle="--", zorder=4,
                 label="pre-FSI (stage 3)")
    ax_em.stairs(y4, E_EDGES, color="C3", lw=2.0, zorder=5, label=p4lab)
    ax_em.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6",
                   elinewidth=3, alpha=0.8, zorder=8)
    ax_em.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black",
                   capsize=2, zorder=9, label="Dutta fig 9")
    ax_em.text(0.35, 0.97,
               f"data/pre = {strength_em(dsf) / strength_em(y3):.2f}"
               f"   I4/I3 = {strength_em(y4) / strength_em(y3):.2f}",
               transform=ax_em.transAxes, va="top", fontsize=FS_TICK)
    nlab = {"sel": r"N_{sel}", "postfsi": r"N_{postFSI}",
            "postwin": r"N_{win}^{postFSI}"}[nsel_mode]
    style_axis(ax_em, title=r"C12 $E_m$ spectrum vs fig 9",
               xlabel=r"$E_m+T_{rec}$  [MeV]",
               ylabel=rf"$Z\cdot$ d$N/$d$E\,/\,{nlab}$   [MeV$^{{-1}}$]",
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
        y3, y4 = (mc_pm_density(c, 3, e_win, n_norm),
                  mc_pm_density(c, 4, e_win, n_norm))
        if tune in TABLE_TUNES:
            ax.stairs(yt, k_edges, color="C1", lw=1.0, linestyle="--",
                      alpha=0.8, zorder=3, label=f"table {table_stem}")
        ax.stairs(y3, K_EDGES, color="C0", lw=1.6, linestyle="--", zorder=4,
                  label="pre-FSI (stage 3)")
        ax.stairs(y4, K_EDGES, color="C3", lw=2.0, zorder=5, label=p4lab)
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
                   logx=False, ymin=None, logy=True)
        ax.set_xlim(0, 330)
        plot_sel = K_EDGES[1:] <= 330.0
        top = 1.5 * max(y3[plot_sel].max(), y4[plot_sel].max(),
                        yt[k_edges[1:] <= 330.0].max(), (dy + de).max())
        ax.set_ylim(top / 1e3, top)     # 3 decades, as the dens ladder
        ax.legend(fontsize=FS_LEGEND - 2, frameon=False, loc="upper right")
        print(f"  {title}: data/pre="
              f"{s_data / strength_pm(y3, K_EDGES):.3f}  "
              f"I4/I3={strength_pm(y4, K_EDGES) / strength_pm(y3, K_EDGES):.3f}")

    if nsel_mode == "postfsi":
        norm_note = (f"MC / N$_{{post-FSI}}$ = {int(n_post):,} "
                     f"(of {int(n_sel):,} selected)")
    elif nsel_mode == "postwin":
        norm_note = f"MC / in-win post-FSI N = {int(n_win):,}"
    else:
        norm_note = f"N$_{{sel}}$ = {int(n_sel):,}"
    sel_clause = ("N$_p$=1" if psel == "1p" else "leading p")
    fig.suptitle(f"Dutta E91-013 vs simulated {tune} ({TUNE_GS[tune]}) — "
                 r"$E_m$ spectrum and folded $|p_m|$"
                 f"\nqel && hit p && {sel_clause}, NO $Q^2$ cut "
                 f"({norm_note}); data at publ. scale, "
                 "table thin dashed",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    infix = {"sel": "", "postfsi": "_nselpost",
             "postwin": "_nselwin"}[nsel_mode] \
        + ("" if psel == "1p" else "_leadp")
    out = OUT_DIR / f"em_folded_pm_sim{infix}_c12_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


def main_combo(tune, shells=False):
    """Mixed normalizations together: table, pre-FSI/N_sel, post-FSI
    leading p / N_win(leading), post-FSI N_p=1 / N_win(1p) — each post
    stage renormalized by its OWN in-window count. Single |p_m| panel on
    the FULL E_m window [0, 80): the fig 6 p+s folded data are summed and
    scaled up by the gap-fill factor f = fig 9 strength in [0, 80) / fig 9
    strength in (10-25 u 30-50) — the E_m-shape correction for the 25-30
    and 50-80 MeV strength the shell windows miss ([0, 10) is empty)."""
    apply_style()
    table_stem, table = load_table()
    c1 = load_cache(tune, "1p")
    cl = load_cache(tune, "leading")
    n_sel = float(c1["n_sel"][0])

    def n_win(c):
        with np.errstate(invalid="ignore"):
            m = (np.isfinite(c["E4r"]) & (c["E4r"] >= 0.0)
                 & (c["E4r"] < 80.0) & (c["p4"] < PM_MAX))
        return float(m.sum())

    n_win_l, n_win_1 = n_win(cl), n_win(c1)
    print(f"  N_sel={int(n_sel):,}  N_win(leading)={int(n_win_l):,} "
          f"({n_win_l / n_sel:.3f})  N_win(1p)={int(n_win_1):,} "
          f"({n_win_1 / n_sel:.3f})")

    # (cache, stage, denominator, color, lw, ls, label)
    CURVES = [
        (c1, 3, n_sel, "C0", 1.6, "--",
         "pre-FSI / N$_{sel}$"),
        (cl, 4, n_win_l, "C2", 1.8, "-",
         "post-FSI leading p / N$_{win}$"),
        (c1, 4, n_win_1, "C3", 2.0, "-",
         "post-FSI N$_p$=1 / N$_{win}$"),
    ]

    fig, axes = new_panels(ncols=(3 if shells else 2), nrows=1, sharey=False)
    if shells:
        ax_em, ax_psh, ax_ssh = axes
    else:
        ax_em, ax_pm = axes

    # ---- E_m spectrum ----------------------------------------------------
    (dem, dsf, dstat, dtot), em_dlab = dutta_em_target()
    y_tab = table_em(table, E_EDGES)
    if tune in TABLE_TUNES:
        ax_em.stairs(y_tab, E_EDGES, color="C1", lw=1.0, linestyle="--",
                     alpha=0.8, zorder=3, label=f"table {table_stem}")
    ss = {}
    for cc, s, n_norm, color, lw, ls, lab in CURVES:
        y = mc_em(cc, s, n_norm)
        ss[lab] = strength_em(y)
        ax_em.stairs(y, E_EDGES, color=color, lw=lw, linestyle=ls,
                     zorder=5, label=lab)
    ax_em.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6",
                   elinewidth=3, alpha=0.8, zorder=8)
    ax_em.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black",
                   capsize=2, zorder=9, label=em_dlab)
    print("  E panel strengths: "
          + "  ".join(f"{lab}={v:.3f}" for lab, v in ss.items())
          + f"  data={strength_em(dsf):.3f}")
    style_axis(ax_em, title=rf"{CFG['name']} $E_m$ spectrum",
               xlabel=r"$E_m+T_{rec}$  [MeV]",
               ylabel=r"$Z\cdot$ d$N/$d$E\,/\,N$   [MeV$^{-1}$]",
               logx=False, logy=False, ymin=None)
    ax_em.set_xlim(0, 85)
    ax_em.set_ylim(0, CFG["em_ymax"])
    ax_em.legend(fontsize=FS_LEGEND - 4, frameon=False, loc="center right")

    # ---- folded |p_m|, per-shell variant (original fig 6 data) -----------
    if shells:
        for ax, stem, e_win, title, leg_loc in [
            (ax_psh, "fig6_top_q1p2", (10.0, 25.0),
             "C12 folded p-shell (10–25 MeV)", "lower left"),
            (ax_ssh, "fig6_bot_q1p2", (30.0, 50.0),
             "C12 folded s-shell (30–50 MeV)", "upper right"),
        ]:
            dx, dy, de = dutta_pm(stem)
            yt, k_edges = table_pm_density(table, e_win)
            if tune in TABLE_TUNES:
                ax.stairs(yt, k_edges, color="C1", lw=1.0, linestyle="--",
                          alpha=0.8, zorder=3, label=f"table {table_stem}")
            ys = []
            for cc, s, n_norm, color, lw, ls, lab in CURVES:
                y = mc_pm_density(cc, s, e_win, n_norm)
                ys.append(y)
                ax.stairs(y, K_EDGES, color=color, lw=lw, linestyle=ls,
                          zorder=5, label=lab)
            ax.errorbar(dx, dy, yerr=de, fmt="s", ms=5, color="black",
                        capsize=2, zorder=9, label="Dutta L+R")
            s_data = float((4.0 * np.pi * dx ** 2 * dy).sum() * 40.0)
            print(f"  {title}: data={s_data:.3f}  "
                  + "  ".join(f"{lab}={strength_pm(y, K_EDGES):.3f}"
                              for (_, _, _, _, _, _, lab), y
                              in zip(CURVES, ys)))
            style_axis(ax, title=title, xlabel=r"$|p_m|$  [MeV/c]",
                       ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                       logx=False, ymin=None, logy=True)
            ax.set_xlim(0, 330)
            plot_sel = K_EDGES[1:] <= 330.0
            top = 1.5 * max([y[plot_sel].max() for y in ys]
                            + [yt[k_edges[1:] <= 330.0].max(),
                               (dy + de).max()])
            ax.set_ylim(top / 1e3, top)
            ax.legend(fontsize=FS_LEGEND - 4, frameon=False, loc=leg_loc)

        fig.suptitle(f"Dutta E91-013 vs simulated {tune} "
                     f"({TUNE_GS[tune]})\n"
                     "qel && hit p, NO $Q^2$ cut; mixed normalizations; "
                     "data at publ. scale",
                     fontsize=FS_SUPTITLE - 2)
        fig.tight_layout()
        out = (OUT_DIR
               / f"em_folded_pm_sim_combo_shells_{CFG['tlow']}_{tune}.png")
        fig.savefig(out, dpi=DPI)
        print("wrote", out)
        return

    # ---- folded |p_m| on the full E window -------------------------------
    E_WIN = (0.0, 80.0)
    dx, dy, de, pm_dlab = pm_full_data(dem, dsf)

    yt, k_edges = table_pm_density(table, E_WIN)
    if tune in TABLE_TUNES:
        ax_pm.stairs(yt, k_edges, color="C1", lw=1.0, linestyle="--",
                     alpha=0.8, zorder=3, label=f"table {table_stem}")
    ys = []
    for cc, s, n_norm, color, lw, ls, lab in CURVES:
        y = mc_pm_density(cc, s, E_WIN, n_norm)
        ys.append(y)
        ax_pm.stairs(y, K_EDGES, color=color, lw=lw, linestyle=ls,
                     zorder=5, label=lab)
    ax_pm.errorbar(dx, dy, yerr=de, fmt="s", ms=5, color="black",
                   capsize=2, zorder=9, label=pm_dlab)
    s_data = float((4.0 * np.pi * dx ** 2 * dy).sum() * 40.0)
    print(f"  pm panel (E 0–80): data={s_data:.3f}  "
          + "  ".join(f"{lab}={strength_pm(y, K_EDGES):.3f}"
                      for (_, _, _, _, _, _, lab), y in zip(CURVES, ys)))
    style_axis(ax_pm,
               title=rf"{CFG['name']} folded $|p_m|$ ($E_m$ 0–80 MeV)",
               xlabel=r"$|p_m|$  [MeV/c]",
               ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
               logx=False, ymin=None, logy=True)
    ax_pm.set_xlim(0, 330)
    plot_sel = K_EDGES[1:] <= 330.0
    top = 1.5 * max([y[plot_sel].max() for y in ys]
                    + [yt[k_edges[1:] <= 330.0].max(), (dy + de).max()])
    ax_pm.set_ylim(top / 1e3, top)
    ax_pm.legend(fontsize=FS_LEGEND - 4, frameon=False, loc="lower left")

    fig.suptitle(f"Dutta E91-013 vs simulated {tune} "
                 f"({TUNE_GS[tune]})\n"
                 "qel && hit p, NO $Q^2$ cut; mixed normalizations; "
                 "data at publ. scale",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"em_folded_pm_sim_combo_{CFG['tlow']}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


def main_grid():
    """--combo for ALL FOUR tunes in one figure: a len(TUNE_ORDER) x 2
    grid, one tune per row, left column = E_m spectrum, right column =
    folded |p_m| on the full E window [0, 80) — per row exactly the
    main_combo curves, normalizations and data. Paper layout: 3:4 (h:w)
    panels with the rows TOUCHING (hspace = 0), no suptitle and no panel
    titles (the tune tag sits inside each E_m panel), x tick labels on
    the bottom row only, and ONE log scale shared by the whole |p_m|
    column so the rows compare directly."""
    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MaxNLocator

    table_stem, table = load_table()
    (dem, dsf, dstat, dtot), em_dlab = dutta_em_target()
    E_WIN = (0.0, 80.0)
    dx, dy, de, pm_dlab = pm_full_data(dem, dsf)
    y_tab = table_em(table, E_EDGES)
    yt, kt_edges = table_pm_density(table, E_WIN)

    nrows = len(GRID_TUNES)
    # 3:4 (h:w) panels, rows touching: margins fixed in inches and turned
    # into fractions by hand (tight_layout would reopen the row gap)
    PW, PH = 5.0, 3.75
    ML, MR, MT, MB, WGAP = 1.0, 0.15, 0.15, 0.55, 1.0
    figw = ML + 2 * PW + WGAP + MR
    figh = MT + nrows * PH + MB
    fig, ax2d = plt.subplots(nrows, 2, figsize=(figw, figh))
    fig.subplots_adjust(left=ML / figw, right=1.0 - MR / figw,
                        bottom=MB / figh, top=1.0 - MT / figh,
                        wspace=WGAP / PW, hspace=0.0)
    axes = list(ax2d.ravel())

    pm_axes, pm_tops = [], []
    plot_sel = K_EDGES[1:] <= 330.0
    for irow, tune in enumerate(GRID_TUNES):
        ax_em, ax_pm = axes[2 * irow], axes[2 * irow + 1]
        bottom = irow == nrows - 1
        c1 = load_cache(tune, "1p")
        cl = load_cache(tune, "leading")
        n_sel = float(c1["n_sel"][0])

        def n_win(c):
            with np.errstate(invalid="ignore"):
                m = (np.isfinite(c["E4r"]) & (c["E4r"] >= 0.0)
                     & (c["E4r"] < 80.0) & (c["p4"] < PM_MAX))
            return float(m.sum())

        n_win_l, n_win_1 = n_win(cl), n_win(c1)
        print(f"  [{tune}] N_sel={int(n_sel):,}  "
              f"N_win(leading)={int(n_win_l):,} ({n_win_l / n_sel:.3f})  "
              f"N_win(1p)={int(n_win_1):,} ({n_win_1 / n_sel:.3f})")
        curves = [
            (c1, 3, n_sel, "C0", 1.6, "--", "pre-FSI / N$_{sel}$"),
            (cl, 4, n_win_l, "C2", 1.8, "-",
             "post-FSI leading p / N$_{win}$"),
            (c1, 4, n_win_1, "C3", 2.0, "-",
             "post-FSI N$_p$=1 / N$_{win}$"),
        ]

        # ---- E_m panel ----------------------------------------------------
        if tune in TABLE_TUNES:
            ax_em.stairs(y_tab, E_EDGES, color="C1", lw=1.0, linestyle="--",
                         alpha=0.8, zorder=3)
        ss = {}
        for cc, s, n_norm, color, lw, ls, lab in curves:
            y = mc_em(cc, s, n_norm)
            ss[lab] = strength_em(y)
            ax_em.stairs(y, E_EDGES, color=color, lw=lw, linestyle=ls,
                         zorder=5)
        ax_em.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6",
                       elinewidth=3, alpha=0.8, zorder=8)
        ax_em.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black",
                       capsize=2, zorder=9)
        ax_em.text(0.97, 0.97, f"{tune}\n{TUNE_GS[tune]}",
                   transform=ax_em.transAxes, ha="right", va="top",
                   fontsize=FS_LEGEND, zorder=10)
        print("    E strengths: "
              + "  ".join(f"{lab}={v:.3f}" for lab, v in ss.items())
              + f"  data={strength_em(dsf):.3f}")
        style_axis(ax_em,
                   xlabel=r"$E_m+T_{rec}$  [MeV]" if bottom else None,
                   ylabel=r"$Z\cdot$ d$N/$d$E\,/\,N$   [MeV$^{-1}$]",
                   logx=False, logy=False, ymin=None)
        ax_em.set_xlim(0, 85)
        ax_em.set_ylim(0, CFG["em_ymax"])
        # rows touch: drop the top tick label so it can't collide with
        # the "0.0" of the panel above at the shared border (steps = the
        # AutoLocator set, else MaxNLocator picks 0.08-sized ticks here)
        ax_em.yaxis.set_major_locator(
            MaxNLocator(steps=[1, 2, 2.5, 5, 10], prune="upper"))

        # ---- |p_m| panel (full E window) -----------------------------------
        if tune in TABLE_TUNES:
            ax_pm.stairs(yt, kt_edges, color="C1", lw=1.0, linestyle="--",
                         alpha=0.8, zorder=3)
        ys = []
        for cc, s, n_norm, color, lw, ls, lab in curves:
            y = mc_pm_density(cc, s, E_WIN, n_norm)
            ys.append(y)
            ax_pm.stairs(y, K_EDGES, color=color, lw=lw, linestyle=ls,
                         zorder=5)
        ax_pm.errorbar(dx, dy, yerr=de, fmt="s", ms=5, color="black",
                       capsize=2, zorder=9)
        s_data = float((4.0 * np.pi * dx ** 2 * dy).sum() * 40.0)
        print(f"    pm strengths: data={s_data:.3f}  "
              + "  ".join(f"{lab}={strength_pm(y, K_EDGES):.3f}"
                          for (_, _, _, _, _, _, lab), y
                          in zip(curves, ys)))
        style_axis(ax_pm, xlabel=r"$|p_m|$  [MeV/c]" if bottom else None,
                   ylabel=r"$\int_{E\,\rm win} P\,dE_m$   [MeV$^{-3}$]",
                   logx=False, ymin=None, logy=True)
        ax_pm.set_xlim(0, 330)
        pm_tops.append(1.5 * max([y[plot_sel].max() for y in ys]
                                 + [yt[kt_edges[1:] <= 330.0].max(),
                                    (dy + de).max()]))
        pm_axes.append(ax_pm)
        if not bottom:
            ax_em.tick_params(labelbottom=False)
            ax_pm.tick_params(labelbottom=False)

    # one shared |p_m| scale containing every row's own 3-decade window
    pm_top, pm_bot = max(pm_tops), min(pm_tops) / 1e3
    for ax in pm_axes:
        ax.set_ylim(pm_bot, pm_top)

    # legends once, on the top row (proxy handles — row 1 has no table curve)
    axes[0].legend(handles=[
        Line2D([], [], color="C1", lw=1.0, ls="--", alpha=0.8,
               label=f"table {table_stem}"),
        Line2D([], [], color="C0", lw=1.6, ls="--",
               label="pre-FSI / N$_{sel}$"),
        Line2D([], [], color="C2", lw=1.8,
               label="post-FSI leading p / N$_{win}$"),
        Line2D([], [], color="C3", lw=2.0,
               label="post-FSI N$_p$=1 / N$_{win}$"),
        Line2D([], [], color="black", marker="s", ls="none", ms=5,
               label=em_dlab),
    ], fontsize=FS_LEGEND - 4, frameon=False, loc="center right")
    axes[1].legend(handles=[
        Line2D([], [], color="black", marker="s", ls="none", ms=5,
               label=pm_dlab),
    ], fontsize=FS_LEGEND - 4, frameon=False, loc="lower left")

    out = OUT_DIR / f"em_folded_pm_sim_combo_grid_{CFG['tlow']}{TAG}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="C12", choices=sorted(TGT))
    ap.add_argument("--tune", default="GEM26_22b_05_000",
                    choices=sorted(TUNE_GS))
    ap.add_argument("--nsel", default="sel",
                    choices=["sel", "postfsi", "postwin"],
                    help="postfsi: normalize the MC by the events after "
                         "FSI (a surviving proton) instead of N_sel; "
                         "postwin: by the post-FSI events inside the "
                         "window (E_m+T_rec in [0,80), p_m < 300)")
    ap.add_argument("--proton-sel", default="1p", choices=["1p", "leading"],
                    help="leading: stage 4 = leading FS proton of any "
                         ">=1p event (reads the _leading cache)")
    ap.add_argument("--combo", action="store_true",
                    help="mixed-normalization summary (table, pre/N_sel, "
                         "post leading/N_postFSI, post 1p/N_win); "
                         "--nsel/--proton-sel are ignored")
    ap.add_argument("--shells", action="store_true",
                    help="with --combo (C12 only): per-shell |p_m| panels "
                         "with the ORIGINAL folded fig 6 data (no "
                         "gap-fill scale); writes the _combo_shells figure")
    ap.add_argument("--grid", action="store_true",
                    help="with --combo: ALL FOUR tunes in one 4x2 grid "
                         "(rows = tunes, cols = E_m | folded |p_m|), no "
                         "titles; --tune is ignored; writes the "
                         "_combo_grid figure")
    ap.add_argument("--grid-tunes", nargs="+", default=None,
                    choices=sorted(TUNE_GS),
                    help="with --combo --grid: row tunes in order (default: "
                         "the four campaign tunes)")
    ap.add_argument("--tag", default="",
                    help="output-stem tag for a --grid-tunes grid, e.g. _incl")
    args = ap.parse_args()
    CFG = dict(TGT[args.target], name=args.target)
    if args.grid_tunes:
        GRID_TUNES = args.grid_tunes
    TAG = args.tag
    if args.shells and (not args.combo or args.target != "C12"):
        raise SystemExit("--shells goes with --combo and C12 only")
    if args.grid and (not args.combo or args.shells):
        raise SystemExit("--grid goes with --combo (and not --shells)")
    if args.combo:
        if args.grid:
            main_grid()
        else:
            main_combo(args.tune, args.shells)
    else:
        if args.target != "C12":
            raise SystemExit("the per-variant figures are C12-only; "
                             "use --combo for Fe56")
        main(args.tune, args.nsel, args.proton_sel)

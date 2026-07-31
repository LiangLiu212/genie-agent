"""Four-stage |p_miss| ladder with the Dutta Q^2 cut, per target/tune.

The missing-MOMENTUM analogue of make_emiss_ladder_q2cut.py: the same four
stages (1 input table, 2 struck-nucleon record |p_n|, 3 pre-FSI primary
proton |p_p - q|, 4 post-FSI proton |p_p - q|), but projected onto |p_m|
with the E_m window applied instead of onto E_m with the p_m window:

    stage s histogram:  |p_s|, restored E_s + T_rec inside the E window
    stage 1 table:      n_win(k) = Z * int_{E win} 4pi k^2 P(k,E) dE

The E window is matched per target to the Dutta p_m data overlaid on every
panel (folded L+R = full |p_m| density, published scale, weighted 4pi p_m^2
onto the occupancy axis):

    Fe56: fig 7  (Q^2 = 1.2), E_m < 80 MeV
    C12:  fig 6 top+bottom summed (Q^2 = 1.28), E_m 10-25 (+) 30-50 MeV

so each panel's strength is directly comparable to the data with no window
mismatch (the folded-data convention: results/normalization/README.md).

Reads the ladder caches built by make_emiss_ladder_q2cut.py (run that first;
--proton-sel 1p reads/writes the v0.3 caches, where stage 4 = the unique
proton of exactly-one-proton events). Occupancy normalization
Z*hist/(N_sel*dk) with N_sel = the windowed selection count and the table's
native 20 MeV/c bins. Stage 2 also shows the unwindowed record (dotted) --
for GEM21/SuSA the record E is negative and the window empties the stage.

Figures: results/prd-analyzer-v0.<2|3>/pm_ladder_<target>_<tune>.png.

Usage:
  pixi run python results/template/make_pmiss_ladder_q2cut.py --target Fe56 --all-tunes --proton-sel 1p
  pixi run python results/template/make_pmiss_ladder_q2cut.py --target C12  --all-tunes --proton-sel 1p
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"

PROTON_SEL = "leading"          # or "1p": stage 4 = exactly one FS proton
DK = 20.0                       # native table k grid [MeV/c]
EDGES = np.arange(0.0, 820.0 + 1.0, DK)
PM_PLOT = 330.0                 # plotted |p_m| range (data reach 300)
PM_SUM = 320.0                  # strength sums, aligned with the data grid

# tune -> (has 2D SF table, ground-state label stem)
TUNE_GS = {
    "GEM26_11a_05_000": (False, "LocalFGM"),
    "GEM26_22a_05_000": (True,  "SpectralFunc"),
    "GEM26_22b_05_000": (True,  "SpectralFunc"),
    "GEM21_11a_05_000": (False, "LocalFGM"),
}


def _m_rec_c12():
    from acceptance import M_REC       # B11 [GeV], v0 value (matches caches)
    return M_REC


def _dutta_fe56():
    """fig7 folded L+R: full |p_m| density on the published scale."""
    x, y, _, e = np.loadtxt(DATA_DIR / "fig7_q1p2.dat", unpack=True)
    m = x > 0
    return x[m], 2.0 * y[m], 2.0 * e[m]


def _dutta_c12():
    """fig6 top+bottom summed, then folded L+R (windows 10-25 (+) 30-50)."""
    x, y_p, _, e_p = np.loadtxt(DATA_DIR / "fig6_top_q1p2.dat", unpack=True)
    _, y_s, _, e_s = np.loadtxt(DATA_DIR / "fig6_bot_q1p2.dat", unpack=True)
    m = x > 0
    return x[m], 2.0 * (y_p + y_s)[m], 2.0 * np.sqrt(e_p ** 2 + e_s ** 2)[m]


# per-target configuration (E windows match the overlaid data)
TGT = {
    "Fe56": dict(
        Z=26, tgt_pdg=1000260560,
        m_rec_gev=51.1616880,          # Mn55, install genie_pdg_table.txt
        e_windows=[(0.0, 80.0)], win_label=r"$E_m+T_{rec}$ < 80 MeV",
        dutta=_dutta_fe56, data_label="Dutta Fig. 7 L+R (publ. scale)",
    ),
    "C12": dict(
        Z=6, tgt_pdg=1000060120,
        m_rec_gev=None,                # B11 from acceptance.M_REC
        e_windows=[(10.0, 25.0), (30.0, 50.0)],
        win_label=r"$E_m+T_{rec}$ 10–25 $\cup$ 30–50 MeV",
        dutta=_dutta_c12, data_label="Dutta Fig. 6 p+s L+R (publ. scale)",
    ),
}


def load_table(target):
    """Occupancy-normalized (integral = Z) 22a/22b Benhar table."""
    cfg = TGT[target]
    path = resolve_sf_table("GEM26_22a_05_000", cfg["tgt_pdg"], 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    P = S / raw                        # int 4pi k^2 P dk dE = 1
    print(f"input table {path.name}: raw 4pi k^2 integral = {raw:.3f}; "
          f"occupancy scale Z={cfg['Z']}")
    return path.stem, (k, E, k_edges, P, dk, dE)


def n_windowed(table, Z, e_windows):
    """n_win(k) = Z * int_{E win} 4pi k^2 P dE, partial E bins clipped."""
    k, E, k_edges, P, dk, dE = table
    ov = np.zeros_like(E)
    for lo, hi in e_windows:
        ov += np.clip(np.minimum(E + dE / 2.0, hi)
                      - np.maximum(E - dE / 2.0, lo), 0.0, None)
    return Z * 4.0 * np.pi * (k ** 2) * (P * ov[None, :]).sum(axis=1), k_edges


def in_windows(Er, e_windows):
    m = np.zeros(Er.shape, dtype=bool)
    for lo, hi in e_windows:
        m |= (Er >= lo) & (Er < hi)
    return m & np.isfinite(Er)


def occ_hist(p, n_sel, Z):
    cnt, _ = np.histogram(p[np.isfinite(p)], bins=EDGES)
    return Z * cnt / (n_sel * DK)


def strength(y, edges, pmax=PM_SUM):
    sel = edges[1:] <= pmax + 1e-9
    return float(y[sel].sum() * DK)


def make_figure(target, tune, table_stem, table, dutta):
    cfg = TGT[target]
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else _m_rec_c12()
    tlow = target.lower()
    cache = CACHE_ROOT / f"ladder_{tlow}" / f"{tune}.npz"
    if not cache.exists():
        raise SystemExit(f"missing cache {cache} — build it first with "
                         "make_emiss_ladder_q2cut.py"
                         + (" --proton-sel 1p" if PROTON_SEL == "1p" else ""))
    c = dict(np.load(cache))
    n_sel = float(c["n_sel"][0])
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):          # restored axis: E_s + p_s^2/(2 M_rec)
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)

    has_table = TUNE_GS[tune][0]
    y_in = k_edges = None
    if has_table:
        y_in, k_edges = n_windowed(table, cfg["Z"], cfg["e_windows"])
    dx, dy, de = dutta                # folded density [MeV^-3], publ. scale
    w = 4.0 * np.pi * dx ** 2         # onto the occupancy dN/dp axis
    s_data = float((dy * dx ** 2).sum() * 4.0 * np.pi * 40.0)

    h, h2_all = {}, occ_hist(c["p2"], n_sel, cfg["Z"])
    for s in (2, 3, 4):
        win = in_windows(c[f"E{s}r"], cfg["e_windows"])
        h[s] = occ_hist(np.where(win, c[f"p{s}"], np.nan), n_sel, cfg["Z"])

    print(f"[{tune}] windowed |p_m| ladder ({cfg['win_label']}, "
          f"strengths |p_m|<{PM_SUM:.0f}):")
    if y_in is not None:
        print(f"  I1(table)={strength(y_in, k_edges):.3f}", end="  ")
    print(f"I(data)={s_data:.3f}  "
          + "  ".join(f"I{s}={strength(h[s], EDGES):.3f}" for s in (2, 3, 4))
          + f"  I4/I3={strength(h[4], EDGES) / max(strength(h[3], EDGES), 1e-12):.3f}")

    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    TITLES = ["1 — input table  $n_{win}(k)$",
              "2 — struck nucleon (record),  $|p_n|$",
              "3 — pre-FSI primary proton,  $|\\vec{p}_p-\\vec{q}\\,|$",
              "4 — post-FSI proton,  $|\\vec{p}_p-\\vec{q}\\,|$"
              if PROTON_SEL == "1p" else
              "4 — post-FSI leading proton,  $|\\vec{p}_p-\\vec{q}\\,|$"]

    def draw_data(ax, with_label=False):
        ax.errorbar(dx, w * dy, yerr=w * de, fmt="s", ms=4, color="black",
                    capsize=2, zorder=9,
                    label=cfg["data_label"] if with_label else None)

    ax = axes[0]
    if y_in is not None:
        ax.stairs(y_in, k_edges, color="C1", linewidth=2.0, zorder=4,
                  label=f"Benhar SF {table_stem} (input)")
    else:
        ax.annotate(f"{TUNE_GS[tune][1]}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="folded data = full $|p_m|$ density",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if y_in is not None:
            ax.stairs(y_in, k_edges, color="C1", linewidth=1.0, linestyle="--",
                      alpha=0.8, zorder=2)
        if s == 2:
            ax.stairs(h2_all, EDGES, color="0.5", linewidth=1.2,
                      linestyle=":", zorder=3, label="record, no $E_m$ window")
            ax.legend(fontsize=FS_LEGEND - 3, loc="upper right")
        ax.stairs(h[s], EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax)

    if tune == "GEM21_11a_05_000":
        axes[1].annotate("SuSA record: $E$ restored $<0$,\n"
                         "outside every $E_m$ window\n(dotted = unwindowed)",
                         xy=(0.30, 0.45), xycoords="axes fraction",
                         fontsize=FS_LEGEND - 3, color="0.35")
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title=("thin dashed: input table"
                          if y_in is not None else None),
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    ymax = 1.15 * max([h[s][EDGES[1:] <= PM_PLOT].max() for s in (2, 3, 4)]
                      + [(w * (dy + de)).max()]
                      + ([y_in[k_edges[1:] <= PM_PLOT].max()]
                         if y_in is not None else [])
                      + [h2_all[EDGES[1:] <= PM_PLOT].max()])
    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$|p_m|$  [MeV/c]" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, PM_PLOT)
        ax.set_ylim(0, ymax)
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$|p_m|\,/\,N_{sel}$   [(MeV/c)$^{-1}$]",
                          fontsize=FS_LABEL)

    fig.suptitle(f"{target} $|p_m|$ ladder — {tune}  ({TUNE_GS[tune][1]})\n"
                 "qel && hit p && $Q^2=1.28\\pm5\\%$"
                 + (" && N$_p$=1" if PROTON_SEL == "1p" else "")
                 + "; " + cfg["win_label"],
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"pm_ladder_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TGT))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_GS))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--proton-sel", default="leading", choices=["leading", "1p"],
                    help="1p: stage 4 = exactly one FS proton, reads/writes v0.3")
    args = ap.parse_args()
    PROTON_SEL = args.proton_sel
    if PROTON_SEL == "1p":
        CACHE_ROOT = REPO / "results/prd-analyzer-v0.3/cache"
        OUT_DIR = REPO / "results/prd-analyzer-v0.3"

    apply_style()
    table_stem, table = load_table(args.target)
    dutta = TGT[args.target]["dutta"]()
    for tune in (sorted(TUNE_GS) if args.all_tunes else [args.tune]):
        make_figure(args.target, tune, table_stem, table, dutta)

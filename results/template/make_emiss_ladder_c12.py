"""C12 four-stage E_miss ladder on the restored (input-table) axis vs Dutta Fig. 9.

C12 sibling of make_emiss_ladder_fe56.py, same four-tune pattern for the
electron_c12_scattering.md note. IMPORTANT provenance difference: the June-2026
C12 grid samples (EMQE genlist) have been PURGED from scratch dCache, so this
script reads the surviving prd-analyzer-v0.1 ladder caches
(results/prd-analyzer-v0.1/cache/ladder/<model>.npz, built 2026-06 by
results/prd-analyzer-v0/build_cache_ladder.py from 2M events/model) instead of
streaming. Model key -> tune: LFG=GEM26_11a_05_000, SF=GEM26_22a_05_000,
UnifiedQEL=GEM26_22b_05_000, SuSAv2=GEM21_11a_05_000 (samples.py).

Stages (cache formulas = build_cache_ladder.py, remnant B11; selection
hitnuc==2212, all events are QEL by the EMQE genlist):
  1  input table f_{k<300}(E)  from pke12_tot.data (proton-occupancy, Z=6);
     LocalFGM tunes (11a, GEM21) have no 2D SF table -> data-only panel 1
  2  struck nucleon (record), restored  E2 + T_rec(p_n)  = m_N - E_n
  3  pre-FSI primary proton,  restored  E3 + T_rec(p_m)  = omega - T_p
  4  post-FSI leading proton, restored  E4 + T_rec(p_m)  = omega - T_p
Occupancy normalization y = Z*hist(p_s<300)/(N_hitp*5 MeV). Dutta Fig. 9
(fig9_q1p2.dat) overlaid at its published scale (integral 6.080 ~ Z=6), with
the v0 fig9_common error model (2% pt-to-pt (+) 5% model, pixel-measured
p-shell bars). S_p(C12->B11+p) = 15.96 MeV (masses from genie_pdg_table.txt).
Unlike Fe56, the C12 table E grid (edges 0,5,...,400) is ALIGNED with the
data/plot grid -- no half-bin offset.

Usage: pixi run python results/template/make_emiss_ladder_c12.py [--tune T | --all-tunes]
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
from fig9_common import load_dutta                            # noqa: E402
from acceptance import M_REC                                  # B11 [GeV], v0 value
                                                              # (matches the caches)

REPO = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO / "results/prd-analyzer-v0.1/cache/ladder"
OUT_DIR = REPO / "results/prd-analyzer-v0.1"

# tune -> (v0 cache model key, has 2D SF table, ground-state label)
RUNS = {
    "GEM26_11a_05_000": ("LFG",        False, "LocalFGM"),
    "GEM26_22a_05_000": ("SF",         True,  "SpectralFunc (pke12_tot)"),
    "GEM26_22b_05_000": ("UnifiedQEL", True,  "SpectralFunc (pke12_tot)"),
    "GEM21_11a_05_000": ("SuSAv2",     False, "LocalFGM"),
}

Z = 6
TGT_PDG = 1000060120
M_MEV = M_REC * 1000.0

PM_MAX = 300.0
BINW = 5.0
EDGES = np.arange(0.0, 85.0, 5.0)


def load_table(tune):
    path = resolve_sf_table(tune, TGT_PDG, 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    P = S * (Z / raw) / Z
    print(f"input table {path.name}: raw 4pi k^2 integral = {raw:.3f}; "
          f"rescaled to proton occupancy Z={Z}")
    return k, E, P, dk, dE


def f_restricted(k, P, dk, kmax=PM_MAX):
    sel = (k + dk / 2.0) <= kmax + 1e-9
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def rebin(E, f, dE, edges):
    """Spread each table column uniformly over its native bin (Fe56 lesson;
    for C12 the grids are aligned so this reduces to a straight rebin)."""
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        ov = np.clip(np.minimum(E + dE / 2.0, hi) - np.maximum(E - dE / 2.0, lo),
                     0.0, None)
        out[i] = (f * ov).sum() / (hi - lo)
    return out


def occ_hist(E, p, n_sel):
    win = p < PM_MAX
    cnt, _ = np.histogram(E[win], bins=EDGES)
    return Z * cnt / (n_sel * BINW)


def make_figure(tune, dutta, table):
    model, has_table, gs = RUNS[tune]
    c = dict(np.load(CACHE_DIR / f"{model}.npz"))
    n_sel = float(c["n_hitp"][0])
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * M_MEV)

    y_in = None
    if has_table:
        k, E, P, dk, dE = table
        y_in = rebin(E, f_restricted(k, P, dk), dE, EDGES)
    dem, dsf, dstat, dtot = dutta

    h = {s: occ_hist(c[f"E{s}r"], c[f"p{s}"], n_sel) for s in (2, 3, 4)}
    w2 = c["p2"] < PM_MAX
    print(f"[{tune}] (cache '{model}', N_hitp={int(n_sel):,} of "
          f"{int(c['ntot'][0]):,}) restored ladder:")
    if y_in is not None:
        print(f"  I1(table,k<300)={y_in.sum() * BINW:.3f}", end="  ")
    print("  ".join(f"I{s}r={h[s].sum() * BINW:.3f}" for s in (2, 3, 4))
          + f"  I4r/I3r={h[4].sum() / max(h[3].sum(), 1e-12):.3f}")
    print(f"  stage-2 record: median {np.median(c['E2r'][w2]):.2f} MeV, "
          f"p5-p95 [{np.percentile(c['E2r'][w2], 5):.2f}, "
          f"{np.percentile(c['E2r'][w2], 95):.2f}] MeV")

    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    TITLES = ["1 — input table  $f_{k<300}(E)$",
              "2 — struck nucleon (record),  $m_N-E_n$",
              "3 — pre-FSI primary proton,  $\\omega-T_p$",
              "4 — post-FSI leading proton,  $\\omega-T_p$"]

    def draw_data(ax, with_label=False):
        ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                    zorder=9,
                    label="Dutta Fig. 9 (publ. scale)" if with_label else None)

    ax = axes[0]
    if y_in is not None:
        ax.stairs(y_in, EDGES, color="C1", linewidth=2.0, zorder=4,
                  label="Benhar SF pke12_tot (input)")
    else:
        ax.annotate(f"{gs}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="table axis = restored axis",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if y_in is not None:
            ax.stairs(y_in, EDGES, color="C1", linewidth=1.0, linestyle="--",
                      alpha=0.8, zorder=2)
        ax.stairs(h[s], EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax)

    med2 = float(np.median(c["E2r"][w2]))
    pk = max(h[2].max(), h[3].max())
    if tune == "GEM26_22b_05_000":
        note = ("b-tune record: QELEventGenerator keeps\nthe sampled $w$ — "
                "$m_N-E_n=E_{sampled}$\n(restoration)")
    elif tune == "GEM21_11a_05_000":
        note = ("SuSA record: $m_N-E_n=-T_N<0$,\noff scale left "
                f"(median {med2:.1f} MeV)")
    else:
        note = ("record: FermiMover drops the sampled $w$\n— $\\delta$ at "
                f"$S_p\\approx16$ MeV (off scale:\npeak bin = {pk:.1f})")
    axes[1].annotate(note, xy=(0.28, 0.55), xycoords="axes fraction",
                     fontsize=FS_LEGEND - 3, color="0.35")
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title=("thin dashed: input table\n(data axis: $-T_{rec}$, sub-bin)"
                          if y_in is not None else
                          "(data axis: $-T_{rec}$, sub-bin)"),
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$E_m+T_{rec}$  (MeV)" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 85)
        ax.set_ylim(0, 1.0)          # fixed range, deltas clip (C12 scale)
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$(E_m+T_{rec})\,/\,N_{sel}$   (MeV$^{-1}$)",
                          fontsize=FS_LABEL)

    fig.suptitle(f"C12 restored E$_m$ ladder — {tune}  ({gs})\n"
                 "EMQE, hit p, $p_m<300$ MeV/$c$; Dutta Fig. 9 at publ. scale",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"em_ladder_restored_c12_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(RUNS))
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()

    apply_style()
    dutta = load_dutta()
    table = load_table("GEM26_22a_05_000")
    for t in (list(RUNS) if args.all_tunes else [args.tune]):
        make_figure(t, dutta, table)

"""2D struck-nucleon (P_miss, r) — momentum vs in-nucleus radial position, per tune.

Plot 3 of the per-tune ground-state series (plot 1 = make_sf2d_table.py, the
input table; plot 2 = make_sf2d_events.py, the realized (P_miss, E_rm)): the
struck-nucleon momentum against the radial position r = |X4| the record carries,
in the Fe56 full-EM t05 campaign samples (e- 2.445 GeV, genlist EM, grid jobs
of 2026-07-16).

Why this plot: r is set by VertexGenerator, the momentum by the nuclear model,
and whether the two are CORRELATED in the record is a chain property — LocalFGM
ties k_F to the local density k_F(r), but only a generator that hands the
already-generated vertex radius to `NuclearModel::GenerateNucleon(tgt, r)`
imprints that correlation on the event; SpectralFunc has no r dependence at
all. The per-column profile <p>(r) (overlaid) makes the answer visible: flat =
factorized record, falling = the LFG envelope survived.

Input: the same dump_hitnuc CSVs as plot 2 (pdg,px,py,pz,E,w,scat,r), one per
tune: <dump-dir>/<tune>.csv.

Outputs:
  results/prd-analyzer-v0.1/struck_pr_fe56_<tune>.png       one figure per tune
  results/prd-analyzer-v0.1/struck_pr_fe56_all_t05.png      1x4 comparison, shared color scale
                                            (only with --all-tunes)

Usage:
  pixi run python results/template/make_struck_pr_fe56.py --dump-dir <dir>              # 22b
  pixi run python results/template/make_struck_pr_fe56.py --dump-dir <dir> --all-tunes  # campaign 4
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, FS_LABEL, FS_TITLE, FS_TICK,
                        FS_SUPTITLE, PANEL_SIZE)    # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TUNES = ["GEM26_11a_05_000", "GEM26_22a_05_000",
         "GEM26_22b_05_000", "GEM21_11a_05_000"]
GROUND_STATE = {                      # active Fe56 model per tune (plot 1)
    "GEM26_11a_05_000": "LocalFGM",
    "GEM26_22a_05_000": "SpectralFunc (pke56_tot)",
    "GEM26_22b_05_000": "SpectralFunc (pke56_tot)",
    "GEM21_11a_05_000": "LocalFGM",
}

# momentum on the pke56_tot.data table grid (plots 1-2, comparability);
# radius: 0.2 fm bins to ~1.6x the Fe56 hard-sphere radius
P_EDGES = np.linspace(0.0, 800.0, 41)     # momentum [MeV/c], 40 bins
R_EDGES = np.linspace(0.0, 8.0, 41)       # radius   [fm],    40 bins


def load_hist(csv: Path):
    """CSV from dump_hitnuc -> (H fraction/bin [r, p], profile, counts)."""
    d = np.genfromtxt(csv, delimiter=",", names=True)
    p = np.sqrt(d["px"]**2 + d["py"]**2 + d["pz"]**2) * 1000.0   # MeV/c
    r = d["r"]                                                   # fm
    H, _, _ = np.histogram2d(r, p, bins=[R_EDGES, P_EDGES])
    n = len(p)
    in_range = int(H.sum())
    H = H / H.sum()
    # per-radius-column momentum profile <p>(r), on the unbinned p
    r_ctr = 0.5 * (R_EDGES[:-1] + R_EDGES[1:])
    idx = np.digitize(r, R_EDGES) - 1
    prof = np.full(len(r_ctr), np.nan)
    for i in range(len(r_ctr)):
        m = idx == i
        if m.sum() >= 200:            # keep the profile out of empty tails
            prof[i] = p[m].mean()
    corr = float(np.corrcoef(p, r)[0, 1])
    return H, (r_ctr, prof), {"n_kept": n, "in_range": in_range,
                              "corr": corr, "mean_r": float(r.mean())}


def draw_panel(ax, fig, H, prof, norm, add_cbar=True):
    # orientation: x = missing momentum P_miss (plots 1-2), y = radius r
    Xe, Ye = np.meshgrid(P_EDGES, R_EDGES, indexing="ij")
    Zm = np.ma.masked_less_equal(H.T, 0.0)
    pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
    r_ctr, p_of_r = prof
    ax.plot(p_of_r, r_ctr, "w--", lw=1.8, label=r"$\langle p\rangle(r)$")
    ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
    ax.set_xlim(P_EDGES[0], P_EDGES[-1])
    ax.tick_params(labelsize=FS_TICK)
    if add_cbar:
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    return pc


def single_figure(tune, H, prof, c):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, ax = plt.subplots(figsize=(w * 1.4, h), layout="constrained")
    norm = LogNorm(vmin=H.max() * 1e-6, vmax=H.max())
    draw_panel(ax, fig, H, prof, norm)
    ax.set_ylabel(r"$r$  [fm]", fontsize=FS_LABEL)
    ax.legend(loc="upper right", fontsize=FS_TICK)
    ax.set_title(f"N = {c['n_kept']:,} single-nucleon events,  "
                 f"corr(p, r) = {c['corr']:+.3f}", fontsize=FS_TITLE - 3)
    fig.suptitle(f"Fe56 struck nucleon: momentum vs sampled position\n"
                 f"{tune}  ({GROUND_STATE[tune]}),  e$^-$ 2.445 GeV, genlist EM",
                 fontsize=FS_SUPTITLE - 2)
    out = REPO / "results" / "prd-analyzer-v0.1" / f"struck_pr_fe56_{tune}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


def combined_figure(results):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, len(results), figsize=(w * len(results) * 0.95, h),
                             sharey=True, layout="constrained")
    vmax = max(H.max() for _, H, _, _ in results)
    norm = LogNorm(vmin=vmax * 1e-6, vmax=vmax)
    pc = None
    for ax, (tune, H, prof, c) in zip(axes, results):
        pc = draw_panel(ax, fig, H, prof, norm, add_cbar=False)
        ax.set_title(f"{tune}\n{GROUND_STATE[tune]},  corr = {c['corr']:+.3f}",
                     fontsize=FS_TITLE - 3)
    axes[0].set_ylabel(r"$r$  [fm]", fontsize=FS_LABEL)
    axes[0].legend(loc="upper right", fontsize=FS_TICK)
    cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.02)
    cb.set_label("fraction of events / bin", fontsize=FS_TITLE - 2)
    cb.ax.tick_params(labelsize=FS_TICK)
    fig.suptitle("Fe56 struck nucleon: momentum vs sampled position  "
                 "(e$^-$ 2.445 GeV, genlist EM, t05 tunes, shared color scale)",
                 fontsize=FS_SUPTITLE - 2)
    out = REPO / "results" / "prd-analyzer-v0.1" / "struck_pr_fe56_all_t05.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22b_05_000", choices=TUNES)
    ap.add_argument("--dump-dir", required=True,
                    help="dir with <tune>.csv files from dump_hitnuc")
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()

    apply_style()
    tunes = TUNES if args.all_tunes else [args.tune]
    results = []
    for t in tunes:
        H, prof, c = load_hist(Path(args.dump_dir) / f"{t}.csv")
        print(f"{t}: N={c['n_kept']:,}  in-grid={c['in_range']:,}  "
              f"corr(p,r)={c['corr']:+.3f}  <r>={c['mean_r']:.2f} fm")
        single_figure(t, H, prof, c)
        results.append((t, H, prof, c))
    if args.all_tunes:
        combined_figure(results)

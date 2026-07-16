"""2D ground state P(p, E_rm) realized in the generated events, per tune.

Plot 2 of the per-tune ground-state series (prototype: GEM26_22b_05_000, Fe56).
The event-level counterpart of make_sf2d_table.py (plot 1): the struck-nucleon
momentum and the SAMPLED removal energy w in the Fe56 full-EM t05 campaign
samples (e- 2.445 GeV, genlist EM, grid jobs of 2026-07-16), binned on the SAME
grid as the pke56_tot.data input table so plots 1 and 2 are directly comparable.

Why GHEP dumps and not gst: gst has no removal-energy branch, and the off-shell
En it stores cannot recover w for most events -- FermiMover's default branch
(RES/DIS in all four tunes, QEL in 11a/22a) encodes En = M_A - sqrt(p^2 +
M_rem_gs^2), a pure function of p (verified: inverted w is the constant 10.2 /
11.2 MeV p/n separation energy). Only 22b's QELEventGenerator folds w into En.
The sampled w for EVERY event lives in GHepParticle::RemovalEnergy, so a small
compiled dumper (dump_hitnuc.cxx, GENIE libs) writes per-event CSVs
    pdg,px,py,pz,E,w,scat
from the .ghep.root files, and this script reads those:  <dump-dir>/<tune>.csv.

Outputs:
  results/prd-analyzer-v0.1/sf2d_events_fe56_<tune>.png       one figure per tune
  results/prd-analyzer-v0.1/sf2d_events_fe56_all_t05.png      1x4 comparison, shared color scale
                                            (only with --all-tunes)

Usage:
  pixi run python results/template/make_sf2d_events.py --dump-dir <dir>              # 22b
  pixi run python results/template/make_sf2d_events.py --dump-dir <dir> --all-tunes  # campaign 4
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

# binning = the pke56_tot.data table grid (make_sf2d_table.py), for comparability
E_EDGES = np.linspace(2.5, 402.5, 81)     # removal energy w [MeV],  80 bins
P_EDGES = np.linspace(0.0, 800.0, 41)     # momentum        [MeV/c], 40 bins


def load_hist(csv: Path):
    """CSV from dump_hitnuc -> (H fraction/bin, counts)."""
    d = np.genfromtxt(csv, delimiter=",", names=True)
    p = np.sqrt(d["px"]**2 + d["py"]**2 + d["pz"]**2) * 1000.0   # MeV/c
    w = d["w"] * 1000.0                                          # MeV
    H, _, _ = np.histogram2d(w, p, bins=[E_EDGES, P_EDGES])
    n = len(p)
    in_range = int(H.sum())
    H = H / H.sum()
    return H, {"n_kept": n, "in_range": in_range,
               "frac_p250": float(H[:, P_EDGES[:-1] >= 250.0].sum()),
               "frac_e100": float(H[E_EDGES[:-1] >= 100.0, :].sum())}


def draw_panel(ax, fig, H, norm, add_cbar=True):
    # orientation: x = missing momentum P_miss, y = removal (missing) energy E_miss
    Xe, Ye = np.meshgrid(P_EDGES, E_EDGES, indexing="ij")
    Zm = np.ma.masked_less_equal(H.T, 0.0)
    pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
    ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    if add_cbar:
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    return pc


def single_figure(tune, H, c):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, ax = plt.subplots(figsize=(w * 1.4, h), layout="constrained")
    norm = LogNorm(vmin=H.max() * 1e-6, vmax=H.max())
    draw_panel(ax, fig, H, norm)
    ax.set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)
    ax.set_title(f"N = {c['n_kept']:,} single-nucleon events (sampled w from GHEP)",
                 fontsize=FS_TITLE - 3)
    fig.suptitle(f"Fe56 ground state realized in generated events\n"
                 f"{tune}  ({GROUND_STATE[tune]}),  e$^-$ 2.445 GeV, genlist EM",
                 fontsize=FS_SUPTITLE - 2)
    out = REPO / "results" / "prd-analyzer-v0.1" / f"sf2d_events_fe56_{tune}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


def combined_figure(results):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, len(results), figsize=(w * len(results) * 0.95, h),
                             sharey=True, layout="constrained")
    vmax = max(H.max() for _, H, _ in results)
    norm = LogNorm(vmin=vmax * 1e-6, vmax=vmax)
    pc = None
    for ax, (tune, H, c) in zip(axes, results):
        pc = draw_panel(ax, fig, H, norm, add_cbar=False)
        ax.set_title(f"{tune}\n{GROUND_STATE[tune]}", fontsize=FS_TITLE - 3)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)
    cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.02)
    cb.set_label("fraction of events / bin", fontsize=FS_TITLE - 2)
    cb.ax.tick_params(labelsize=FS_TICK)
    fig.suptitle("Fe56 ground state realized in generated events  "
                 "(e$^-$ 2.445 GeV, genlist EM, t05 tunes, shared color scale)",
                 fontsize=FS_SUPTITLE - 2)
    out = REPO / "results" / "prd-analyzer-v0.1" / "sf2d_events_fe56_all_t05.png"
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
        H, c = load_hist(Path(args.dump_dir) / f"{t}.csv")
        print(f"{t}: N={c['n_kept']:,}  in-grid={c['in_range']:,}  "
              f"P(p>250)={c['frac_p250']:.3f}  P(E>100)={c['frac_e100']:.3f}")
        single_figure(t, H, c)
        results.append((t, H, c))
    if args.all_tunes:
        combined_figure(results)

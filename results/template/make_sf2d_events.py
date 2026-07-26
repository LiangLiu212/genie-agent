"""2D ground state P(p, E_rm) realized in the generated events, per tune.

Plot 2 of the per-tune ground-state series (plot 1 = make_sf2d_table.py): the
struck-nucleon momentum and the SAMPLED removal energy w in the full-EM t05
campaign samples (e- 2.445 GeV, genlist EM; Fe56 = grid jobs of 2026-07-16,
C12 = grid jobs of 2026-07-26), binned on the SAME grid as the target's SF
input table (pke56_tot / pke12_tot, read via make_sf2d_table.read_pke_table)
so plots 1 and 2 are directly comparable.

Why GHEP dumps and not gst: gst has no removal-energy branch, and the off-shell
En it stores cannot recover w for most events -- FermiMover's default branch
(RES/DIS in all four tunes, QEL in 11a/22a) encodes En = M_A - sqrt(p^2 +
M_rem_gs^2), a pure function of p (verified: inverted w is the constant 10.2 /
11.2 MeV p/n separation energy). Only 22b's QELEventGenerator folds w into En.
The sampled w for EVERY event lives in GHepParticle::RemovalEnergy, so a small
compiled dumper (dump_hitnuc.cxx, GENIE libs) writes per-event CSVs
    pdg,px,py,pz,E,w,scat,r
from the .ghep.root files, and this script reads those:  <dump-dir>/<tune>.csv.

Outputs:
  results/prd-analyzer-v0.1/sf2d_events_<target>_<tune>.png    one figure per tune
  results/prd-analyzer-v0.1/sf2d_events_<target>_all_t05.png   1x4 comparison, shared
                                             color scale (only with --all-tunes)

Usage:
  pixi run python results/template/make_sf2d_events.py --dump-dir <dir>              # 22b, Fe56
  pixi run python results/template/make_sf2d_events.py --dump-dir <dir> --all-tunes
  pixi run python results/template/make_sf2d_events.py --dump-dir <dir> --all-tunes --target C12
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "genie-agent")
import numpy as np
from lib.pdg import resolve_pdg                     # noqa: E402
from plot_style import (apply_style, FS_LABEL, FS_TITLE, FS_TICK,
                        FS_SUPTITLE, PANEL_SIZE)    # noqa: E402
from make_sf2d_table import (resolve_ground_state, resolve_sf_table,
                             read_pke_table)        # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TUNES = ["GEM26_11a_05_000", "GEM26_22a_05_000",
         "GEM26_22b_05_000", "GEM21_11a_05_000"]
SF_TUNE = "GEM26_22a_05_000"          # any tune resolving to the 2D SF table


def target_setup(target: str):
    """(E_EDGES, P_EDGES, GROUND_STATE) for a target: grid = its SF table's."""
    pdg = resolve_pdg(target)
    table = resolve_sf_table(SF_TUNE, pdg, 2212)
    _, _, p_edges, E_edges, _ = read_pke_table(table)
    gs = {}
    for t in TUNES:
        model = resolve_ground_state(t, pdg)
        gs[t] = (f"SpectralFunc ({table.stem})"
                 if "genie::SpectralFunc/" in model else "LocalFGM")
    return E_edges, p_edges, gs


def load_hist(csv: Path, E_edges, P_edges):
    """CSV from dump_hitnuc -> (H fraction/bin, counts)."""
    d = np.genfromtxt(csv, delimiter=",", names=True)
    p = np.sqrt(d["px"]**2 + d["py"]**2 + d["pz"]**2) * 1000.0   # MeV/c
    w = d["w"] * 1000.0                                          # MeV
    H, _, _ = np.histogram2d(w, p, bins=[E_edges, P_edges])
    n = len(p)
    in_range = int(H.sum())
    H = H / H.sum()
    return H, {"n_kept": n, "in_range": in_range,
               "frac_p250": float(H[:, P_edges[:-1] >= 250.0].sum()),
               "frac_e100": float(H[E_edges[:-1] >= 100.0, :].sum())}


def draw_panel(ax, fig, H, E_edges, P_edges, norm, add_cbar=True):
    # orientation: x = missing momentum P_miss, y = removal (missing) energy E_miss
    Xe, Ye = np.meshgrid(P_edges, E_edges, indexing="ij")
    Zm = np.ma.masked_less_equal(H.T, 0.0)
    pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
    ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    if add_cbar:
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    return pc


def single_figure(target, tune, H, c, E_edges, P_edges, gs):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, ax = plt.subplots(figsize=(w * 1.4, h), layout="constrained")
    norm = LogNorm(vmin=H.max() * 1e-6, vmax=H.max())
    draw_panel(ax, fig, H, E_edges, P_edges, norm)
    ax.set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)
    ax.set_title(f"N = {c['n_kept']:,} single-nucleon events (sampled w from GHEP)",
                 fontsize=FS_TITLE - 3)
    fig.suptitle(f"{target} ground state realized in generated events\n"
                 f"{tune}  ({gs[tune]}),  e$^-$ 2.445 GeV, genlist EM",
                 fontsize=FS_SUPTITLE - 2)
    out = (REPO / "results" / "prd-analyzer-v0.1" /
           f"sf2d_events_{target.lower()}_{tune}.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


def combined_figure(target, results, E_edges, P_edges, gs):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, len(results), figsize=(w * len(results) * 0.95, h),
                             sharey=True, layout="constrained")
    vmax = max(H.max() for _, H, _ in results)
    norm = LogNorm(vmin=vmax * 1e-6, vmax=vmax)
    pc = None
    for ax, (tune, H, c) in zip(axes, results):
        pc = draw_panel(ax, fig, H, E_edges, P_edges, norm, add_cbar=False)
        ax.set_title(f"{tune}\n{gs[tune]}", fontsize=FS_TITLE - 3)
    axes[0].set_ylabel(r"$E_{\rm miss}$  [MeV]", fontsize=FS_LABEL)
    cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.02)
    cb.set_label("fraction of events / bin", fontsize=FS_TITLE - 2)
    cb.ax.tick_params(labelsize=FS_TICK)
    fig.suptitle(f"{target} ground state realized in generated events  "
                 "(e$^-$ 2.445 GeV, genlist EM, t05 tunes, shared color scale)",
                 fontsize=FS_SUPTITLE - 2)
    out = (REPO / "results" / "prd-analyzer-v0.1" /
           f"sf2d_events_{target.lower()}_all_t05.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22b_05_000", choices=TUNES)
    ap.add_argument("--dump-dir", required=True,
                    help="dir with <tune>.csv files from dump_hitnuc")
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--target", default="Fe56", choices=["Fe56", "C12"])
    args = ap.parse_args()

    apply_style()
    E_edges, P_edges, gs = target_setup(args.target)
    print(f"{args.target} table grid: {len(P_edges)-1} p bins "
          f"[{P_edges[0]:g}, {P_edges[-1]:g}] MeV/c x {len(E_edges)-1} E bins "
          f"[{E_edges[0]:g}, {E_edges[-1]:g}] MeV")
    tunes = TUNES if args.all_tunes else [args.tune]
    results = []
    for t in tunes:
        H, c = load_hist(Path(args.dump_dir) / f"{t}.csv", E_edges, P_edges)
        print(f"{t}: N={c['n_kept']:,}  in-grid={c['in_range']:,}  "
              f"P(p>250)={c['frac_p250']:.3f}  P(E>100)={c['frac_e100']:.3f}")
        single_figure(args.target, t, H, c, E_edges, P_edges, gs)
        results.append((t, H, c))
    if args.all_tunes:
        combined_figure(args.target, results, E_edges, P_edges, gs)

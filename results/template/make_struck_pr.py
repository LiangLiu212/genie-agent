"""2D struck-nucleon (P_miss, r) — momentum vs in-nucleus radial position, per tune.

Plot 3 of the per-tune ground-state series (plot 1 = make_sf2d_table.py, the
input table; plot 2 = make_sf2d_events.py, the realized (P_miss, E_rm)): the
struck-nucleon momentum against the radial position r = |X4| the record
carries, in the full-EM t05 campaign samples (e- 2.445 GeV, genlist EM;
Fe56 = grid jobs of 2026-07-16, C12 = grid jobs of 2026-07-26).

Why this plot: r is set by VertexGenerator, the momentum by the nuclear model,
and whether the two are CORRELATED in the record is a chain property — LocalFGM
ties k_F to the local density k_F(r), but only a generator that hands the
already-generated vertex radius to `NuclearModel::GenerateNucleon(tgt, r)`
imprints that correlation on the event; SpectralFunc has no r dependence at
all. The per-column profile <p>(r) (overlaid) makes the answer visible: flat =
factorized record, falling = the LFG envelope survived.

Input: the same dump_hitnuc CSVs as plot 2 (pdg,px,py,pz,E,w,scat,r), one per
tune: <dump-dir>/<tune>.csv. Momentum binned on the target SF table's p grid;
radius in 0.2 fm bins up to R_MAX[target].

Outputs:
  results/prd-analyzer-v0.1/struck_pr_<target>_<tune>.png      one figure per tune
  results/prd-analyzer-v0.1/struck_pr_<target>_all_t05.png     1x4 comparison, shared
                                             color scale (only with --all-tunes)

Usage:
  pixi run python results/template/make_struck_pr.py --dump-dir <dir>              # 22b, Fe56
  pixi run python results/template/make_struck_pr.py --dump-dir <dir> --all-tunes
  pixi run python results/template/make_struck_pr.py --dump-dir <dir> --all-tunes --target C12
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
OUT_DEFAULT = REPO / "results" / "prd-analyzer-v0.1"
TUNES = ["GEM26_11a_05_000", "GEM26_22a_05_000",
         "GEM26_22b_05_000", "GEM21_11a_05_000"]
SF_TUNE = "GEM26_22a_05_000"          # any tune resolving to the 2D SF table
R_MAX = {"Fe56": 8.0, "C12": 6.0}     # fm, ~1.6x the hard-sphere radius
Q2_CENTER, Q2_FRAC = 1.28, 0.05       # --sel-qel-q2 window (Dutta slice)


def target_setup(target: str):
    """(R_EDGES, P_EDGES, GROUND_STATE) for a target."""
    pdg = resolve_pdg(target)
    table = resolve_sf_table(SF_TUNE, pdg, 2212)
    _, _, p_edges, _, _ = read_pke_table(table)
    r_edges = np.arange(0.0, R_MAX[target] + 1e-9, 0.2)
    gs = {}
    for t in TUNES:
        model = resolve_ground_state(t, pdg)
        gs[t] = (f"SpectralFunc ({table.stem})"
                 if "genie::SpectralFunc/" in model else "LocalFGM")
    return r_edges, p_edges, gs


def load_hist(csv: Path, R_edges, P_edges, sel_qel_q2=False):
    """CSV from dump_hitnuc -> (H fraction/bin [r, p], profile, counts).

    sel_qel_q2: keep only scat==1 (QEL) events inside the Dutta Q^2 window
    (needs the q2 column of the extended dumper)."""
    d = np.genfromtxt(csv, delimiter=",", names=True)
    if sel_qel_q2:
        m = (d["scat"] == 1) & (np.abs(d["q2"] / Q2_CENTER - 1.0) <= Q2_FRAC)
        d = d[m]
    p = np.sqrt(d["px"]**2 + d["py"]**2 + d["pz"]**2) * 1000.0   # MeV/c
    r = d["r"]                                                   # fm
    H, _, _ = np.histogram2d(r, p, bins=[R_edges, P_edges])
    n = len(p)
    in_range = int(H.sum())
    H = H / H.sum()
    # per-radius-column momentum profile <p>(r), on the unbinned p
    r_ctr = 0.5 * (R_edges[:-1] + R_edges[1:])
    idx = np.digitize(r, R_edges) - 1
    prof = np.full(len(r_ctr), np.nan)
    for i in range(len(r_ctr)):
        m = idx == i
        if m.sum() >= 200:            # keep the profile out of empty tails
            prof[i] = p[m].mean()
    corr = float(np.corrcoef(p, r)[0, 1])
    return H, (r_ctr, prof), {"n_kept": n, "in_range": in_range,
                              "corr": corr, "mean_r": float(r.mean())}


def draw_panel(ax, fig, H, prof, R_edges, P_edges, norm, add_cbar=True):
    # orientation: x = missing momentum P_miss (plots 1-2), y = radius r
    Xe, Ye = np.meshgrid(P_edges, R_edges, indexing="ij")
    Zm = np.ma.masked_less_equal(H.T, 0.0)
    pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
    r_ctr, p_of_r = prof
    ax.plot(p_of_r, r_ctr, "w--", lw=1.8, label=r"$\langle p\rangle(r)$")
    ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
    ax.set_xlim(P_edges[0], P_edges[-1])
    ax.tick_params(labelsize=FS_TICK)
    if add_cbar:
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    return pc


def single_figure(target, tune, H, prof, c, R_edges, P_edges, gs,
                  out_dir=OUT_DEFAULT, sel_note=""):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, ax = plt.subplots(figsize=(w * 1.4, h), layout="constrained")
    norm = LogNorm(vmin=H.max() * 1e-6, vmax=H.max())
    draw_panel(ax, fig, H, prof, R_edges, P_edges, norm)
    ax.set_ylabel(r"$r$  [fm]", fontsize=FS_LABEL)
    ax.legend(loc="upper right", fontsize=FS_TICK)
    ax.set_title(f"N = {c['n_kept']:,}{sel_note or ' single-nucleon'} events,  "
                 f"corr(p, r) = {c['corr']:+.3f}", fontsize=FS_TITLE - 3)
    fig.suptitle(f"{target} struck nucleon: momentum vs sampled position\n"
                 f"{tune}  ({gs[tune]}),  e$^-$ 2.445 GeV, genlist EM",
                 fontsize=FS_SUPTITLE - 2)
    out = Path(out_dir) / f"struck_pr_{target.lower()}_{tune}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


def combined_figure(target, results, R_edges, P_edges, gs,
                    out_dir=OUT_DEFAULT, sel_note=""):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, axes = plt.subplots(1, len(results), figsize=(w * len(results) * 0.95, h),
                             sharey=True, layout="constrained")
    vmax = max(H.max() for _, H, _, _ in results)
    norm = LogNorm(vmin=vmax * 1e-6, vmax=vmax)
    pc = None
    for ax, (tune, H, prof, c) in zip(axes, results):
        pc = draw_panel(ax, fig, H, prof, R_edges, P_edges, norm, add_cbar=False)
        ax.set_title(f"{tune}\n{gs[tune]},  corr = {c['corr']:+.3f}",
                     fontsize=FS_TITLE - 3)
    axes[0].set_ylabel(r"$r$  [fm]", fontsize=FS_LABEL)
    axes[0].legend(loc="upper right", fontsize=FS_TICK)
    cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.02)
    cb.set_label("fraction of events / bin", fontsize=FS_TITLE - 2)
    cb.ax.tick_params(labelsize=FS_TICK)
    fig.suptitle(f"{target} struck nucleon: momentum vs sampled position  "
                 f"(e$^-$ 2.445 GeV, genlist EM{sel_note}, t05 tunes, "
                 "shared color scale)",
                 fontsize=FS_SUPTITLE - 2)
    out = Path(out_dir) / f"struck_pr_{target.lower()}_all_t05.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22b_05_000", choices=TUNES)
    ap.add_argument("--dump-dir", required=True,
                    help="dir with <tune>.csv files from dump_hitnuc")
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--target", default="Fe56", choices=["Fe56", "C12"])
    ap.add_argument("--sel-qel-q2", action="store_true",
                    help="keep only QEL events in the Dutta Q2=1.28+-5%% window")
    ap.add_argument("--out-dir", default=str(OUT_DEFAULT),
                    help="figure output dir (v0.2: results/prd-analyzer-v0.2)")
    args = ap.parse_args()

    apply_style()
    sel_note = ", qel && $Q^2=1.28\\pm5\\%$" if args.sel_qel_q2 else ""
    R_edges, P_edges, gs = target_setup(args.target)
    tunes = TUNES if args.all_tunes else [args.tune]
    results = []
    for t in tunes:
        H, prof, c = load_hist(Path(args.dump_dir) / f"{t}.csv", R_edges, P_edges,
                               sel_qel_q2=args.sel_qel_q2)
        print(f"{t}: N={c['n_kept']:,}  in-grid={c['in_range']:,}  "
              f"corr(p,r)={c['corr']:+.3f}  <r>={c['mean_r']:.2f} fm")
        single_figure(args.target, t, H, prof, c, R_edges, P_edges, gs,
                      out_dir=args.out_dir, sel_note=sel_note and " qel-window")
        results.append((t, H, prof, c))
    if args.all_tunes:
        combined_figure(args.target, results, R_edges, P_edges, gs,
                        out_dir=args.out_dir, sel_note=sel_note)

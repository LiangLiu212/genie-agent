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
# non-campaign tunes, selectable via --tunes only (local samples dumped with
# dump_hitnuc the same way); GS_OVERRIDE labels chains whose ground state is
# not the ModelConfiguration NuclearModel line (the INCL thread samples r AND
# p in NucleusGenINCL and never reads that line, which 44b left as 22b's SF)
EXTRA_TUNES = ["GEM26_44b_05_000"]
GS_OVERRIDE = {"GEM26_44b_05_000": "INCL++ (NucleusGenINCL)"}
GENLIST = {"GEM26_44b_05_000": "EMQE"}       # default: EM (t05 campaigns)
R_ON_X = False       # --r-on-x: radius on x, momentum on y (default: p on x)
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
    for t in TUNES + EXTRA_TUNES:
        if t in GS_OVERRIDE:
            gs[t] = GS_OVERRIDE[t]
            continue
        model = resolve_ground_state(t, pdg)
        gs[t] = (f"SpectralFunc ({table.stem})"
                 if "genie::SpectralFunc/" in model else "LocalFGM")
    return r_edges, p_edges, gs


def load_hist(csv: Path, R_edges, P_edges, sel_qel_q2=False, sel_qel=False):
    """CSV from dump_hitnuc -> (H fraction/bin [r, p], profile, counts).

    sel_qel_q2: keep only scat==1 (QEL) events inside the Dutta Q^2 window
    (needs the q2 column of the extended dumper).
    sel_qel: keep only scat==1 (QEL), no Q^2 window (works on the older
    8-column dumps too) — the like-for-like selection against an EMQE-only
    sample."""
    d = np.genfromtxt(csv, delimiter=",", names=True)
    if sel_qel:
        d = d[d["scat"] == 1]
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
    # default orientation: x = missing momentum P_miss (plots 1-2), y = radius
    # r; --r-on-x transposes (x = r, y = P_miss). H is indexed [r, p].
    r_ctr, p_of_r = prof
    if R_ON_X:
        Xe, Ye = np.meshgrid(R_edges, P_edges, indexing="ij")
        Zm = np.ma.masked_less_equal(H, 0.0)
        pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
        ax.plot(r_ctr, p_of_r, "w--", lw=1.8, label=r"$\langle p\rangle(r)$")
        ax.set_xlabel(r"$r$  [fm]", fontsize=FS_LABEL)
        ax.set_xlim(R_edges[0], R_edges[-1])
    else:
        Xe, Ye = np.meshgrid(P_edges, R_edges, indexing="ij")
        Zm = np.ma.masked_less_equal(H.T, 0.0)
        pc = ax.pcolormesh(Xe, Ye, Zm, cmap="viridis", norm=norm)
        ax.plot(p_of_r, r_ctr, "w--", lw=1.8, label=r"$\langle p\rangle(r)$")
        ax.set_xlabel(r"$P_{\rm miss}$  [MeV/c]", fontsize=FS_LABEL)
        ax.set_xlim(P_edges[0], P_edges[-1])
    ax.tick_params(labelsize=FS_TICK)
    if add_cbar:
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.046)
        cb.ax.tick_params(labelsize=FS_TICK)
    return pc


YLABEL = {False: r"$r$  [fm]", True: r"$P_{\rm miss}$  [MeV/c]"}


def single_figure(target, tune, H, prof, c, R_edges, P_edges, gs,
                  out_dir=OUT_DEFAULT, sel_note="", tag=""):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    w, h = PANEL_SIZE
    fig, ax = plt.subplots(figsize=(w * 1.4, h), layout="constrained")
    norm = LogNorm(vmin=H.max() * 1e-6, vmax=H.max())
    draw_panel(ax, fig, H, prof, R_edges, P_edges, norm)
    ax.set_ylabel(YLABEL[R_ON_X], fontsize=FS_LABEL)
    ax.legend(loc="upper right", fontsize=FS_TICK)
    ax.set_title(f"N = {c['n_kept']:,}{sel_note or ' single-nucleon'} events,  "
                 f"corr(p, r) = {c['corr']:+.3f}", fontsize=FS_TITLE - 3)
    fig.suptitle(f"{target} struck nucleon: momentum vs sampled position\n"
                 f"{tune}  ({gs[tune]})\n"
                 f"e$^-$ 2.445 GeV, genlist {GENLIST.get(tune, 'EM')}",
                 fontsize=FS_SUPTITLE - 2)
    out = Path(out_dir) / f"struck_pr_{target.lower()}_{tune}{tag}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


def combined_figure(target, results, R_edges, P_edges, gs,
                    out_dir=OUT_DEFAULT, sel_note="", tag=""):
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
    axes[0].set_ylabel(YLABEL[R_ON_X], fontsize=FS_LABEL)
    axes[0].legend(loc="upper right", fontsize=FS_TICK)
    cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.02)
    cb.set_label("fraction of events / bin", fontsize=FS_TITLE - 2)
    cb.ax.tick_params(labelsize=FS_TICK)
    fig.suptitle(f"{target} struck nucleon: momentum vs sampled position  "
                 f"(e$^-$ 2.445 GeV, genlist EM{sel_note}, t05 tunes, "
                 "shared color scale)",
                 fontsize=FS_SUPTITLE - 2)
    out = Path(out_dir) / f"struck_pr_{target.lower()}_all_t05{tag}.png"
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
    ap.add_argument("--sel-qel", action="store_true",
                    help="keep only QEL events (scat==1), no Q2 window")
    ap.add_argument("--tunes", nargs="+", default=None,
                    choices=TUNES + EXTRA_TUNES,
                    help="explicit tune set (overrides --tune/--all-tunes; "
                         "the combined figure is drawn for >1 tune)")
    ap.add_argument("--tag", default="",
                    help="output-stem tag, e.g. _qel -> struck_pr_c12_all_t05_qel.png")
    ap.add_argument("--r-on-x", action="store_true",
                    help="radius on x, momentum on y (default: P_miss on x, "
                         "the orientation of plots 1-2)")
    args = ap.parse_args()
    R_ON_X = args.r_on_x

    apply_style()
    sel_note = (", qel && $Q^2=1.28\\pm5\\%$" if args.sel_qel_q2
                else ", qel" if args.sel_qel else "")
    R_edges, P_edges, gs = target_setup(args.target)
    tunes = args.tunes or (TUNES if args.all_tunes else [args.tune])
    results = []
    for t in tunes:
        H, prof, c = load_hist(Path(args.dump_dir) / f"{t}.csv", R_edges, P_edges,
                               sel_qel_q2=args.sel_qel_q2, sel_qel=args.sel_qel)
        print(f"{t}: N={c['n_kept']:,}  in-grid={c['in_range']:,}  "
              f"corr(p,r)={c['corr']:+.3f}  <r>={c['mean_r']:.2f} fm")
        single_figure(args.target, t, H, prof, c, R_edges, P_edges, gs,
                      out_dir=args.out_dir, tag=args.tag,
                      sel_note=(" qel-window" if args.sel_qel_q2
                                else " qel" if args.sel_qel else ""))
        results.append((t, H, prof, c))
    if args.all_tunes or (args.tunes and len(args.tunes) > 1):
        combined_figure(args.target, results, R_edges, P_edges, gs,
                        out_dir=args.out_dir, sel_note=sel_note, tag=args.tag)

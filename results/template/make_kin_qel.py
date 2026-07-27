"""(e,e'p) QEL kinematics, uncut, per campaign tune — El, theta_e', T_p, theta_p, Q^2.

v0.1 descendant of prd-analyzer-v0 README section 6 (plot_dists_q2.py), on the
full-EM t05 campaign samples (e- 2.445 GeV, genlist EM; Fe56 = grid jobs of
2026-07-16, C12 = grid jobs of 2026-07-26), with the selection reduced to

    qel                (EMQE-equivalent on the full-EM samples; RES/DIS/MEC
                        dropped, NO Q^2 window and no electron/proton cuts)

The Q^2 = 1.28 +- 5 % slice of the Dutta setting is drawn on the Q^2 panel as
grey-dashed REFERENCE lines only (nothing is applied); the t05 generation cut
EM-MinQ2Limit = 1.18 GeV^2 is the hard lower edge visible in the Q^2 panel.
Construction otherwise as v0: selection.load_events (leading proton =
highest-momentum final-state proton; T_p/theta_p panels implicitly drop
no-proton events). File lists are built over XRootD (dirlist), not the NFS
mount, so this runs with an expired Kerberos key; needs BEARER_TOKEN_FILE.

Panel ranges are computed from the pooled tunes (p0.2-p99.8, rounded to nice
steps) and printed, so the two targets stay directly readable without
hand-tuned windows.

Two figures per target:
    kin_qel_<target>.png         area-normalized (shape comparison)
    kin_qel_<target>_counts.png  raw events/bin (equal ntot = 2M/tune)

Cache: results/prd-analyzer-v0.1/cache/kin_qel_<target>/<tune>.npz
(El, theta_e, Tp, theta_p, Q2, has_p + ntot). Delete to re-stream.

Usage:
  pixi run python results/template/make_kin_qel.py --target Fe56
  pixi run python results/template/make_kin_qel.py --target C12 --plot-only
  MAX_FILES=2 WORKERS=4 pixi run python results/template/make_kin_qel.py --target C12
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import multiprocessing
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.1/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.1"
DOOR = "root://fndca1.fnal.gov:1094"

Q2_CENTER, Q2_FRAC = 1.28, 0.05          # Dutta slice, drawn as reference only
Q2_LO, Q2_HI = Q2_CENTER * (1 - Q2_FRAC), Q2_CENTER * (1 + Q2_FRAC)
# E_miss = omega - T_p [MeV] (leading proton, heavy-recoil convention of
# selection.py -- identical to the restored axis E_m + T_rec); p_miss [MeV/c]
KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss"]

# tune -> (color, linestyle, ground-state label): the v0.1 series convention
TUNES = {
    "GEM26_11a_05_000": ("C0", "-",  "LocalFGM"),
    "GEM26_22a_05_000": ("C2", "-",  "SF"),
    "GEM26_22b_05_000": ("C3", "-",  "SF"),
    "GEM21_11a_05_000": ("C4", "--", "LocalFGM"),
}
# target -> {tune: gevgen gridlog (run-dir, stem)} — the campaign samples
RUNS = {
    "Fe56": ("gevgen_grid-2026-07-16", {
        "GEM26_11a_05_000": "eminus_Fe56_20260716-113802",
        "GEM26_22a_05_000": "eminus_Fe56_20260716-141800",
        "GEM26_22b_05_000": "eminus_Fe56_20260716-141807",
        "GEM21_11a_05_000": "eminus_Fe56_20260716-113817",
    }),
    "C12": ("gevgen_grid-2026-07-26", {
        "GEM26_11a_05_000": "eminus_C12_20260726-105638",
        "GEM26_22a_05_000": "eminus_C12_20260726-105642",
        "GEM26_22b_05_000": "eminus_C12_20260726-105646",
        "GEM21_11a_05_000": "eminus_C12_20260726-105650",
    }),
}

# panel -> (cache key, axis label, nice range step, nbins)
PANELS = [
    ("El",      r"E$_{e'}$  [GeV]",       0.1,  60),
    ("theta_e", r"$\theta_{e'}$  [deg]",  2.0,  60),
    ("Tp",      r"T$_p$  [GeV]",          0.1,  60),
    ("theta_p", r"$\theta_p$  [deg]",     5.0,  56),
    ("Q2",      r"Q$^2$  [(GeV/c)$^2$]",  0.1,  60),
]


def gst_urls(target: str, tune: str, max_files: int):
    """XRootD URLs of the tune's first max_files gst files (dirlist, not NFS)."""
    from XRootD import client
    run_dir, stems = RUNS[target]
    gl = REPO / "jobsub-agent" / "jobsub-runs" / run_dir / f"{stems[tune]}.gridlog"
    pnfs = json.loads(gl.read_text())["pnfs_output_dir"]
    base = pnfs.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)
    fs = client.FileSystem(DOOR)
    st, top = fs.dirlist(base)
    assert st.ok, f"{tune}: dirlist failed: {st.message}"
    urls = []
    for sub in sorted(x.name for x in top if x.name.strip("/").isdigit()):
        st2, ls2 = fs.dirlist(f"{base}/{sub}")
        if not st2.ok:
            continue
        urls += [f"{DOOR}/{base}/{sub}/{f.name}"
                 for f in ls2 if f.name.endswith(".gst.root")]
    return sorted(urls)[:max_files]


def _build_one_file(url):
    from selection import load_events
    ev = load_events(url)
    m = ev["qel"]
    out = {k: ev[k][m] for k in KEYS}
    out["has_p"] = ev["has_p"][m]
    return out, len(ev["Q2"])


def build(target, tune, max_files, workers):
    urls = gst_urls(target, tune, max_files)
    print(f"[{tune}] streaming {len(urls)} gst file(s) over XRootD "
          f"(selection: qel only, {workers} workers)", flush=True)
    parts, ntot = [], 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        futs = {ex.submit(_build_one_file, u): u for u in urls}
        for fut in as_completed(futs):
            part, n = fut.result()
            parts.append(part)
            ntot += n
    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])
    cache_dir = CACHE_ROOT / f"kin_qel_{target.lower()}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{tune}.npz"
    np.savez_compressed(path, **out)
    print(f"[{tune}] ntot={ntot}  selected(qel)={len(out['Q2'])} "
          f"({100.0*len(out['Q2'])/max(ntot,1):.2f}%)  ->  {path}  "
          f"({time.time()-t0:.0f}s)", flush=True)


def load_cache(target, tune):
    return dict(np.load(CACHE_ROOT / f"kin_qel_{target.lower()}" / f"{tune}.npz"))


def panel_range(cache, key, step):
    """Pooled p0.2-p99.8 across tunes, rounded outward to `step`."""
    x = np.concatenate([cache[t][key] for t in TUNES])
    x = x[np.isfinite(x)]
    lo, hi = np.percentile(x, [0.2, 99.8])
    lo = np.floor(lo / step) * step
    hi = np.ceil(hi / step) * step
    return float(lo), float(hi)


def make_fig(target, cache, density):
    fig, axes = new_panels(ncols=3, nrows=2, sharey=False)
    for ax, (key, lab, step, nb) in zip(axes, PANELS):
        rng = panel_range(cache, key, step)
        if density:
            print(f"  panel {key}: range [{rng[0]:g}, {rng[1]:g}]")
        bins = np.linspace(rng[0], rng[1], nb)
        for tune, (color, ls, gs) in TUNES.items():
            x = cache[tune][key]
            m = np.isfinite(x)
            if key in ("Tp", "theta_p"):     # proton panels: real protons only
                m &= cache[tune]["has_p"].astype(bool)
            x = x[m]
            ax.hist(x, bins=bins, histtype="step", linewidth=1.8, color=color,
                    ls=ls, density=density,
                    label=f"{tune} ({gs}, N={len(cache[tune]['Q2']):,})")
        if key == "Q2":                       # reference only, nothing applied
            for v in (Q2_LO, Q2_HI):
                ax.axvline(v, color="0.5", ls="--", lw=1.0)
        style_axis(ax, title=None, xlabel=lab, logx=False, logy=False, ymin=None)
        ax.set_ylabel("normalized / bin" if density else "events / bin",
                      fontsize=FS_LABEL)
    axes[5].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[5].legend(handles, labels, title="campaign tune", loc="center",
                   fontsize=FS_LEGEND - 1, title_fontsize=FS_LEGEND_TITLE)
    norm_note = ("area-normalized" if density
                 else "raw events/bin (equal ntot = 2M/tune)")
    fig.suptitle(f"(e,e'p) QEL kinematics, uncut (qel only)  —  e⁻ on {target} "
                 f"(t05, genlist EM), {norm_note}\n"
                 "grey dashed on Q² = the Dutta Q² = 1.28 ± 5 % slice, "
                 "reference only (NOT applied)",
                 fontsize=FS_SUPTITLE - 1)
    fig.tight_layout()
    suffix = "" if density else "_counts"
    out = OUT_DIR / f"kin_qel_{target.lower()}{suffix}.png"
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(RUNS))
    ap.add_argument("--plot-only", action="store_true",
                    help="skip streaming, use existing caches")
    args = ap.parse_args()
    max_files = int(os.environ.get("MAX_FILES", "20"))
    workers = int(os.environ.get("WORKERS", "8"))

    if not args.plot_only:
        for tune in TUNES:
            if (CACHE_ROOT / f"kin_qel_{args.target.lower()}" / f"{tune}.npz").exists():
                print(f"[{tune}] cache exists, skipping stream")
                continue
            build(args.target, tune, max_files, workers)

    apply_style()
    cache = {t: load_cache(args.target, t) for t in TUNES}
    make_fig(args.target, cache, density=True)
    make_fig(args.target, cache, density=False)
    for t in TUNES:
        c = cache[t]
        print(f"  {t:18s} N={len(c['Q2']):7,d} of ntot={int(c['ntot'][0]):,}  "
              f"has_p={100*np.mean(c['has_p']):.1f}%")

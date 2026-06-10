"""Stream the (e,e'p) samples off dCache over XRootD, apply the stage-1
(electron-arm) selection, and cache the survivors locally so the plot scripts
never re-stream. Writes one results/prd-analyzer/cache/<model>.npz per model.

The stage-1 cut (El & theta_e, which fixes Q^2 ~ 1.28) is tight, so the cache holds
a small fraction of the streamed events — re-plotting is then instant. Re-run only
when the sample list or the selection changes (pass model keys to build just the
new/changed ones). Files are streamed in parallel worker processes (WORKERS env,
default 8) — at ~60 MB/s/stream this is what makes the 1B-event samples tractable.

Superset mode (--superset): build the stage-1 cache ONCE with the loosest electron
angular window of the analysis branches (theta_e +- SUPERSET_THETA_E_HW; the El
window is identical on all branches) into cache/superset/<model>.npz. Each branch
then derives its own cache/<model>.npz from the superset with recut_cache.py —
no re-streaming per branch. If a future branch uses a window wider than
SUPERSET_THETA_E_HW, widen the constant and rebuild the superset.

    export BEARER_TOKEN_FILE=<token>        # dCache/XRootD auth (htgettoken -i dune)
    pixi run python results/prd-analyzer/build_cache.py            # all models, branch CUTS
    pixi run python results/prd-analyzer/build_cache.py --superset # all models, loosest theta_e
    MAX_FILES=2 WORKERS=2 pixi run python results/prd-analyzer/build_cache.py SF   # quick test

Cached per model: stage-1 events' {El,theta_e,Tp,theta_p,Q2,E_miss,p_miss,has_p,qel}
+ the stage-2 coincidence mask + the total streamed event count `ntot`.
(In superset npz files the stage2 column reflects the *building* branch's proton
cuts and is recomputed by recut_cache.py — do not read it directly.)
"""
import sys
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "results/prd-analyzer")
import numpy as np
import samples as S
import selection as sel

KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss"]
SUPERSET_THETA_E_HW = 6.0     # loosest theta_e half-width across analysis branches [deg]


def _build_one_file(args):
    """Worker: stream one gst, return its stage-1 arrays (+ event count)."""
    url, theta_e_hw = args
    ev = sel.load_events(url)            # uproot.open(root://...) streams the file
    if theta_e_hw is None:
        m1 = sel.select_electron(ev)     # this branch's stage 1
    else:                                # superset: same El window, overridden theta_e
        cen = sel.CUTS["theta_e"][0]
        m1 = sel._win(ev["El"], *sel.CUTS["El"]) & sel._win(ev["theta_e"], cen, theta_e_hw)
    out = {k: ev[k][m1] for k in KEYS}
    out["has_p"] = ev["has_p"][m1]
    out["qel"] = ev["qel"][m1]
    out["stage2"] = sel.select(ev)[m1]   # recomputed by recut_cache.py in superset mode
    return out, len(m1)


def build(model, max_files=None, superset=False, workers=8):
    urls = S.gst_urls(model, max_files=max_files)
    hw = SUPERSET_THETA_E_HW if superset else None
    mode = f"superset theta_e +-{hw}" if superset else "branch CUTS"
    print(f"[{model}] streaming {len(urls)} gst file(s) over XRootD "
          f"({mode}, {workers} workers)", flush=True)
    parts, ntot = [], 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")   # no fork: clean XRootD state per worker
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        futs = {ex.submit(_build_one_file, (u, hw)): u for u in urls}
        for i, fut in enumerate(as_completed(futs), 1):
            part, n = fut.result()
            parts.append(part)
            ntot += n
            if i % 50 == 0 or i == len(urls):
                n1 = sum(len(p["El"]) for p in parts)
                print(f"  [{model}] {i}/{len(urls)} files  stage1={n1}  "
                      f"({time.time()-t0:.0f}s)", flush=True)

    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])

    cache_dir = f"{S.CACHE_DIR}/superset" if superset else S.CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{model}.npz"
    np.savez_compressed(path, **out)
    eff = 100.0 * len(out["El"]) / max(ntot, 1)
    print(f"[{model}] ntot={ntot}  stage1={len(out['El'])} ({eff:.3f}%)  "
          f"stage2={int(out['stage2'].sum())}  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    superset = "--superset" in sys.argv[1:]
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "0")) or None
    workers = int(os.environ.get("WORKERS", "8"))
    t0 = time.time()
    for m in models:
        build(m, max_files=max_files, superset=superset, workers=workers)
    print(f"all done in {time.time()-t0:.0f}s", flush=True)

"""Stream the (e,e'p) samples off dCache over XRootD, apply the stage-1
(electron-arm) selection, and cache the survivors locally so the plot scripts
never re-stream. Writes one small results/prd-analyzer/cache/<model>.npz per model.

The stage-1 cut (El & theta_e, which fixes Q^2 ~ 1.28) is already very tight, so
the cache holds only ~1e4-1e5 events/model — re-plotting is then instant. Re-run
this only when the sample list or the selection changes (pass model keys to build
just the new/changed ones).

    export BEARER_TOKEN_FILE=<token>        # dCache/XRootD auth (htgettoken -i dune)
    pixi run python results/prd-analyzer/build_cache.py            # all models in samples.MODELS
    MAX_FILES=2 pixi run python results/prd-analyzer/build_cache.py SF   # quick test

Cached per model: stage-1 events' {El,theta_e,Tp,theta_p,Q2,E_miss,p_miss,has_p,qel}
+ the stage-2 coincidence mask + the total streamed event count `ntot`.
"""
import sys
import os
import time

sys.path.insert(0, "results/prd-analyzer")
import numpy as np
import samples as S
import selection as sel

KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss"]


def build(model, max_files=None):
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] streaming {len(urls)} gst file(s) over XRootD", flush=True)
    store = {k: [] for k in KEYS}
    has_p, qel, stage2 = [], [], []
    ntot = 0
    t0 = time.time()
    for i, url in enumerate(urls, 1):
        ev = sel.load_events(url)            # uproot.open(root://...) streams the file
        m1 = sel.select_electron(ev)         # stage 1: scattered-electron arm (fixes Q^2)
        ntot += len(m1)
        for k in KEYS:
            store[k].append(ev[k][m1])
        has_p.append(ev["has_p"][m1])
        qel.append(ev["qel"][m1])
        stage2.append(sel.select(ev)[m1])    # stage-2 coincidence mask, indexed within stage 1
        if i % 10 == 0 or i == len(urls):
            n1 = sum(len(x) for x in store["El"])
            print(f"  [{model}] {i}/{len(urls)} files  stage1={n1}  ({time.time()-t0:.0f}s)",
                  flush=True)

    out = {k: np.concatenate(v) for k, v in store.items()}
    out["has_p"] = np.concatenate(has_p)
    out["qel"] = np.concatenate(qel)
    out["stage2"] = np.concatenate(stage2)
    out["ntot"] = np.array([ntot])

    os.makedirs(S.CACHE_DIR, exist_ok=True)
    path = f"{S.CACHE_DIR}/{model}.npz"
    np.savez_compressed(path, **out)
    eff = 100.0 * len(out["El"]) / max(ntot, 1)
    print(f"[{model}] ntot={ntot}  stage1={len(out['El'])} ({eff:.3f}%)  "
          f"stage2={int(out['stage2'].sum())}  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "0")) or None
    t0 = time.time()
    for m in models:
        build(m, max_files=max_files)
    print(f"all done in {time.time()-t0:.0f}s", flush=True)

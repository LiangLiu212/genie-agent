"""Stream the (e,e'p) samples off dCache over XRootD and cache events with
ONLY a Q^2 window — no electron or proton cuts at all.

Selection: |Q^2 / 1.28 - 1| <= 5 %  (Q^2 in [1.216, 1.344] GeV^2), fully inside
the t05 generation cut (Q^2 >= 1.18), so unlike the spectrometer-acceptance
selection this window is NOT clipped by the generation boundary. Efficiency is
~27 %, so a few files per model give ample statistics (MAX_FILES default 4 =
2M events -> ~550k selected/model). Writes cache/q2window/<model>.npz with the
same columns as build_cache.py (El, theta_e, Tp, theta_p, Q2, E_miss, p_miss,
has_p, qel) + ntot.

    export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)   # htgettoken -a htvaultprod.fnal.gov -i dune
    pixi run python results/prd-analyzer-v0/build_cache_q2.py            # all models
    MAX_FILES=1 WORKERS=1 pixi run python results/prd-analyzer-v0/build_cache_q2.py SF
"""
import sys
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
import samples as S
import selection as sel

Q2_CENTER, Q2_FRAC = 1.28, 0.05
KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss"]


def _build_one_file(url):
    ev = sel.load_events(url)
    m = np.abs(ev["Q2"] / Q2_CENTER - 1.0) <= Q2_FRAC
    out = {k: ev[k][m] for k in KEYS}
    out["has_p"] = ev["has_p"][m]
    out["qel"] = ev["qel"][m]
    return out, len(m)


def build(model, max_files, workers):
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] streaming {len(urls)} gst file(s) over XRootD "
          f"(Q2 = {Q2_CENTER} +- {100*Q2_FRAC:.0f} % only, {workers} workers)", flush=True)
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
    cache_dir = f"{S.CACHE_DIR}/q2window"
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{model}.npz"
    np.savez_compressed(path, **out)
    eff = 100.0 * len(out["Q2"]) / max(ntot, 1)
    print(f"[{model}] ntot={ntot}  selected={len(out['Q2'])} ({eff:.2f}%)"
          f"  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "4"))
    workers = int(os.environ.get("WORKERS", "8"))
    t0 = time.time()
    for m in models:
        build(m, max_files=max_files, workers=workers)
    print(f"all done in {time.time()-t0:.0f}s", flush=True)

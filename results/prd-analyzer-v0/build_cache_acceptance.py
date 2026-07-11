"""Stream the (e,e'p) samples off dCache over XRootD, apply the HMS/SOS
spectrometer-ACCEPTANCE selection (acceptance.py), and cache the accepted
events into results/prd-analyzer-v0/cache/acceptance/<model>.npz.

Unlike build_cache.py's stage-1 windows (El +-5 MeV, theta_e +-0.5..6 deg),
the acceptance boxes span the full HMS momentum bite (+-8 % = +-138 MeV), so
no existing cache can be recut for this -- the gst must be re-streamed. The
samples are 2000 x 500k events per model; MAX_FILES (default 20 = 10M events)
bounds the streamed subset, and ntot records how many events were streamed.

    export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)   # htgettoken -a htvaultprod.fnal.gov -i dune
    pixi run python results/prd-analyzer-v0/build_cache_acceptance.py            # all models
    MAX_FILES=1 WORKERS=1 pixi run python results/prd-analyzer-v0/build_cache_acceptance.py UnifiedQEL
"""
import sys
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
import samples as S
import acceptance as acc


def _build_one_file(url):
    ev = acc.load_events(url)
    m = acc.select_acceptance(ev)
    out = {k: ev[k][m] for k in acc.KEYS}
    return out, len(m)


def build(model, max_files, workers):
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] streaming {len(urls)} gst file(s) over XRootD "
          f"(acceptance cuts, {workers} workers)", flush=True)
    parts, ntot = [], 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        futs = {ex.submit(_build_one_file, u): u for u in urls}
        for i, fut in enumerate(as_completed(futs), 1):
            part, n = fut.result()
            parts.append(part)
            ntot += n
            if i % 10 == 0 or i == len(urls):
                nacc = sum(len(p["E_miss"]) for p in parts)
                print(f"  [{model}] {i}/{len(urls)} files  accepted={nacc}  "
                      f"({time.time()-t0:.0f}s)", flush=True)

    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])
    cache_dir = f"{S.CACHE_DIR}/acceptance"
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{model}.npz"
    np.savez_compressed(path, **out)
    eff = 100.0 * len(out["E_miss"]) / max(ntot, 1)
    print(f"[{model}] ntot={ntot}  accepted={len(out['E_miss'])} ({eff:.3f}%)"
          f"  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "20"))
    workers = int(os.environ.get("WORKERS", "8"))
    t0 = time.time()
    for m in models:
        build(m, max_files=max_files, workers=workers)
    print(f"all done in {time.time()-t0:.0f}s", flush=True)

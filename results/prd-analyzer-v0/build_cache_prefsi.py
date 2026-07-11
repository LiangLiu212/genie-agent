"""Stream the (e,e'p) samples and cache the PRE-FSI missing kinematics of the
proton-channel events -- no cuts at all (beyond the sample's own t05
generation cut Q^2 >= 1.18).

Selection: hitnuc == 2212 (QEL on a bound proton; neutron-channel events have
no primary proton). Kinematics from the PRIMARY (pre-INTRANUKE) proton --
gst branches pdgi/Ei/pxi/pyi/pzi -- with the same reconstruction as everywhere
else in the analyzer:
    E_miss = omega - T_p - T_rec,   p_miss = |q - p_p|,  T_rec = pm^2/(2 M_11B)
For 1-body QEL the primary proton is p = q + p_init, so p_miss is exactly the
sampled initial-nucleon momentum and E_miss the sampled removal energy (up to
the binding prescription) -- the event-level image of the ground-state input.

Writes cache/prefsi/<model>.npz: E_miss, p_miss [MeV], Q2 [GeV^2] per
proton-channel event, + ntot (all streamed) and n_hitp (proton-channel count).

    export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)
    pixi run python results/prd-analyzer-v0/build_cache_prefsi.py           # all models
"""
import sys
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
import uproot
import awkward as ak

import samples as S
from selection import M_P
from acceptance import M_REC

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "Q2", "pdgi", "Ei", "pxi", "pyi", "pzi"]


def load_prefsi(path):
    a = uproot.open(path)["gst"].arrays(BRANCHES, library="ak")
    hitp = ak.to_numpy(a.hitnuc) == 2212

    isp = (a.pdgi == 2212)
    lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
    g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
    Ep, pxp, pyp, pzp = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)

    nz = lambda b: ak.to_numpy(a[b])
    omega = nz("Ev") - nz("El")
    qx, qy, qz = nz("pxv") - nz("pxl"), nz("pyv") - nz("pyl"), nz("pzv") - nz("pzl")
    p_miss = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)
    E_miss = (omega - (Ep - M_P) - p_miss ** 2 / (2.0 * M_REC)) * 1000.0

    return dict(E_miss=E_miss[hitp], p_miss=p_miss[hitp] * 1000.0,
                Q2=nz("Q2")[hitp]), len(hitp), int(hitp.sum())


def _one(url):
    return load_prefsi(url)


def build(model, max_files, workers):
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] streaming {len(urls)} file(s) (pre-FSI, hitnuc==p, no cuts)",
          flush=True)
    parts, ntot, nhitp = [], 0, 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        for fut in as_completed({ex.submit(_one, u): u for u in urls}):
            part, n, nh = fut.result()
            parts.append(part)
            ntot += n
            nhitp += nh
    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])
    out["n_hitp"] = np.array([nhitp])
    cache_dir = f"{S.CACHE_DIR}/prefsi"
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{model}.npz"
    np.savez_compressed(path, **out)
    print(f"[{model}] ntot={ntot}  hitnuc==p: {nhitp} ({100.0*nhitp/ntot:.1f}%)"
          f"  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "4"))
    workers = int(os.environ.get("WORKERS", "8"))
    for m in models:
        build(m, max_files=max_files, workers=workers)
    print("all done", flush=True)

"""Stream the (e,e'p) samples and cache the FOUR-STAGE ladder kinematics of the
proton-channel events -- no cuts at all (beyond the sample's own t05
generation cut Q^2 >= 1.18).

Selection: hitnuc == 2212 (QEL on a bound proton). Per event, the same missing
kinematics at the three event-record stages of the generator workflow (the
input SF table is stage 1, drawn straight from the tables by the plots):

  stage 2  struck nucleon (record):  E2 = M_p - En - pn^2/(2 M_11B),  p2 = pn
           NB deliberately differs from results/template/make_groundstate_*
           (M_N - En, no T_rec): subtracting T_rec = pn^2/(2 M_11B) puts E2 on
           the SF-table E axis and makes E2 == E3 exact for an
           energy-conserving chain (1-body QEL: Ep = omega + En, p_miss = pn).
  stage 3  pre-FSI primary proton:   bit-identical to build_cache_prefsi.py --
           leading pdgi==2212 by max Ei, p3 = |q - p_i|,
           E3 = omega - (Ei - M_p) - p3^2/(2 M_11B)
  stage 4  post-FSI leading proton:  acceptance.py idiom -- leading pdgf==2212
           by max pf, same reconstruction from Ef/pxf/pyf/pzf; NaN when FSI
           left no proton (absorption/CEX) -- those events stay in the n_hitp
           denominator only, so occupancy integrals show the loss directly.

Writes cache/ladder/<model>.npz per proton-channel event (float64):
  E2,p2,E3,p3,E4,p4 [MeV], Q2 [GeV^2]           the ladder kinematics
  El [GeV], cthl                                 scattered e' (FSI-blind)
  T3,cth3 / T4,cth4 [GeV]                        kinetic energy + cos(theta)
                                                 of the pre-FSI / leading
                                                 post-FSI proton
+ scalars ntot (all streamed) and n_hitp.

    export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)
    MAX_FILES=20 pixi run python results/prd-analyzer-v0/build_cache_ladder.py \
        LFG SF UnifiedQEL2024 UnifiedQEL
    MAX_FILES=4  pixi run python results/prd-analyzer-v0/build_cache_ladder.py SuSAv2
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

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl", "cthl",
            "hitnuc", "Q2",
            "En", "pxn", "pyn", "pzn",                    # stage 2 (no `pn` scalar
            # in the genie_dev-install gst -- SuSAv2 sample -- so build |p_n|
            # from the components everywhere)
            "pdgi", "Ei", "pxi", "pyi", "pzi",            # stage 3
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]      # stage 4


def load_ladder(path):
    a = uproot.open(path)["gst"].arrays(BRANCHES, library="ak")
    hitp = ak.to_numpy(a.hitnuc) == 2212

    nz = lambda b: ak.to_numpy(a[b])
    omega = nz("Ev") - nz("El")
    qx, qy, qz = nz("pxv") - nz("pxl"), nz("pyv") - nz("pyl"), nz("pzv") - nz("pzl")

    # stage 2 -- struck nucleon as written into the record
    En = nz("En")
    pn = np.sqrt(nz("pxn") ** 2 + nz("pyn") ** 2 + nz("pzn") ** 2)
    E2 = (M_P - En - pn ** 2 / (2.0 * M_REC)) * 1000.0
    p2 = pn * 1000.0

    # stage 3 -- pre-FSI primary proton (bit-identical to build_cache_prefsi)
    isp = (a.pdgi == 2212)
    lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
    g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
    Ep, pxp, pyp, pzp = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
    p3 = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)
    E3 = (omega - (Ep - M_P) - p3 ** 2 / (2.0 * M_REC)) * 1000.0

    # stage 4 -- post-FSI leading proton (acceptance.py idiom); NaN if absorbed
    isf = (a.pdgf == 2212)
    leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
    gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
    Efp, pxf, pyf, pzf = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
    p4 = np.sqrt((pxf - qx) ** 2 + (pyf - qy) ** 2 + (pzf - qz) ** 2)
    E4 = (omega - (Efp - M_P) - p4 ** 2 / (2.0 * M_REC)) * 1000.0

    with np.errstate(invalid="ignore", divide="ignore"):
        cth3 = pzp / np.sqrt(pxp ** 2 + pyp ** 2 + pzp ** 2)
        cth4 = pzf / np.sqrt(pxf ** 2 + pyf ** 2 + pzf ** 2)

    out = dict(E2=E2[hitp], p2=p2[hitp],
               E3=E3[hitp], p3=p3[hitp] * 1000.0,
               E4=E4[hitp], p4=p4[hitp] * 1000.0,
               Q2=nz("Q2")[hitp],
               El=nz("El")[hitp], cthl=nz("cthl")[hitp],
               T3=(Ep - M_P)[hitp], cth3=cth3[hitp],
               T4=(Efp - M_P)[hitp], cth4=cth4[hitp])
    n_nop3 = int(np.sum(~np.isfinite(out["E3"])))    # expect 0: EMQE is pure QEL
    return out, len(hitp), int(hitp.sum()), n_nop3


def _one(url):
    return load_ladder(url)


def build(model, max_files, workers):
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] streaming {len(urls)} file(s) (4-stage ladder, hitnuc==p, no cuts)",
          flush=True)
    parts, ntot, nhitp, nop3 = [], 0, 0, 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        for fut in as_completed({ex.submit(_one, u): u for u in urls}):
            part, n, nh, n3 = fut.result()
            parts.append(part)
            ntot += n
            nhitp += nh
            nop3 += n3
    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])
    out["n_hitp"] = np.array([nhitp])
    cache_dir = f"{S.CACHE_DIR}/ladder"
    os.makedirs(cache_dir, exist_ok=True)
    path = f"{cache_dir}/{model}.npz"
    np.savez_compressed(path, **out)
    surv = float(np.isfinite(out["E4"]).mean())
    print(f"[{model}] ntot={ntot}  hitnuc==p: {nhitp} ({100.0*nhitp/ntot:.1f}%)"
          f"  no-primary-p: {nop3}  post-FSI-p survival: {100.0*surv:.1f}%"
          f"  ->  {path}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "4"))
    workers = int(os.environ.get("WORKERS", "8"))
    for m in models:
        build(m, max_files=max_files, workers=workers)
    print("all done", flush=True)

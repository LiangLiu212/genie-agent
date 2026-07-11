"""Stream the (e,e'p) samples and cache everything the S^D extraction needs
(plan: .claude/plans/genie-experimental-spectral-function.md, step 2).

One XRootD pass per model -> TWO caches (the plan's fiducial variants):
    cache/sd/<model>_q2win.npz   (a) has_p and |Q2/1.28 - 1| <= 5 %  (full 4pi arms)
    cache/sd/<model>_accept.npz  (b) the HMS x SOS acceptance boxes (acceptance.py)

Cached per event (units in [.]): El [GeV], theta_e [deg], Q2 [GeV^2] -- plus the
sigma_cc1 inputs nu, qmag, Ep, pp [MeV], sin_gamma, cos_phi (deforest.angles_pq,
beam along z), and the binning variables E_miss [MeV] (= nu - Tp - Trec, recoil
included) and p_miss [MeV/c]. The per-event estimator weight 1/(Ep*pp*sigma_cc1)
is computed at plot time from these scalars (kept raw for flexibility).

Normalization scalars per cache: `ntot` (events streamed -- the N_gen of
sigma*n/N) and the sample cross section from the SAME spline XML the gevgen
production used (extracted from the campaign gridlog, fetched over XRootD once
and parsed here): `sigma_p_ub`, `sigma_n_ub` (bound-p / bound-n QES channels)
and their sum `sigma_ub` [microbarn/nucleus] at E = 2.445 GeV. The gst files
carry no xsec branch, so the spline is the source of truth; knots are linearly
interpolated (adjacent knots differ by ~4 %, so the interpolation error is
negligible). GENIE spline XML stores xsec in natural units 1/GeV^2; converted
with hbar^2 c^2 = 0.3893793721 mb GeV^2 (CODATA).

    export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)   # htgettoken -a htvaultprod.fnal.gov -i dune
    pixi run python results/prd-analyzer-v0/build_cache_sd.py             # all models
    MAX_FILES=1 WORKERS=1 pixi run python results/prd-analyzer-v0/build_cache_sd.py UnifiedQEL
"""
import sys
import os
import re
import time
import subprocess
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
import uproot
import awkward as ak

import samples as S
import acceptance as acc
from selection import M_P, BRANCHES
from deforest import angles_pq

GRIDLOG_DIR = "jobsub-agent/jobsub-runs/gevgen_grid-2026-06-11"
HBARC2_UB_GEV2 = 389.3793721        # hbar^2 c^2 [microbarn GeV^2] (CODATA)
EV_GEV = 2.445                      # beam energy of the campaign [GeV]

KEYS = ["El", "theta_e", "Q2", "nu", "qmag", "Ep", "pp",
        "sin_gamma", "cos_phi", "E_miss", "p_miss"]


# ---------------------------------------------------------------- sigma from the spline
def spline_sigma(model, cache_dir):
    """Cross section [microbarn/nucleus] at EV_GEV from the tune's own gmkspl
    spline -- the exact XML the gevgen production loaded (path recorded in the
    campaign gridlog). Returns dict(sigma_p_ub, sigma_n_ub, sigma_ub)."""
    jobid = re.search(r"/(eminus_[^/]+?)_gev/", S.SAMPLES[model][2]).group(1)
    text = open(f"{GRIDLOG_DIR}/{jobid}.gridlog").read()
    pnfs = re.search(r"-f (/pnfs/\S+?\.xml)", text).group(1)

    os.makedirs(f"{cache_dir}/splines", exist_ok=True)
    local = f"{cache_dir}/splines/{model}.xml"
    if not os.path.exists(local):
        url = S.xrootd_url(pnfs)
        subprocess.run(["xrdcp", "-f", url, local], check=True, capture_output=True)

    xml = open(local).read()
    out = {}
    for name, body in re.findall(r'<spline name="([^"]*)" nknots="\d+">(.*?)</spline>',
                                 xml, re.S):
        if "tgt:1000060120" not in name:      # multi-target spline files (e.g. the
            continue                          # GEM21 C12+Fe56+Au197 job): C12 only
        knots = np.array(re.findall(
            r"<E>\s*([\d.eE+-]+)\s*</E>\s*<xsec>\s*([\d.eE+-]+)\s*</xsec>", body),
            dtype=float)
        sig_ub = np.interp(EV_GEV, knots[:, 0], knots[:, 1]) * HBARC2_UB_GEV2
        if "N:2212" in name:
            out["sigma_p_ub"] = sig_ub
        elif "N:2112" in name:
            out["sigma_n_ub"] = sig_ub
    out["sigma_ub"] = out["sigma_p_ub"] + out["sigma_n_ub"]
    return out


# ---------------------------------------------------------------- event loader
def load_events_sd(path):
    """One gst -> per-event dict: superset of acceptance.load_events plus the
    sigma_cc1 inputs (nu, qmag, Ep, pp, sin_gamma, cos_phi)."""
    a = uproot.open(path)["gst"].arrays(BRANCHES, library="ak")

    isp = (a.pdgf == 2212)
    has_p = ak.to_numpy(ak.any(isp, axis=1))
    lead = ak.argmax(ak.where(isp, a.pf, -1.0), axis=1, keepdims=True)
    g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
    Ep, pxp, pyp, pzp, pp = g(a.Ef), g(a.pxf), g(a.pyf), g(a.pzf), g(a.pf)

    nz = lambda b: ak.to_numpy(a[b])
    Ev, El = nz("Ev"), nz("El")
    pxv, pyv, pzv = nz("pxv"), nz("pyv"), nz("pzv")
    pxl, pyl, pzl = nz("pxl"), nz("pyl"), nz("pzl")
    cthl = nz("cthl")

    # electron arm (HMS frame) -- as acceptance.load_events
    pTl = np.hypot(pxl, pyl)
    pl = np.hypot(pTl, pzl)
    delta_e = (pl / acc.P0_E - 1.0) * 100.0
    se, ce = np.sin(acc.TH0_E), np.cos(acc.TH0_E)
    yptar_e = (pTl * ce - pzl * se) / (pTl * se + pzl * ce)

    # proton arm (SOS frame), e'-plane rotation -- as acceptance.load_events
    phi_e = np.arctan2(pyl, pxl)
    cph, sph = np.cos(phi_e), np.sin(phi_e)
    pxp_r = pxp * cph + pyp * sph
    pyp_r = -pxp * sph + pyp * cph
    sp, cp = np.sin(acc.TH0_P), np.cos(acc.TH0_P)
    pz_arm = -pxp_r * sp + pzp * cp
    py_arm = -pxp_r * cp - pzp * sp
    with np.errstate(divide="ignore", invalid="ignore"):
        yptar_p = np.where(pz_arm > 0, py_arm / pz_arm, np.nan)
        xptar_p = np.where(pz_arm > 0, pyp_r / pz_arm, np.nan)
    delta_p = (pp / acc.P0_P - 1.0) * 100.0

    # missing kinematics + sigma_cc1 angle inputs (all GeV until the end)
    omega = Ev - El
    Tp = Ep - M_P
    qx, qy, qz = pxv - pxl, pyv - pyl, pzv - pzl
    qmag = np.sqrt(qx ** 2 + qy ** 2 + qz ** 2)
    p_miss = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)
    T_rec = p_miss ** 2 / (2.0 * acc.M_REC)
    E_miss = (omega - Tp - T_rec) * 1000.0

    with np.errstate(divide="ignore", invalid="ignore"):
        uq = np.stack([qx / qmag, qy / qmag, qz / qmag], axis=1)
        up = np.stack([np.where(pp > 0, pxp / pp, 0.0),
                       np.where(pp > 0, pyp / pp, 0.0),
                       np.where(pp > 0, pzp / pp, 1.0)], axis=1)
    sin_gamma, cos_phi = angles_pq(uq, up)

    theta_e = np.degrees(np.arccos(np.clip(cthl, -1.0, 1.0)))

    return dict(El=El, theta_e=theta_e, Q2=nz("Q2"),
                nu=omega * 1000.0, qmag=qmag * 1000.0,
                Ep=Ep * 1000.0, pp=pp * 1000.0,
                sin_gamma=sin_gamma, cos_phi=cos_phi,
                E_miss=E_miss, p_miss=p_miss * 1000.0,
                delta_e=delta_e, yptar_e=yptar_e,
                delta_p=delta_p, yptar_p=yptar_p, xptar_p=xptar_p,
                has_p=has_p)


def _build_one_file(url):
    ev = load_events_sd(url)
    m_a = ev["has_p"] & (np.abs(np.nan_to_num(ev["Q2"], nan=1e9) / 1.28 - 1.0) <= 0.05)
    m_b = acc.select_acceptance(ev)
    out_a = {k: ev[k][m_a] for k in KEYS}
    out_b = {k: ev[k][m_b] for k in KEYS}
    return out_a, out_b, len(m_a)


def build(model, max_files, workers, cache_dir):
    sig = spline_sigma(model, cache_dir)
    urls = S.gst_urls(model, max_files=max_files)
    print(f"[{model}] sigma(2.445) = {sig['sigma_ub']*1e3:.4f} nb "
          f"(p {sig['sigma_p_ub']*1e3:.4f} + n {sig['sigma_n_ub']*1e3:.4f}); "
          f"streaming {len(urls)} file(s), {workers} workers", flush=True)
    parts_a, parts_b, ntot = [], [], 0
    t0 = time.time()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
        futs = {ex.submit(_build_one_file, u): u for u in urls}
        for fut in as_completed(futs):
            pa, pb, n = fut.result()
            parts_a.append(pa)
            parts_b.append(pb)
            ntot += n

    for tag, parts in (("q2win", parts_a), ("accept", parts_b)):
        out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        out["ntot"] = np.array([ntot])
        for k, v in sig.items():
            out[k] = np.array([v])
        path = f"{cache_dir}/{model}_{tag}.npz"
        np.savez_compressed(path, **out)
        print(f"  [{model}] {tag}: {len(out['El'])} events "
              f"({100.0*len(out['El'])/ntot:.3f}%) -> {path}", flush=True)
    print(f"[{model}] done in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    max_files = int(os.environ.get("MAX_FILES", "8"))
    workers = int(os.environ.get("WORKERS", "8"))
    cache_dir = f"{S.CACHE_DIR}/sd"
    os.makedirs(cache_dir, exist_ok=True)
    t0 = time.time()
    for m in models:
        build(m, max_files=max_files, workers=workers, cache_dir=cache_dir)
    print(f"all done in {time.time()-t0:.0f}s", flush=True)

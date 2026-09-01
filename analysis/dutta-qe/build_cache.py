"""Stage 0: build cache/<target>/<tune>.npz from events.

Three interchangeable sources (identical schema, see select.py):

  --seed-from-v03   copy the study's committed-analysis caches
                    (results/prd-analyzer-v0.3/cache/ladder_*) — instant,
                    no grid access needed
  --stream          rebuild from the grid gst files over XRootD
                    (needs a valid bearer token: BEARER_TOKEN_FILE,
                    refresh with `htgettoken -a htvaultprod.fnal.gov -i dune`)
  --local           read local gst chunk files declared per target/tune in
                    config TARGETS[target]["local_gst"] (tunes with no grid
                    campaign, e.g. the GEM26_44b INCL sample)

The stream/local paths apply the selection qel && hitnuc==p &&
|Q^2/1.28-1|<=5% and record the three event stages; stage 4 uses the
study's final N_p = 1 post-FSI selection (the unique final-state proton).

Usage:
  pixi run python analysis/dutta-qe/build_cache.py --seed-from-v03
  pixi run python analysis/dutta-qe/build_cache.py --stream --target C12 [--tune ...] [--max-files 20]
  pixi run python analysis/dutta-qe/build_cache.py --local --target C12 [--tune ...]
"""
import argparse
import glob as globmod
import json
import shutil

import numpy as np

from config import (CACHE_DIR, GRIDLOG_ROOT, M_P, M_REC, Q2_CENTER, Q2_FRAC,
                    REPO, TARGETS, TUNES, V03_CACHE)

DOOR = "root://fndca1.fnal.gov:1094"

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel", "Q2",
            "En", "pxn", "pyn", "pzn",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def seed_from_v03():
    n = 0
    for target in TARGETS:
        src_dir = V03_CACHE / f"ladder_{target.lower()}"
        dst_dir = CACHE_DIR / target.lower()
        dst_dir.mkdir(parents=True, exist_ok=True)
        for tune in TUNES:
            src = src_dir / f"{tune}.npz"
            if not src.exists():
                print(f"  MISSING {src}")
                continue
            shutil.copy2(src, dst_dir / f"{tune}.npz")
            n += 1
            print(f"  seeded {target}/{tune}.npz")
    print(f"{n} cache file(s) seeded from {V03_CACHE}")


def gst_urls(gridlog_path, max_files):
    """The gridlog's gst outputs as XRootD URLs (from results/template/pnfs_ls.py)."""
    from XRootD import client
    pnfs = json.loads(gridlog_path.read_text())["pnfs_output_dir"]
    base = str(pnfs).replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)
    fs = client.FileSystem(DOOR)

    def dirlist(path):
        st, ls = fs.dirlist(path)
        if not st.ok:
            raise RuntimeError(f"dirlist {path}: {st.message}")
        return ls

    urls = []
    for sub in sorted(x.name for x in dirlist(base)
                      if x.name.strip("/").isdigit()):
        try:
            ls = dirlist(f"{base}/{sub}")
        except RuntimeError:
            continue
        urls += [f"{DOOR}/{base}/{sub}/{f.name}"
                 for f in ls if f.name.endswith(".gst.root")]
    return sorted(urls)[:max_files] if max_files else sorted(urls)


def build(target, tune, paths, verb):
    """Selection + three-stage projection over gst files (URLs or local)."""
    import uproot
    import awkward as ak
    m_rec = M_REC[target]
    out_dir = CACHE_DIR / target.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[{tune}] {verb} {len(paths)} gst file(s) "
          f"(qel && hitnuc==p && |Q2/{Q2_CENTER}-1|<={Q2_FRAC:.0%})")
    parts, ntot, nsel = [], 0, 0
    for ipath, url in enumerate(paths):
        a = uproot.open(url)["gst"].arrays(BRANCHES, library="ak")
        keep = (ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
                & (np.abs(ak.to_numpy(a.Q2) / Q2_CENTER - 1.0) <= Q2_FRAC))
        nz = lambda b: ak.to_numpy(a[b])
        omega = nz("Ev") - nz("El")
        qx = nz("pxv") - nz("pxl")
        qy = nz("pyv") - nz("pyl")
        qz = nz("pzv") - nz("pzl")

        En = nz("En")
        pn = np.sqrt(nz("pxn") ** 2 + nz("pyn") ** 2 + nz("pzn") ** 2)
        E2 = (M_P - En - pn ** 2 / (2.0 * m_rec)) * 1000.0
        p2 = pn * 1000.0

        # NB: ak.argmax(where(is_p, x, -1)) returns index 0 (NOT None) when
        # an event has no proton at all — the has-mask below is required or a
        # neutron/photon silently poses as the proton.
        isp = (a.pdgi == 2212)
        has3 = ak.to_numpy(ak.any(isp, axis=1))
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        Ep, pxp, pyp, pzp = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        p3 = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)
        E3 = (omega - (Ep - M_P) - p3 ** 2 / (2.0 * m_rec)) * 1000.0
        E3[~has3] = np.nan
        p3[~has3] = np.nan

        isf = (a.pdgf == 2212)
        has4 = (ak.to_numpy(ak.sum(isf, axis=1)) == 1)     # N_p = 1
        leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
        gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
        Efp, pxf, pyf, pzf = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
        p4 = np.sqrt((pxf - qx) ** 2 + (pyf - qy) ** 2 + (pzf - qz) ** 2)
        E4 = (omega - (Efp - M_P) - p4 ** 2 / (2.0 * m_rec)) * 1000.0
        E4[~has4] = np.nan
        p4[~has4] = np.nan

        parts.append(dict(E2=E2[keep], p2=p2[keep],
                          E3=E3[keep], p3=p3[keep] * 1000.0,
                          E4=E4[keep], p4=p4[keep] * 1000.0))
        ntot += len(keep)
        nsel += int(keep.sum())
        print(f"  ... file {ipath + 1}/{len(paths)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    np.savez_compressed(out_dir / f"{tune}.npz", **out)
    print(f"[{tune}] ntot={ntot}  selected={nsel} ({100.0 * nsel / ntot:.2f}%)"
          f"  -> {out_dir / f'{tune}.npz'}")


def stream(target, tune, max_files):
    cfg = TARGETS[target]
    gridlog = GRIDLOG_ROOT / cfg["run_dir"] / f"{cfg['stems'][tune]}.gridlog"
    build(target, tune, gst_urls(gridlog, max_files), "streaming")


def local(target, tune):
    """Local gst chunks declared in config TARGETS[target]["local_gst"]."""
    pattern = TARGETS[target].get("local_gst", {}).get(tune)
    if not pattern:
        raise SystemExit(f"no local_gst source for {target}/{tune} in config.py")
    paths = sorted(globmod.glob(str(REPO / pattern)))
    if not paths:
        raise SystemExit(f"no files match {REPO / pattern}")
    build(target, tune, paths, "reading local")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--seed-from-v03", action="store_true")
    src.add_argument("--stream", action="store_true")
    src.add_argument("--local", action="store_true")
    ap.add_argument("--target", default="C12", choices=list(TARGETS))
    ap.add_argument("--tune", default=None, choices=sorted(TUNES))
    ap.add_argument("--max-files", type=int, default=20)
    args = ap.parse_args()
    if args.seed_from_v03:
        seed_from_v03()
    elif args.stream:
        for tune in ([args.tune] if args.tune
                     else sorted(TARGETS[args.target]["stems"])):
            stream(args.target, tune, args.max_files)
    else:
        for tune in ([args.tune] if args.tune
                     else sorted(TARGETS[args.target].get("local_gst", {}))):
            local(args.target, tune)

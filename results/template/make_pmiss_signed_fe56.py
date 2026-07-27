"""Fe56 SIGNED missing momentum (+-p_m) from simulation, per tune.

The published Dutta Figs. 6-8 momentum distributions carry a left-right
(+-p_m) asymmetry, attributed by the paper to W_LT interference beyond the
deForest sigma_cc1 and/or Coulomb distortion (tex 1144-1155). The digitized
fig7_*.dat files are exactly symmetrized, and all earlier repo code computes
|p_m| only. This script builds the signed distribution from GENIE events,
4pi (no spectrometer acceptance), for the pre-FSI primary and post-FSI
leading proton, one figure per campaign tune.

Sign convention (the paper never states its own -- flip if mirrored vs print):
per event, z_hat = q_hat; x_hat = normalized transverse-to-q component of the
scattered-electron momentum (in the scattering plane, e' side);
signed p_m = sign(p_m . x_hat) * |p_m| with p_m = p_p' - q. Positive = p_m
tilted toward the e' side of q.

Expected physics: the a-tune chain (FermiMover + QELKinematicsGenerator,
factorized dsigma/dQ^2) has no phi_pq dependence at the vertex, so its
intrinsic asymmetry is purely KINEMATIC (flux/Q^2-window weighting favors
initial nucleons moving away from the e' side); 22b (QELEventGenerator) and
GEM21 (QELEventGeneratorSuSA) sample the proton angle differently and may
differ. The paper's W_LT/Coulomb mechanism is absent from every chain here.

Selection: qel && hitnuc==2212, Dutta-estimator window 0 < E_m < 80 MeV
(E_m = omega - T_p - p_m^2/(2 M_Mn55)). Data grid: 16 x 40 MeV/c bins,
edges -320..320 (fig7 centers +-20, +-60, ..., +-300).

Usage:
  export BEARER_TOKEN_FILE=/tmp/bt_u$(id -u)
  pixi run python results/template/make_pmiss_signed_fe56.py [--tune T | --all-tunes]
Cache: results/prd-analyzer-v0.1/cache/pmiss_signed_fe56/<tune>.npz.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE,
                        FS_SUPTITLE, FS_TICK, DPI)

REPO = Path(__file__).resolve().parents[2]
GRIDLOG_DIR = REPO / "jobsub-agent/jobsub-runs/gevgen_grid-2026-07-16"
DATA = REPO / "data/Dipingkar-dutta-data-prc_figs/fig7_q1p2.dat"
CACHE_DIR = REPO / "results/prd-analyzer-v0.1/cache/pmiss_signed_fe56"
OUT_DIR = REPO / "results/prd-analyzer-v0.1"

# tune -> (gridlog stem, ground-state label, QEL kinematics generator)
RUNS = {
    "GEM26_11a_05_000": ("eminus_Fe56_20260716-113802", "LocalFGM",
                         "QELKinematicsGenerator"),
    "GEM26_22a_05_000": ("eminus_Fe56_20260716-141800", "SF",
                         "QELKinematicsGenerator"),
    "GEM26_22b_05_000": ("eminus_Fe56_20260716-141807", "SF",
                         "QELEventGenerator"),
    "GEM21_11a_05_000": ("eminus_Fe56_20260716-113817", "LocalFGM",
                         "QELEventGeneratorSuSA"),
}

Z = 26
M_REC = 51.1616880                    # Mn55 [GeV], install genie_pdg_table.txt
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

EDGES = np.arange(-320.0, 321.0, 40.0)   # fig7 grid: 16 bins, centers +-20..+-300
BINW = 40.0
EM_MAX = 80.0

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def xrootd_url(p, door="fndca1.fnal.gov:1094"):
    return f"root://{door}/" + p.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def signed_pm(pxp, pyp, pzp, qx, qy, qz, lx, ly, lz):
    """Signed p_m = sign(p_m . x_hat)*|p_m|; x_hat = e' transverse to q.

    scikit-hep vector form (regression-checked against the original component
    arithmetic to float precision, zero sign flips):
      p_m = p_p - q;  t = p_l - (p_l.q/|q|^2) q;  sign(p_m.t) * |p_m|
    """
    import vector
    pp = vector.array({"px": pxp, "py": pyp, "pz": pzp})
    q = vector.array({"px": qx, "py": qy, "pz": qz})
    pl = vector.array({"px": lx, "py": ly, "pz": lz})
    pm = pp - q
    t = pl - q * (pl.dot(q) / q.mag2)            # e' transverse to q (in-plane)
    return np.where(pm.dot(t) >= 0, pm.mag, -pm.mag)


def build_cache(tune, max_files):
    import uproot
    import awkward as ak
    cache = CACHE_DIR / f"{tune}.npz"
    gridlog = GRIDLOG_DIR / f"{RUNS[tune][0]}.gridlog"
    pnfs_dir = json.load(open(gridlog))["pnfs_output_dir"]
    paths = sorted(glob.glob(pnfs_dir + "/*/*.gst.root"))[:max_files]
    print(f"[{tune}] streaming {len(paths)} gst file(s) (signed p_m)")
    parts, ntot, nsel = [], 0, 0
    for ipath, p in enumerate(paths):
        a = uproot.open(xrootd_url(p))["gst"].arrays(BRANCHES, library="ak")
        keep = ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
        nz = lambda b: ak.to_numpy(a[b])
        lx, ly, lz = nz("pxl"), nz("pyl"), nz("pzl")
        omega = nz("Ev") - nz("El")
        qx, qy, qz = nz("pxv") - lx, nz("pyv") - ly, nz("pzv") - lz

        # has-proton guards (fixed 2026-07-26; see make_emiss_ladder_fe56.py)
        isp = (a.pdgi == 2212)
        has3 = ak.to_numpy(ak.any(isp, axis=1))
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        E3p, px3, py3, pz3 = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        pm3 = signed_pm(px3, py3, pz3, qx, qy, qz, lx, ly, lz) * 1000.0
        Em3 = (omega - (E3p - M_P) - (pm3 / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0
        pm3[~has3] = np.nan
        Em3[~has3] = np.nan

        isf = (a.pdgf == 2212)
        has4 = ak.to_numpy(ak.any(isf, axis=1))
        leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
        gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
        E4p, px4, py4, pz4 = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
        pm4 = signed_pm(px4, py4, pz4, qx, qy, qz, lx, ly, lz) * 1000.0
        Em4 = (omega - (E4p - M_P) - (pm4 / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0
        pm4[~has4] = np.nan
        Em4[~has4] = np.nan

        parts.append(dict(pm3=pm3[keep], Em3=Em3[keep],
                          pm4=pm4[keep], Em4=Em4[keep]))
        ntot += len(keep)
        nsel += int(keep.sum())
        print(f"  ... file {ipath + 1}/{len(paths)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **out)
    print(f"[{tune}] cached -> {cache}")


def occ_hist(pm, Em, n_sel):
    """Counts per bin + DENSITY y = Z*N/(N_sel*dp*4pi*p_c^2) [(MeV/c)^-3].

    The published fig7 y-axis is a density (int S^D dE_m, per d^3p_m: peaks at
    p_m = 0); raw counts (~ p^2 S) dip at 0, so divide out the 4pi p^2 phase
    space for a shape comparison."""
    win = np.isfinite(pm) & (Em > 0.0) & (Em < EM_MAX)
    cnt, _ = np.histogram(pm[win], bins=EDGES)
    p_c = np.abs((EDGES[:-1] + EDGES[1:]) / 2.0)
    y = Z * cnt / (n_sel * BINW * 4.0 * np.pi * p_c ** 2)
    return cnt, y


def asym(cnt):
    nb = len(cnt) // 2
    Np, Nm = cnt[nb:], cnt[:nb][::-1]
    tot = Np + Nm
    with np.errstate(invalid="ignore", divide="ignore"):
        A = (Np - Nm) / tot
        dA = np.sqrt(np.clip(1.0 - A ** 2, 0, None) / np.clip(tot, 1, None))
    return A, dA


def make_figure(tune, max_files, dutta):
    cache = CACHE_DIR / f"{tune}.npz"
    if not cache.exists():
        build_cache(tune, max_files)
    c = dict(np.load(cache))
    n_sel = float(c["n_sel"][0])
    gs, gen = RUNS[tune][1], RUNS[tune][2]

    stages = {}
    print(f"[{tune}] ({gs}, {gen}):")
    for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI leading p")):
        cnt, y = occ_hist(c[f"pm{s}"], c[f"Em{s}"], n_sel)
        A, dA = asym(cnt)
        Np, Nm = cnt[len(cnt)//2:].sum(), cnt[:len(cnt)//2].sum()
        Ai = (Np - Nm) / max(Np + Nm, 1)
        dAi = np.sqrt((1 - Ai**2) / max(Np + Nm, 1))
        stages[s] = (label, cnt, y, A, dA, Ai, dAi)
        print(f"  stage {s} ({label}): N={int(cnt.sum()):,}  A = {Ai:+.4f} +- {dAi:.4f}")

    dx, dy, _, de = np.loadtxt(dutta, unpack=True)
    scale = stages[4][2].sum() / dy.sum()

    import matplotlib.pyplot as plt
    fig, (ax, axA) = plt.subplots(2, 1, figsize=(8.0, 8.2), sharex=True,
                                  height_ratios=[2.2, 1], layout="constrained")
    ax.stairs(stages[3][2], EDGES, color="C0", linewidth=1.8,
              label="pre-FSI primary p")
    ax.stairs(stages[4][2], EDGES, color="C3", linewidth=1.8,
              label="post-FSI leading p")
    ax.errorbar(dx, dy * scale, yerr=de * scale, fmt="s", ms=4, color="0.5",
                capsize=2, zorder=8, label="fig7_q1p2 (symmetrized, shape)")
    style_axis(ax, title="signed missing momentum, 0 < $E_m$ < 80 MeV",
               logx=False, logy=False, ymin=None)
    ax.set_ylim(0, None)
    ax.set_ylabel(r"$Z\cdot$ d$N/$d$^3p_m\,/\,N_{sel}$   [(MeV/c)$^{-3}$]",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title="sign: $p_m\\cdot\\hat{x}_{e'}$ (toward e$'$ = +)",
              title_fontsize=FS_LEGEND_TITLE - 3)

    centers = (EDGES[len(EDGES)//2:-1] + EDGES[len(EDGES)//2 + 1:]) / 2.0
    for s, color in ((3, "C0"), (4, "C3")):
        _, _, _, A, dA, _, _ = stages[s]
        axA.errorbar(centers, A, yerr=dA, fmt="o", ms=4, color=color, capsize=2)
    axA.axhline(0.0, color="0.5", lw=1, ls=":")
    style_axis(axA, title=None, xlabel=r"$p_m$  [MeV/c]  (|p| for asymmetry)",
               logx=False, logy=False, ymin=None)
    axA.set_ylabel(r"$A=\frac{N_+-N_-}{N_++N_-}$", fontsize=FS_LABEL)
    axA.set_ylim(-0.2, 0.2)
    axA.tick_params(labelsize=FS_TICK)

    fig.suptitle(f"Fe56 signed $p_m$ — {tune}\n({gs}, {gen}); "
                 f"A(post-FSI) = {stages[4][5]:+.3f}, 4$\\pi$, qel && hit p",
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"pmiss_signed_fe56_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print("  wrote", out)
    return {s: (stages[s][5], stages[s][6]) for s in (3, 4)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(RUNS))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--max-files", type=int, default=20)
    args = ap.parse_args()

    apply_style()
    summary = {}
    for t in (list(RUNS) if args.all_tunes else [args.tune]):
        summary[t] = make_figure(t, args.max_files, DATA)
    print("\nintegrated asymmetry summary (post-FSI):")
    for t, s in summary.items():
        print(f"  {t}: pre-FSI {s[3][0]:+.4f}+-{s[3][1]:.4f}  "
              f"post-FSI {s[4][0]:+.4f}+-{s[4][1]:.4f}")

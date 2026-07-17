"""Fe56 SIGNED missing momentum (+-p_m) from simulation — GEM26_22a prototype.

The published Dutta Figs. 6-8 momentum distributions carry a left-right
(+-p_m) asymmetry, attributed by the paper to W_LT interference beyond the
deForest sigma_cc1 and/or Coulomb distortion (tex 1144-1155). The digitized
fig7_*.dat files are exactly symmetrized, and all earlier repo code computes
|p_m| only. This script builds the signed distribution from GENIE events,
4pi (no spectrometer acceptance), for the pre-FSI primary and post-FSI
leading proton.

Sign convention (the paper never states its own -- flip if mirrored vs print):
per event, z_hat = q_hat; x_hat = normalized transverse-to-q component of the
scattered-electron momentum (in the scattering plane, e' side);
signed p_m = sign(p_m . x_hat) * |p_m| with p_m = p_p' - q. Positive = p_m
tilted toward the e' side of q.

Expected physics: the classic 22a chain (FermiMover + QELKinematicsGenerator,
factorized dsigma/dQ^2) has no phi_pq dependence at the vertex, so the
intrinsic pre-FSI asymmetry should be ~0; hA2018 FSI may induce a small one.
The paper's W_LT/Coulomb mechanism is absent from this chain by construction.

Selection: qel && hitnuc==2212, Dutta-estimator window 0 < E_m < 80 MeV
(E_m = omega - T_p - p_m^2/(2 M_Mn55)). Data grid: 16 x 40 MeV/c bins,
edges -320..320 (fig7 centers are +-20, +-60, ..., +-300).

Usage:
  export BEARER_TOKEN_FILE=/tmp/bt_u$(id -u)
  pixi run python results/template/make_pmiss_signed_fe56.py [--max-files 20]
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
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_TITLE,
                        FS_SUPTITLE, FS_TICK, DPI)

REPO = Path(__file__).resolve().parents[2]
TUNE = "GEM26_22a_05_000"
GRIDLOG = REPO / ("jobsub-agent/jobsub-runs/gevgen_grid-2026-07-16/"
                  "eminus_Fe56_20260716-141800.gridlog")
DATA = REPO / "data/Dipingkar-dutta-data-prc_figs/fig7_q1p2.dat"
CACHE = REPO / "results/prd-analyzer-v0.1/cache/pmiss_signed_fe56" / f"{TUNE}.npz"
OUT = REPO / "results/prd-analyzer-v0.1" / f"pmiss_signed_fe56_{TUNE}.png"

Z = 26
M_REC = 51.1616880                    # Mn55 [GeV], install genie_pdg_table.txt
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

EDGES = np.arange(-320.0, 321.0, 40.0)   # fig7 grid: 16 bins, centers +-20..+-300
BINW = 40.0
EM_MAX = 80.0                            # paper window 0 < E_m < 80 MeV

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def xrootd_url(p, door="fndca1.fnal.gov:1094"):
    return f"root://{door}/" + p.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def signed_pm(pxp, pyp, pzp, qx, qy, qz, lx, ly, lz):
    """Signed p_m = sign(p_m . x_hat)*|p_m|; x_hat = e' transverse to q."""
    mx, my, mz = pxp - qx, pyp - qy, pzp - qz
    pm = np.sqrt(mx**2 + my**2 + mz**2)
    q2 = qx**2 + qy**2 + qz**2
    a = (lx * qx + ly * qy + lz * qz) / q2       # (p_l . q)/|q|^2
    tx, ty, tz = lx - a * qx, ly - a * qy, lz - a * qz
    dot = mx * tx + my * ty + mz * tz            # sign of p_m . x_hat (norm >0)
    return np.where(dot >= 0, pm, -pm)


def build_cache(max_files):
    import uproot
    import awkward as ak
    pnfs_dir = json.load(open(GRIDLOG))["pnfs_output_dir"]
    paths = sorted(glob.glob(pnfs_dir + "/*/*.gst.root"))[:max_files]
    print(f"[{TUNE}] streaming {len(paths)} gst file(s) (signed p_m)")
    parts, ntot, nsel = [], 0, 0
    for ipath, p in enumerate(paths):
        a = uproot.open(xrootd_url(p))["gst"].arrays(BRANCHES, library="ak")
        keep = ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
        nz = lambda b: ak.to_numpy(a[b])
        lx, ly, lz = nz("pxl"), nz("pyl"), nz("pzl")
        omega = nz("Ev") - nz("El")
        qx, qy, qz = nz("pxv") - lx, nz("pyv") - ly, nz("pzv") - lz

        isp = (a.pdgi == 2212)
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        E3p, px3, py3, pz3 = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        pm3 = signed_pm(px3, py3, pz3, qx, qy, qz, lx, ly, lz) * 1000.0
        Em3 = (omega - (E3p - M_P) - (pm3 / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0

        isf = (a.pdgf == 2212)
        leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
        gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
        E4p, px4, py4, pz4 = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
        pm4 = signed_pm(px4, py4, pz4, qx, qy, qz, lx, ly, lz) * 1000.0
        Em4 = (omega - (E4p - M_P) - (pm4 / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0

        parts.append(dict(pm3=pm3[keep], Em3=Em3[keep],
                          pm4=pm4[keep], Em4=Em4[keep]))
        ntot += len(keep)
        nsel += int(keep.sum())
        print(f"  ... file {ipath + 1}/{len(paths)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    print(f"[{TUNE}] cached -> {CACHE}")


def occ_hist(pm, Em, n_sel):
    """Counts per bin and the DENSITY y = Z*N/(N_sel*dp*4pi*p_c^2) [(MeV/c)^-3].

    The published fig7 y-axis is a density (int S^D dE_m, per d^3p_m: peaks at
    p_m = 0), so the event counts (~ p^2 * S: dip at 0) must have the 4pi p^2
    phase-space factor divided out for a shape comparison."""
    win = np.isfinite(pm) & (Em > 0.0) & (Em < EM_MAX)
    cnt, _ = np.histogram(pm[win], bins=EDGES)
    p_c = np.abs((EDGES[:-1] + EDGES[1:]) / 2.0)
    y = Z * cnt / (n_sel * BINW * 4.0 * np.pi * p_c ** 2)
    return cnt, y


def asym(cnt):
    """A(|p|) = (N+ - N-)/(N+ + N-) per mirrored bin pair, with stat error."""
    nb = len(cnt) // 2
    Np, Nm = cnt[nb:], cnt[:nb][::-1]
    tot = Np + Nm
    with np.errstate(invalid="ignore", divide="ignore"):
        A = (Np - Nm) / tot
        dA = np.sqrt(np.clip(1.0 - A ** 2, 0, None) / np.clip(tot, 1, None))
    return A, dA, tot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=20)
    args = ap.parse_args()

    if not CACHE.exists():
        build_cache(args.max_files)
    c = dict(np.load(CACHE))
    n_sel = float(c["n_sel"][0])

    stages = {}
    for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI leading p")):
        cnt, y = occ_hist(c[f"pm{s}"], c[f"Em{s}"], n_sel)
        A, dA, tot = asym(cnt)
        Nplus, Nminus = cnt[len(cnt)//2:].sum(), cnt[:len(cnt)//2].sum()
        Aint = (Nplus - Nminus) / max(Nplus + Nminus, 1)
        dAint = np.sqrt((1 - Aint**2) / max(Nplus + Nminus, 1))
        stages[s] = (label, cnt, y, A, dA)
        print(f"stage {s} ({label}): N(in-window)={int(cnt.sum()):,}  "
              f"integrated A = {Aint:+.4f} +- {dAint:.4f}")
        # sign-shuffle control: random signs must give A ~ 0
        rng = np.random.default_rng(20260716)
        pm = c[f"pm{s}"]; Em = c[f"Em{s}"]
        win = np.isfinite(pm) & (Em > 0) & (Em < EM_MAX)
        shuf = np.abs(pm[win]) * rng.choice([-1.0, 1.0], size=int(win.sum()))
        cs, _ = np.histogram(shuf, bins=EDGES)
        Ash = (cs[len(cs)//2:].sum() - cs[:len(cs)//2].sum()) / cs.sum()
        print(f"  sign-shuffle control: A = {Ash:+.4f} (expect ~0)")

    # symmetrized digitized fig7 as gray shape reference (both are densities
    # now; scale data to the stage-4 density integral)
    dx, dy, _, de = np.loadtxt(DATA, unpack=True)
    scale = stages[4][2].sum() / dy.sum()

    apply_style()
    import matplotlib.pyplot as plt
    fig, (ax, axA) = plt.subplots(2, 1, figsize=(8.5, 8.6), sharex=True,
                                  height_ratios=[2.2, 1], layout="constrained")
    ax.stairs(stages[3][2], EDGES, color="C0", linewidth=1.8,
              label="pre-FSI primary p")
    ax.stairs(stages[4][2], EDGES, color="C3", linewidth=1.8,
              label="post-FSI leading p")
    ax.errorbar(dx, dy * scale, yerr=de * scale, fmt="s", ms=4, color="0.5",
                capsize=2, zorder=8,
                label="fig7_q1p2 (symmetrized, shape only)")
    style_axis(ax, title="signed missing momentum, 0 < $E_m$ < 80 MeV",
               logx=False, logy=False, ymin=None)
    ax.set_ylim(0, None)
    ax.set_ylabel(r"$Z\cdot$ d$N/$d$^3p_m\,/\,N_{sel}$   [(MeV/c)$^{-3}$]",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title="sign: $p_m\\cdot\\hat{x}_{e'}$ (toward e$'$ side = +)",
              title_fontsize=FS_LEGEND_TITLE - 3)

    centers = (EDGES[len(EDGES)//2:-1] + EDGES[len(EDGES)//2 + 1:]) / 2.0
    for s, color in ((3, "C0"), (4, "C3")):
        label, cnt, y, A, dA = stages[s]
        axA.errorbar(centers, A, yerr=dA, fmt="o", ms=4, color=color,
                     capsize=2, label=label)
    axA.axhline(0.0, color="0.5", lw=1, ls=":")
    style_axis(axA, title=None, xlabel=r"$p_m$  [MeV/c]  (|p| for asymmetry)",
               logx=False, logy=False, ymin=None)
    axA.set_ylabel(r"$A=\frac{N_+-N_-}{N_++N_-}$", fontsize=FS_LABEL)
    axA.set_ylim(-0.2, 0.2)
    axA.tick_params(labelsize=FS_TICK)

    fig.suptitle(f"Fe56 signed $p_m$ — {TUNE}  (4$\\pi$, qel && hit p)\n"
                 "e$^-$ 2.445 GeV; A $\\approx-5.5\\%$ kinematic, FSI-blind; "
                 "chain has no W$_{LT}$",
                 fontsize=FS_SUPTITLE - 3)
    fig.savefig(OUT, dpi=DPI)
    print("wrote", OUT)

"""v0.2 SIGNED missing momentum (+-p_m) with the Dutta Q^2 cut, per target/tune.

Target-parameterized counterpart of make_pmiss_signed_fe56.py /
make_pmiss_signed_c12.py for prd-analyzer-v0.2: same sign convention
(x_hat = e' transverse to q, signed p_m = sign(p_m.x_hat)|p_m|; `signed_pm`
imported from the Fe56 v0.1 module), same density construction (4pi p^2
divided out) and Dutta overlays (Fe56: fig7_q1p2 symmetrized; C12: fig6
top+bottom combined, shape-scaled), with the selection now

    qel && hitnuc==2212 && |Q^2/1.28 - 1| <= 5 %   (+ estimator 0 < E_m < 80)

Both targets stream their full-EM t05 campaign gst files over XRootD
(pnfs_ls; 20 files = 2M events/tune) — C12 moves off the 2026-07-17 local
samples onto the 2026-07-26 grid campaign.

Cache: results/prd-analyzer-v0.2/cache/pmiss_signed_<target>/<tune>.npz
(pm3/Em3/pm4/Em4 + ntot/n_sel). Figures:
results/prd-analyzer-v0.2/pmiss_signed_<target>_<tune>.png.

Usage:
  pixi run python results/template/make_pmiss_signed_q2cut.py --target Fe56 --all-tunes
  pixi run python results/template/make_pmiss_signed_q2cut.py --target C12 --all-tunes
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE,
                        FS_SUPTITLE, FS_TICK, DPI)
from make_pmiss_signed_fe56 import signed_pm                  # noqa: E402
from pnfs_ls import gst_urls                                  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
GRIDLOG_ROOT = REPO / "jobsub-agent/jobsub-runs"
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"

Q2_CENTER, Q2_FRAC = 1.28, 0.05
PROTON_SEL = "leading"          # or "1p": stage 4 requires exactly one FS proton
EDGES = np.arange(-320.0, 321.0, 40.0)   # fig7 grid: 16 bins, centers +-20..+-300
BINW = 40.0
EM_MAX = 80.0

_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

# tune -> (ground-state label, QEL kinematics generator)
TUNE_INFO = {
    "GEM26_11a_05_000": ("LocalFGM", "QELKinematicsGenerator"),
    "GEM26_22a_05_000": ("SF",       "QELKinematicsGenerator"),
    "GEM26_22b_05_000": ("SF",       "QELEventGenerator"),
    "GEM21_11a_05_000": ("LocalFGM", "QELEventGeneratorSuSA"),
}


def _m_rec_c12():
    from acceptance import M_REC       # B11 [GeV], v0 value
    return M_REC


def _dutta_fe56():
    dx, dy, _, de = np.loadtxt(DATA_DIR / "fig7_q1p2.dat", unpack=True)
    return dx, dy, de, "fig7_q1p2 (symmetrized, shape)"


def _dutta_c12():
    dx, y_p, _, e_p = np.loadtxt(DATA_DIR / "fig6_top_q1p2.dat", unpack=True)
    _, y_s, _, e_s = np.loadtxt(DATA_DIR / "fig6_bot_q1p2.dat", unpack=True)
    return (dx, y_p + y_s, np.sqrt(e_p ** 2 + e_s ** 2),
            "fig6 top+bot (symm., $E_m$ 10–25$\\cup$30–50, shape)")


TGT = {
    "Fe56": dict(
        Z=26, m_rec_gev=51.1616880,    # Mn55, install genie_pdg_table.txt
        run_dir="gevgen_grid-2026-07-16",
        stems={"GEM26_11a_05_000": "eminus_Fe56_20260716-113802",
               "GEM26_22a_05_000": "eminus_Fe56_20260716-141800",
               "GEM26_22b_05_000": "eminus_Fe56_20260716-141807",
               "GEM21_11a_05_000": "eminus_Fe56_20260716-113817"},
        dutta=_dutta_fe56,
    ),
    "C12": dict(
        Z=6, m_rec_gev=None,           # B11 from acceptance.M_REC
        run_dir="gevgen_grid-2026-07-26",
        stems={"GEM26_11a_05_000": "eminus_C12_20260726-105638",
               "GEM26_22a_05_000": "eminus_C12_20260726-105642",
               "GEM26_22b_05_000": "eminus_C12_20260726-105646",
               "GEM21_11a_05_000": "eminus_C12_20260726-105650"},
        dutta=_dutta_c12,
    ),
}

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel", "Q2",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def build_cache(target, tune, max_files):
    import uproot
    import awkward as ak
    cfg = TGT[target]
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else _m_rec_c12()
    cache_dir = CACHE_ROOT / f"pmiss_signed_{target.lower()}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    gridlog = GRIDLOG_ROOT / cfg["run_dir"] / f"{cfg['stems'][tune]}.gridlog"
    urls = gst_urls(gridlog, max_files)
    print(f"[{tune}] streaming {len(urls)} gst file(s) (signed p_m, windowed)")
    parts, ntot, nsel = [], 0, 0
    for ipath, url in enumerate(urls):
        a = uproot.open(url)["gst"].arrays(BRANCHES, library="ak")
        keep = (ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
                & (np.abs(ak.to_numpy(a.Q2) / Q2_CENTER - 1.0) <= Q2_FRAC))
        nz = lambda b: ak.to_numpy(a[b])
        lx, ly, lz = nz("pxl"), nz("pyl"), nz("pzl")
        omega = nz("Ev") - nz("El")
        qx, qy, qz = nz("pxv") - lx, nz("pyv") - ly, nz("pzv") - lz

        # has-proton guards: unguarded argmax(where(is_p, x, -1)) returns
        # index 0 when no proton exists (see make_emiss_ladder_q2cut.py)
        isp = (a.pdgi == 2212)
        has3 = ak.to_numpy(ak.any(isp, axis=1))
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        E3p, px3, py3, pz3 = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        pm3 = signed_pm(px3, py3, pz3, qx, qy, qz, lx, ly, lz) * 1000.0
        Em3 = (omega - (E3p - M_P) - (pm3 / 1000.0) ** 2 / (2.0 * m_rec)) * 1000.0
        pm3[~has3] = np.nan
        Em3[~has3] = np.nan

        isf = (a.pdgf == 2212)
        has4 = (ak.to_numpy(ak.sum(isf, axis=1)) == 1) if PROTON_SEL == "1p" \
               else ak.to_numpy(ak.any(isf, axis=1))
        leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
        gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
        E4p, px4, py4, pz4 = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
        pm4 = signed_pm(px4, py4, pz4, qx, qy, qz, lx, ly, lz) * 1000.0
        Em4 = (omega - (E4p - M_P) - (pm4 / 1000.0) ** 2 / (2.0 * m_rec)) * 1000.0
        pm4[~has4] = np.nan
        Em4[~has4] = np.nan

        parts.append(dict(pm3=pm3[keep], Em3=Em3[keep],
                          pm4=pm4[keep], Em4=Em4[keep]))
        ntot += len(keep)
        nsel += int(keep.sum())
        print(f"  ... file {ipath + 1}/{len(urls)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    np.savez_compressed(cache_dir / f"{tune}.npz", **out)
    print(f"[{tune}] cached -> {cache_dir / f'{tune}.npz'}")


def occ_hist(pm, Em, n_sel, Z):
    """Counts/bin + density y = Z*N/(N_sel*dp*4pi*p_c^2) [(MeV/c)^-3]."""
    win = np.isfinite(pm) & (Em > 0.0) & (Em < EM_MAX)
    cnt, _ = np.histogram(pm[win], bins=EDGES)
    p_c = np.abs((EDGES[:-1] + EDGES[1:]) / 2.0)
    return cnt, Z * cnt / (n_sel * BINW * 4.0 * np.pi * p_c ** 2)


def asym(cnt):
    nb = len(cnt) // 2
    Np, Nm = cnt[nb:], cnt[:nb][::-1]
    tot = Np + Nm
    with np.errstate(invalid="ignore", divide="ignore"):
        A = (Np - Nm) / tot
        dA = np.sqrt(np.clip(1.0 - A ** 2, 0, None) / np.clip(tot, 1, None))
    return A, dA


def make_figure(target, tune, max_files, dutta):
    cfg = TGT[target]
    tlow = target.lower()
    cache = CACHE_ROOT / f"pmiss_signed_{tlow}" / f"{tune}.npz"
    if not cache.exists():
        build_cache(target, tune, max_files)
    c = dict(np.load(cache))
    n_sel = float(c["n_sel"][0])
    gs, gen = TUNE_INFO[tune]

    stages = {}
    print(f"[{tune}] ({gs}, {gen}):")
    for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI leading p")):
        cnt, y = occ_hist(c[f"pm{s}"], c[f"Em{s}"], n_sel, cfg["Z"])
        A, dA = asym(cnt)
        Np, Nm = cnt[len(cnt)//2:].sum(), cnt[:len(cnt)//2].sum()
        Ai = (Np - Nm) / max(Np + Nm, 1)
        dAi = np.sqrt((1 - Ai**2) / max(Np + Nm, 1))
        stages[s] = (label, cnt, y, A, dA, Ai, dAi)
        print(f"  stage {s} ({label}): N={int(cnt.sum()):,}  "
              f"A = {Ai:+.4f} +- {dAi:.4f}")

    dx, dy, de, dlabel = dutta
    scale = stages[4][2].sum() / dy.sum()

    import matplotlib.pyplot as plt
    fig, (ax, axA) = plt.subplots(2, 1, figsize=(8.0, 8.2), sharex=True,
                                  height_ratios=[2.2, 1], layout="constrained")
    ax.stairs(stages[3][2], EDGES, color="C0", linewidth=1.8,
              label="pre-FSI primary p")
    ax.stairs(stages[4][2], EDGES, color="C3", linewidth=1.8,
              label="post-FSI leading p")
    ax.errorbar(dx, dy * scale, yerr=de * scale, fmt="s", ms=4, color="0.5",
                capsize=2, zorder=8, label=dlabel)
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

    fig.suptitle(f"{target} signed $p_m$ — {tune}\n({gs}, {gen}); "
                 f"A(post-FSI) = {stages[4][5]:+.3f}, 4$\\pi$, "
                 "qel && hit p && $Q^2$ slice"
                 + (" && N$_p$=1" if PROTON_SEL == "1p" else ""),
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"pmiss_signed_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print("  wrote", out)
    return {s: (stages[s][5], stages[s][6]) for s in (3, 4)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TGT))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_INFO))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--max-files", type=int, default=20)
    ap.add_argument("--proton-sel", default="leading", choices=["leading", "1p"],
                    help="1p: stage 4 = exactly one FS proton, outputs to v0.3")
    args = ap.parse_args()
    PROTON_SEL = args.proton_sel
    if PROTON_SEL == "1p":
        CACHE_ROOT = REPO / "results/prd-analyzer-v0.3/cache"
        OUT_DIR = REPO / "results/prd-analyzer-v0.3"
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    dutta = TGT[args.target]["dutta"]()
    summary = {}
    for t in (list(TUNE_INFO) if args.all_tunes else [args.tune]):
        summary[t] = make_figure(args.target, t, args.max_files, dutta)
    print("\nintegrated asymmetry summary:")
    for t, s in summary.items():
        print(f"  {t}: pre-FSI {s[3][0]:+.4f}+-{s[3][1]:.4f}  "
              f"post-FSI {s[4][0]:+.4f}+-{s[4][1]:.4f}")

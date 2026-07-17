"""C12 SIGNED missing momentum (+-p_m) from simulation — GEM26_22a prototype.

C12 sibling of make_pmiss_signed_fe56.py (same sign convention, same panels).
The June-2026 C12 grid samples are purged from scratch dCache, so this reads a
LOCALLY regenerated GEM26_22a_05_000 C12 EMQE sample (run_gevgen.py with the
patched genie_inclxx install + a local EMQE spline; the gst is produced by
run_gntpc.py). Selection: hitnuc==2212 (EMQE -> all events QEL), Dutta window
0 < E_m < 80 MeV with the B11 recoil. No data overlay: the digitized C12
momentum distributions (fig6) are shell-split (10<E_m<25 / 30<E_m<50 MeV)
and symmetrized, so no 0-80 MeV signed reference exists.

Sign convention and expectation: identical to the Fe56 script (sign of
p_m . x_hat, x_hat = e' transverse-to-q, positive = toward the e' side;
the 22a chain carries a kinematic asymmetry, no W_LT).

Usage:
  pixi run python results/template/make_pmiss_signed_c12.py --gst <local .gst.root>
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
from make_pmiss_signed_fe56 import signed_pm, BRANCHES   # noqa: E402
from acceptance import M_REC                             # B11 [GeV] (v0 value)

REPO = Path(__file__).resolve().parents[2]
TUNE = "GEM26_22a_05_000"
OUT = REPO / "results/prd-analyzer-v0.1" / f"pmiss_signed_c12_{TUNE}.png"

Z = 6
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

EDGES = np.arange(-320.0, 321.0, 40.0)
BINW = 40.0
EM_MAX = 80.0


def load(gst_path):
    import uproot
    import awkward as ak
    a = uproot.open(gst_path)["gst"].arrays(BRANCHES, library="ak")
    keep = ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
    nz = lambda b: ak.to_numpy(a[b])
    lx, ly, lz = nz("pxl"), nz("pyl"), nz("pzl")
    omega = nz("Ev") - nz("El")
    qx, qy, qz = nz("pxv") - lx, nz("pyv") - ly, nz("pzv") - lz

    out = {}
    for s, pdgb, momb, leadby in ((3, "pdgi", "i", "Ei"), (4, "pdgf", "f", "pf")):
        isp = (a[pdgb] == 2212)
        lead = ak.argmax(ak.where(isp, a[leadby], -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(a[b][lead]), np.nan))
        Ep = g(f"E{momb}")
        px, py, pz = g(f"px{momb}"), g(f"py{momb}"), g(f"pz{momb}")
        pm = signed_pm(px, py, pz, qx, qy, qz, lx, ly, lz) * 1000.0
        Em = (omega - (Ep - M_P) - (pm / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0
        out[f"pm{s}"], out[f"Em{s}"] = pm[keep], Em[keep]
    return out, len(keep), int(keep.sum())


def occ_hist(pm, Em, n_sel):
    win = np.isfinite(pm) & (Em > 0.0) & (Em < EM_MAX)
    cnt, _ = np.histogram(pm[win], bins=EDGES)
    p_c = np.abs((EDGES[:-1] + EDGES[1:]) / 2.0)
    y = Z * cnt / (n_sel * BINW * 4.0 * np.pi * p_c ** 2)   # density [(MeV/c)^-3]
    return cnt, y


def asym(cnt):
    nb = len(cnt) // 2
    Np, Nm = cnt[nb:], cnt[:nb][::-1]
    tot = Np + Nm
    with np.errstate(invalid="ignore", divide="ignore"):
        A = (Np - Nm) / tot
        dA = np.sqrt(np.clip(1.0 - A ** 2, 0, None) / np.clip(tot, 1, None))
    return A, dA


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gst", required=True, help="local C12 22a_05 EMQE gst file")
    args = ap.parse_args()

    c, ntot, nsel = load(args.gst)
    print(f"{TUNE}: {ntot:,} events, {nsel:,} selected (hit p)")

    stages = {}
    for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI leading p")):
        cnt, y = occ_hist(c[f"pm{s}"], c[f"Em{s}"], float(nsel))
        A, dA = asym(cnt)
        Np, Nm = cnt[len(cnt)//2:].sum(), cnt[:len(cnt)//2].sum()
        Ai = (Np - Nm) / max(Np + Nm, 1)
        dAi = np.sqrt((1 - Ai**2) / max(Np + Nm, 1))
        stages[s] = (label, cnt, y, A, dA)
        print(f"stage {s} ({label}): N(in-window)={int(cnt.sum()):,}  "
              f"integrated A = {Ai:+.4f} +- {dAi:.4f}")
        rng = np.random.default_rng(20260717)
        pm, Em = c[f"pm{s}"], c[f"Em{s}"]
        win = np.isfinite(pm) & (Em > 0) & (Em < EM_MAX)
        shuf = np.abs(pm[win]) * rng.choice([-1.0, 1.0], size=int(win.sum()))
        cs, _ = np.histogram(shuf, bins=EDGES)
        print(f"  sign-shuffle control: A = "
              f"{(cs[len(cs)//2:].sum() - cs[:len(cs)//2].sum()) / cs.sum():+.4f}")

    apply_style()
    import matplotlib.pyplot as plt
    fig, (ax, axA) = plt.subplots(2, 1, figsize=(8.5, 8.6), sharex=True,
                                  height_ratios=[2.2, 1], layout="constrained")
    ax.stairs(stages[3][2], EDGES, color="C0", linewidth=1.8,
              label="pre-FSI primary p")
    ax.stairs(stages[4][2], EDGES, color="C3", linewidth=1.8,
              label="post-FSI leading p")
    style_axis(ax, title="signed missing momentum, 0 < $E_m$ < 80 MeV",
               logx=False, logy=False, ymin=None)
    ax.set_ylim(0, None)
    ax.set_ylabel(r"$Z\cdot$ d$N/$d$^3p_m\,/\,N_{sel}$   [(MeV/c)$^{-3}$]",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title="sign: $p_m\\cdot\\hat{x}_{e'}$ (toward e$'$ side = +)\n"
                    "no data overlay: fig6 is shell-split",
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

    fig.suptitle(f"C12 signed $p_m$ — {TUNE}  (4$\\pi$, EMQE, hit p)\n"
                 "e$^-$ 2.445 GeV, locally regenerated sample "
                 "(grid originals purged)",
                 fontsize=FS_SUPTITLE - 3)
    fig.savefig(OUT, dpi=DPI)
    print("wrote", OUT)

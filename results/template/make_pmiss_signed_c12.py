"""C12 SIGNED missing momentum (+-p_m) from simulation, per tune.

C12 sibling of make_pmiss_signed_fe56.py (same sign convention, same panels),
one figure per campaign tune. The June-2026 C12 grid samples are purged from
scratch dCache, so this runs on LOCALLY regenerated C12 EMQE samples (patched
genie_inclxx install; per-tune EMQE spline + run_gevgen.py 500k events +
run_gntpc.py gst, all labeled 'c12-signed-pm', 2026-07-17). Each tune's gst is
resolved automatically from its genie-runs logs (runtype gevgen, that label,
target C12). Selection hitnuc==2212 (EMQE -> all QEL), Dutta window
0 < E_m < 80 MeV with the B11 recoil.

Data overlay: fig6_top + fig6_bot (q1p2) COMBINED -- the C12 momentum
distributions are published per E_m shell window (p-shell 10-25, s-shell
30-50 MeV), so their sum covers E_m in (10,25) u (30,50) with a gap at 25-30
and nothing outside; the MC window stays 0-80 MeV (per user: combine, leave
the gap). Shape only, scaled to the post-FSI integral; symmetrized.

Sign convention/expectation identical to the Fe56 script (a-tunes kinematic,
no W_LT; 22b/GEM21 use different QEL samplers and may differ).

Usage: pixi run python results/template/make_pmiss_signed_c12.py [--tune T | --all-tunes]
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE,
                        FS_SUPTITLE, FS_TICK, DPI)
from make_pmiss_signed_fe56 import signed_pm, BRANCHES, occ_hist, asym  # noqa: E402
from acceptance import M_REC                             # B11 [GeV] (v0 value)

REPO = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO / "genie-agent/genie-runs"
DATA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"
OUT_DIR = REPO / "results/prd-analyzer-v0.1"
LABEL = "c12-signed-pm"

# tune -> (ground-state label, QEL kinematics generator)
RUNS = {
    "GEM26_11a_05_000": ("LocalFGM", "QELKinematicsGenerator"),
    "GEM26_22a_05_000": ("SF",       "QELKinematicsGenerator"),
    "GEM26_22b_05_000": ("SF",       "QELEventGenerator"),
    "GEM21_11a_05_000": ("LocalFGM", "QELEventGeneratorSuSA"),
}

Z = 6
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)
EDGES = np.arange(-320.0, 321.0, 40.0)
EM_MAX = 80.0

# occ_hist/asym imported from the Fe56 module use its Z=26 and EM_MAX; C12 needs
# Z=6. occ_hist's Z cancels in the shape/asymmetry, but keep the density scale
# correct by recomputing here with the C12 Z.
BINW = 40.0


def occ_hist_c12(pm, Em, n_sel):
    win = np.isfinite(pm) & (Em > 0.0) & (Em < EM_MAX)
    cnt, _ = np.histogram(pm[win], bins=EDGES)
    p_c = np.abs((EDGES[:-1] + EDGES[1:]) / 2.0)
    return cnt, Z * cnt / (n_sel * BINW * 4.0 * np.pi * p_c ** 2)


def resolve_gst(tune):
    """Find the tune's local signed-p_m gevgen gst (newest if several).

    Match the 500k-event EMQE C12 samples (label c12-signed-pm, or the first
    22a run which predates the label) and exclude the 2k-event EMRES ladder
    repros; require the .gst.root exists."""
    best = None
    for log in glob.glob(str(RUNS_DIR / f"{tune}-*/*.log")):
        try:
            d = json.load(open(log))
        except Exception:
            continue
        inp = d.get("inputs", {})
        if (d.get("runtype") == "gevgen" and inp.get("target") == "C12"
                and inp.get("genlist") == "EMQE"
                and (inp.get("n_events") or 0) >= 500000
                and d.get("returncode") == 0):
            gst = log[:-4] + ".gst.root"
            if Path(gst).exists() and (best is None or gst > best):
                best = gst
    if best is None:
        raise SystemExit(f"no signed-p_m gst for {tune} (regenerate locally)")
    return best


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
    for s, momb, leadby in ((3, "i", "Ei"), (4, "f", "pf")):
        pdgb = f"pdg{momb}"
        isp = (a[pdgb] == 2212)
        # has-proton guard (fixed 2026-07-26; see make_emiss_ladder_fe56.py)
        hasp = ak.to_numpy(ak.any(isp, axis=1))
        lead = ak.argmax(ak.where(isp, a[leadby], -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(a[b][lead]), np.nan))
        Ep = g(f"E{momb}")
        px, py, pz = g(f"px{momb}"), g(f"py{momb}"), g(f"pz{momb}")
        pm = signed_pm(px, py, pz, qx, qy, qz, lx, ly, lz) * 1000.0
        Em = (omega - (Ep - M_P) - (pm / 1000.0) ** 2 / (2.0 * M_REC)) * 1000.0
        pm[~hasp] = np.nan
        Em[~hasp] = np.nan
        out[f"pm{s}"], out[f"Em{s}"] = pm[keep], Em[keep]
    return out, int(keep.sum())


def make_figure(tune, combined_data):
    gst = resolve_gst(tune)
    c, nsel = load(gst)
    gs, gen = RUNS[tune]
    dx, dy, de = combined_data

    stages = {}
    print(f"[{tune}] ({gs}, {gen}) N_sel={nsel:,}  [{Path(gst).name}]")
    for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI leading p")):
        cnt, y = occ_hist_c12(c[f"pm{s}"], c[f"Em{s}"], float(nsel))
        A, dA = asym(cnt)
        Np, Nm = cnt[len(cnt)//2:].sum(), cnt[:len(cnt)//2].sum()
        Ai = (Np - Nm) / max(Np + Nm, 1)
        dAi = np.sqrt((1 - Ai**2) / max(Np + Nm, 1))
        stages[s] = (label, cnt, y, A, dA, Ai, dAi)
        print(f"  stage {s} ({label}): N={int(cnt.sum()):,}  A = {Ai:+.4f} +- {dAi:.4f}")

    scale = stages[4][2].sum() / dy.sum()

    import matplotlib.pyplot as plt
    fig, (ax, axA) = plt.subplots(2, 1, figsize=(8.0, 8.2), sharex=True,
                                  height_ratios=[2.2, 1], layout="constrained")
    ax.stairs(stages[3][2], EDGES, color="C0", linewidth=1.8,
              label="pre-FSI primary p")
    ax.stairs(stages[4][2], EDGES, color="C3", linewidth=1.8,
              label="post-FSI leading p")
    ax.errorbar(dx, dy * scale, yerr=de * scale, fmt="s", ms=4, color="0.5",
                capsize=2, zorder=8,
                label="fig6 top+bot (symm., $E_m$ 10–25$\\cup$30–50, shape)")
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

    fig.suptitle(f"C12 signed $p_m$ — {tune}\n({gs}, {gen}); "
                 f"A(post-FSI) = {stages[4][5]:+.3f}, 4$\\pi$, EMQE hit p "
                 "(local regen)", fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"pmiss_signed_c12_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print("  wrote", out)
    return {s: (stages[s][5], stages[s][6]) for s in (3, 4)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(RUNS))
    ap.add_argument("--all-tunes", action="store_true")
    args = ap.parse_args()

    apply_style()
    # combined fig6 data (p-shell + s-shell; E_m 10-25 u 30-50, gap at 25-30)
    dx, y_p, _, e_p = np.loadtxt(DATA_DIR / "fig6_top_q1p2.dat", unpack=True)
    _, y_s, _, e_s = np.loadtxt(DATA_DIR / "fig6_bot_q1p2.dat", unpack=True)
    combined = (dx, y_p + y_s, np.sqrt(e_p ** 2 + e_s ** 2))

    summary = {}
    for t in (list(RUNS) if args.all_tunes else [args.tune]):
        summary[t] = make_figure(t, combined)
    print("\nintegrated asymmetry summary:")
    for t, s in summary.items():
        print(f"  {t}: pre-FSI {s[3][0]:+.4f}+-{s[3][1]:.4f}  "
              f"post-FSI {s[4][0]:+.4f}+-{s[4][1]:.4f}")

"""Fe56 four-stage E_miss ladder on the restored (input-table) axis vs Dutta Fig. 11.

Plot 3 of the electron-Fe56 series: replicate the C12 restored ladder
(results/prd-analyzer-v0/plot_em_ladder_restored.py + build_cache_ladder.py,
v0 README section 12) for GEM26_22a_05_000 on Fe56 at Q^2 = 1.28 (GeV/c)^2,
beam 2.445 GeV -- the kinematics of the digitized Fe56 missing-energy spectral
function (paper Fig. 11, data/Dipingkar-dutta-data-prc_figs/fig11_q1p2.dat).

Stages, identical formulas to the C12 ladder with the Fe56 constants
(remnant = Mn55 for proton knockout; Z = 26):
  1  input table f_{k<300}(E)  from pke56_tot.data (proton-occupancy scale)
  2  struck nucleon (record), restored  E2 + T_rec(p_n)  = m_N - E_n
  3  pre-FSI primary proton,  restored  E3 + T_rec(p_m)  = omega - T_p
  4  post-FSI leading proton, restored  E4 + T_rec(p_m)  = omega - T_p
Selection: qel && hitnuc==2212, no other cuts (the C12 samples were EMQE so the
qel cut was implicit there; the Fe56 campaign samples are full-EM). p_s < 300
MeV/c window per stage; occupancy normalization y = Z*hist/(N_sel*5 MeV).

Expected physics (agreed reading): 22a is Rosenbluth QE through the classic
FermiMover chain, so the record drops the sampled removal energy -- panel 2 is
a near-delta at S_p ~ 10.2 MeV (the a-tune finding of the C12 study), NOT the
sampled table. Panel 1 shows what was actually sampled.

Data caveats (same as C12): the published Dutta E_m is recoil-SUBTRACTED, so on
this axis the data sit low by an event-wise T_rec <= ~4.5 MeV (sub-bin at 5-MeV
binning) -- shape reference only. The fig11 absolute scale is renormalized to
the in-window IPSM strength (integral 18.20 +- 0.08, not Z=26); errors in the
file are statistical only (inflated here by 2% pt-to-pt (+) 5% model like the
C12 loader; no pixel-measured overrides exist for Fe).

Usage:
  export BEARER_TOKEN_FILE=/tmp/bt_u$(id -u)
  pixi run python results/template/make_emiss_ladder_fe56.py [--max-files 20]
Cache: results/prd-analyzer-v0.1/cache/ladder_fe56/GEM26_22a_05_000.npz
(delete to re-stream).
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TUNE = "GEM26_22a_05_000"
GRIDLOG = REPO / ("jobsub-agent/jobsub-runs/gevgen_grid-2026-07-16/"
                  "eminus_Fe56_20260716-141800.gridlog")
DATA = REPO / "data/Dipingkar-dutta-data-prc_figs/fig11_q1p2.dat"
CACHE = REPO / "results/prd-analyzer-v0.1/cache/ladder_fe56" / f"{TUNE}.npz"
OUT = REPO / "results/prd-analyzer-v0.1" / f"em_ladder_restored_fe56_{TUNE}.png"

Z = 26                                # Fe protons (occupancy scale)
TGT_PDG = 1000260560
# nuclear masses [GeV] from the install's genie_pdg_table.txt (same provenance
# as the Fe56 mass used in make_sf2d_events.py): Mn55 = proton-knockout remnant
M_REC = 51.1616880                    # Mn55, genie_pdg_table.txt pdg 1000250550
M_MEV = M_REC * 1000.0
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

PM_MAX = 300.0                        # |p_m| window [MeV/c] (paper)
BINW = 5.0
EDGES = np.arange(0.0, 85.0, 5.0)     # 16 data bins [0,80)


# ---- stage 1: input table (proton-occupancy scale) --------------------------------
def load_table():
    """pke56_tot.data -> (k, E, P_per_proton, dk, dE); prints the raw norm."""
    path = resolve_sf_table(TUNE, TGT_PDG, 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)   # S raw [MeV^-4], (n_k, n_E)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    # normalize so the FULL-window proton occupancy is Z (GENIE itself only uses
    # the shape; the raw integral tells us the file's own normalization)
    P = S * (Z / raw) / Z             # per-proton density: full integral = 1
    print(f"input table {path.name}: raw 4pi k^2 integral = {raw:.3f} "
          f"(file normalization); rescaled to proton occupancy Z={Z}")
    return k, E, P, dk, dE


def f_restricted(k, P, dk, kmax=PM_MAX):
    """Z * int_{k<kmax} 4pi k^2 P dk -> occupancy-scale f(E) [MeV^-1]."""
    sel = (k + dk / 2.0) <= kmax + 1e-9
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def rebin(E, f, dE, edges):
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (E >= lo) & (E < hi)
        out[i] = (f[m] * dE[m]).sum() / (hi - lo)
    return out


# ---- Dutta fig11 -------------------------------------------------------------------
def load_dutta():
    dem, dsf, _, dstat = np.loadtxt(DATA, unpack=True)
    dtot = np.sqrt(dstat ** 2 + (0.02 * dsf) ** 2 + (0.05 * dsf) ** 2)
    return dem, dsf, dstat, dtot


# ---- cache builder (stages 2-4, formulas = build_cache_ladder.py:64-87) -----------
BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel",
            "En", "pxn", "pyn", "pzn",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def xrootd_url(p, door="fndca1.fnal.gov:1094"):
    return f"root://{door}/" + p.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def build_cache(max_files):
    import uproot
    import awkward as ak
    pnfs_dir = json.load(open(GRIDLOG))["pnfs_output_dir"]
    paths = sorted(glob.glob(pnfs_dir + "/*/*.gst.root"))[:max_files]
    print(f"[{TUNE}] streaming {len(paths)} gst file(s) (qel && hitnuc==p)")
    parts, ntot, nsel = [], 0, 0
    for ipath, p in enumerate(paths):
        a = uproot.open(xrootd_url(p))["gst"].arrays(BRANCHES, library="ak")
        keep = ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
        nz = lambda b: ak.to_numpy(a[b])
        omega = nz("Ev") - nz("El")
        qx = nz("pxv") - nz("pxl")
        qy = nz("pyv") - nz("pyl")
        qz = nz("pzv") - nz("pzl")

        En = nz("En")
        pn = np.sqrt(nz("pxn") ** 2 + nz("pyn") ** 2 + nz("pzn") ** 2)
        E2 = (M_P - En - pn ** 2 / (2.0 * M_REC)) * 1000.0
        p2 = pn * 1000.0

        isp = (a.pdgi == 2212)
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        Ep, pxp, pyp, pzp = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        p3 = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)
        E3 = (omega - (Ep - M_P) - p3 ** 2 / (2.0 * M_REC)) * 1000.0

        isf = (a.pdgf == 2212)
        leadf = ak.argmax(ak.where(isf, a.pf, -1.0), axis=1, keepdims=True)
        gf = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[leadf]), np.nan))
        Efp, pxf, pyf, pzf = gf(a.Ef), gf(a.pxf), gf(a.pyf), gf(a.pzf)
        p4 = np.sqrt((pxf - qx) ** 2 + (pyf - qy) ** 2 + (pzf - qz) ** 2)
        E4 = (omega - (Efp - M_P) - p4 ** 2 / (2.0 * M_REC)) * 1000.0

        parts.append(dict(E2=E2[keep], p2=p2[keep],
                          E3=E3[keep], p3=p3[keep] * 1000.0,
                          E4=E4[keep], p4=p4[keep] * 1000.0))
        ntot += len(keep)
        nsel += int(keep.sum())
        print(f"  ... file {ipath + 1}/{len(paths)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    surv = float(np.mean(np.isfinite(out["E4"])))
    print(f"[{TUNE}] ntot={ntot}  qel&&hitp={nsel} ({100.0 * nsel / ntot:.1f}%)"
          f"  post-FSI-p survival {100.0 * surv:.1f}%  -> {CACHE}")


def occ_hist(E, p, n_sel):
    win = p < PM_MAX
    cnt, _ = np.histogram(E[win], bins=EDGES)
    return Z * cnt / (n_sel * BINW)


# ---- main ---------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=20)
    args = ap.parse_args()

    if not CACHE.exists():
        build_cache(args.max_files)
    c = dict(np.load(CACHE))
    n_sel = float(c["n_sel"][0])
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):          # restored axis: E_s + p_s^2/(2 M_Mn55)
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * M_MEV)

    k, E, P, dk, dE = load_table()
    y_in = rebin(E, f_restricted(k, P, dk), dE, EDGES)
    dem, dsf, dstat, dtot = load_dutta()

    h = {s: occ_hist(c[f"E{s}r"], c[f"p{s}"], n_sel) for s in (2, 3, 4)}
    print("restored ladder bookkeeping (E<80, p_s<300; occupancy units):")
    print(f"  I1(table,k<300)={y_in.sum() * BINW:.3f}  "
          + "  ".join(f"I{s}r={h[s].sum() * BINW:.3f}" for s in (2, 3, 4))
          + f"  I4r/I3r={h[4].sum() / max(h[3].sum(), 1e-12):.3f}")
    print(f"  data integral {np.sum(dsf) * BINW:.3f} (published fig11 scale, "
          "in-window IPSM strength; recoil-subtracted axis)")
    w2 = c["p2"] < PM_MAX
    print(f"  stage-2 record: median {np.median(c['E2r'][w2]):.2f} MeV, "
          f"p5-p95 [{np.percentile(c['E2r'][w2], 5):.2f}, "
          f"{np.percentile(c['E2r'][w2], 95):.2f}] MeV (S_p delta check)")

    apply_style()
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    TITLES = ["1 — input table  $f_{k<300}(E)$",
              "2 — struck nucleon (record),  $m_N-E_n$",
              "3 — pre-FSI primary proton,  $\\omega-T_p$",
              "4 — post-FSI leading proton,  $\\omega-T_p$"]

    def draw_data(ax, with_label=False):
        ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                    zorder=9,
                    label="Dutta Fig. 11 (publ. scale)" if with_label else None)

    ax = axes[0]
    ax.stairs(y_in, EDGES, color="C1", linewidth=2.0, zorder=4,
              label="Benhar SF pke56_tot (22a input)")
    draw_data(ax, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="table axis = restored axis",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        ax.stairs(y_in, EDGES, color="C1", linewidth=1.0, linestyle="--",
                  alpha=0.8, zorder=2)
        ax.stairs(h[s], EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=TUNE if i == 3 else None)
        draw_data(ax)
    pk = max(h[2].max(), h[3].max())
    axes[1].annotate("a-tune record: FermiMover drops the\nsampled $w$ — "
                     "$\\delta$ at $S_p\\approx10.2$ MeV\n(off scale: "
                     f"[10,15) bin = {pk:.1f}), not the\ndashed table",
                     xy=(0.30, 0.52), xycoords="axes fraction",
                     fontsize=FS_LEGEND - 3, color="0.35")
    axes[2].annotate("$\\equiv$ stage 2 (energy-conserving\nchain: "
                     "$\\omega-T_p = m_N-E_n$)",
                     xy=(0.35, 0.60), xycoords="axes fraction",
                     fontsize=FS_LEGEND - 3, color="0.35")
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title="thin dashed: input table\n(data axis: $-T_{rec}$, sub-bin)",
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$E_m+T_{rec}$  (MeV)" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 85)
        ax.set_ylim(0, 1.5)          # C12 convention: fixed range, delta clips
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$(E_m+T_{rec})\,/\,N_{sel}$   (MeV$^{-1}$)",
                          fontsize=FS_LABEL)

    fig.suptitle("Fe56 restored E$_m$ ladder — " + TUNE +
                 "\nqel && hit p, $p_m<300$ MeV/$c$; Dutta Fig. 11 at publ. scale",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    fig.savefig(OUT, dpi=DPI)
    print("wrote", OUT)

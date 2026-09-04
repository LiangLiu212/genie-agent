"""v0.2 four-stage E_miss ladder (restored axis) with the Dutta Q^2 cut, per target.

The prd-analyzer-v0.2 counterpart of make_emiss_ladder_fe56.py /
make_emiss_ladder_c12.py: the same four-stage restored-axis construction
(stage 1 input table, 2 struck-nucleon record m_N - E_n, 3 pre-FSI primary
proton omega - T_p, 4 post-FSI leading proton omega - T_p; every event stage
on E + T_rec with the target remnant), with the selection

    qel && hitnuc==2212 && |Q^2/1.28 - 1| <= 5 %

on the full-EM t05 campaign samples for BOTH targets (Fe56 grid 2026-07-16,
C12 grid 2026-07-26, 20 gst files = 2M events/tune, streamed over XRootD via
pnfs_ls — NFS-free). This retires v0.1's C12 provenance split (purged June
EMQE caches): both targets stream the same way, with the explicit `qel`
replacing the EMQE-implicit selection.

Occupancy normalization Z*hist(p_s<300)/(N_sel*5 MeV) with N_sel = the
windowed selection count. Dutta fig at its published scale (fig11 for Fe56
with the 2% pt-to-pt (+) 5% model inflation; fig9 for C12 via
fig9_common.load_dutta incl. the pixel-measured p-shell bars) — the data IS
the Q^2 = 1.28 setting, so the window brings MC phase space closer to it.

Cache: results/prd-analyzer-v0.2/cache/ladder_<target>/<tune>.npz
(E2/p2/E3/p3/E4/p4 [MeV, MeV/c] + ntot/n_sel; same fields as the v0.1 Fe56
caches, consumed by make_pmiss_q2cut.py). Delete to re-stream.
Figures: results/prd-analyzer-v0.2/em_ladder_restored_<target>_<tune>.png.

Usage:
  pixi run python results/template/make_emiss_ladder_q2cut.py --target Fe56 --all-tunes
  pixi run python results/template/make_emiss_ladder_q2cut.py --target C12 --all-tunes
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
from make_sf2d_table import resolve_sf_table, read_pke_table  # noqa: E402
from pnfs_ls import gst_urls, xrootd_url                      # noqa: E402

REPO = Path(__file__).resolve().parents[2]
GRIDLOG_ROOT = REPO / "jobsub-agent/jobsub-runs"
CACHE_ROOT = REPO / "results/prd-analyzer-v0.2/cache"
OUT_DIR = REPO / "results/prd-analyzer-v0.2"

Q2_CENTER, Q2_FRAC = 1.28, 0.05
PROTON_SEL = "leading"          # or "1p": stage 4 requires exactly one FS proton
NO_Q2CUT = False                # True (v1.0): drop the Q^2 window entirely
SEL_TAG = ""                    # "_leading" for the uncut leading-p variant
                                # (cache dir + figure-stem tag, v1.0 only)
PM_MAX = 300.0
BINW = 5.0
EDGES = np.arange(0.0, 85.0, 5.0)

# proton mass from the repo-shared PDG table (same provenance as v0.1)
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

# tune -> (has 2D SF table, ground-state label stem)
TUNE_GS = {
    "GEM26_11a_05_000": (False, "LocalFGM"),
    "GEM26_22a_05_000": (True,  "SpectralFunc"),
    "GEM26_22b_05_000": (True,  "SpectralFunc"),
    "GEM21_11a_05_000": (False, "LocalFGM"),
    # INCL++ ground state + INCL++ cascade FSI; local C12 sample only
    # (TGT["C12"]["local_gst"]), no grid campaign
    "GEM26_44b_05_000": (False, "INCL++ GS+FSI"),
    # the same tune on the new vertex (fork branch feature/incl-vertex-local-energy,
    # 200k local events each, 2026-09-04): one bound struck nucleon everywhere,
    # local energy on (LFG-like momentum) / never (INCL ball with floor)
    "GEM26_44b_05_000_locEon":    (False, "INCL++ new vertex, local energy ON"),
    "GEM26_44b_05_000_locEnever": (False, "INCL++ new vertex, never"),
    # the INCL-scheme vertex (convention of 2026-09-04: scattering in INCL's local
    # frame, balance E - V without a local-energy term, record = global nucleon
    # (p_ball, E_ball - V0)); 200k local events each on their own spline
    "GEM26_44b_05_000_lfon":    (False, "INCL-scheme vertex, locE ON"),
    "GEM26_44b_05_000_lfnever": (False, "INCL-scheme vertex, never"),
}


def _m_rec_c12():
    from acceptance import M_REC       # B11 [GeV], v0 value (matches v0 caches)
    return M_REC


def _dutta_fe56():
    dem, dsf, _, dstat = np.loadtxt(
        REPO / "data/Dipingkar-dutta-data-prc_figs/fig11_q1p2.dat", unpack=True)
    dtot = np.sqrt(dstat ** 2 + (0.02 * dsf) ** 2 + (0.05 * dsf) ** 2)
    return dem, dsf, dstat, dtot


def _dutta_c12():
    from fig9_common import load_dutta
    return load_dutta()


# per-target configuration
TGT = {
    "Fe56": dict(
        Z=26, tgt_pdg=1000260560,
        m_rec_gev=51.1616880,          # Mn55, install genie_pdg_table.txt (v0.1)
        run_dir="gevgen_grid-2026-07-16",
        stems={"GEM26_11a_05_000": "eminus_Fe56_20260716-113802",
               "GEM26_22a_05_000": "eminus_Fe56_20260716-141800",
               "GEM26_22b_05_000": "eminus_Fe56_20260716-141807",
               "GEM21_11a_05_000": "eminus_Fe56_20260716-113817"},
        dutta=_dutta_fe56, data_label="Dutta Fig. 11 (publ. scale)",
        ymax=1.5, sp_note=r"$S_p\approx10.2$ MeV",
        gem21_note=("SuSA record: $m_N-E_n=-T_N<0$,\noff scale left "
                    "(median {med:.1f} MeV).\nFe56 EM SuSAv2 = scaled-C12 surrogate"),
    ),
    "C12": dict(
        Z=6, tgt_pdg=1000060120,
        m_rec_gev=None,                # filled from acceptance.M_REC (B11)
        run_dir="gevgen_grid-2026-07-26",
        stems={"GEM26_11a_05_000": "eminus_C12_20260726-105638",
               "GEM26_22a_05_000": "eminus_C12_20260726-105642",
               "GEM26_22b_05_000": "eminus_C12_20260726-105646",
               "GEM21_11a_05_000": "eminus_C12_20260726-105650"},
        dutta=_dutta_c12, data_label="Dutta Fig. 9 (publ. scale)",
        ymax=1.0, sp_note=r"$S_p\approx16$ MeV",
        gem21_note=("SuSA record: $m_N-E_n=-T_N<0$,\noff scale left "
                    "(median {med:.1f} MeV)"),
        # tunes with no campaign: local gst chunks (repo-relative glob);
        # GEM26_44b_05_000 = 4x125k EMQE-only, 2026-09-01, install cc9c9b417
        local_gst={"GEM26_44b_05_000": "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-01/eminus_C12_20260901-*.gst.root",
                   # explicit chunk lists: both settings share the tune id and the run dir
                   "GEM26_44b_05_000_locEon": ["genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135725-84c.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135727-8b5.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135727-a11.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135728-d90.gst.root"],
                   "GEM26_44b_05_000_lfon": ["genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-170929-740.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-170930-58d.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-170930-0b5.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-170931-b2b.gst.root"],
                   "GEM26_44b_05_000_lfnever": ["genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-171310-ad8.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-171310-15a.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-171310-6f2.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-171310-ff5.gst.root"],
                   "GEM26_44b_05_000_locEnever": ["genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135728-089.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-135728-a87.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-143137-3cd.gst.root", "genie-agent/genie-runs/GEM26_44b_05_000-2026-09-04/eminus_C12_20260904-143137-546.gst.root"]},
        incl_note=("INCL record: $E=v_{{loc}}-T_i$, no $S_p$ floor\n"
                   "— mostly $<0$, off scale left\n(median {med:.1f} MeV)"),
        incl_lf_note=("INCL-scheme vertex: record = INCL ball nucleon,\n"
                      "$m_N-E_n = V_0 - T_{{ball}}$ (median {med:.1f} MeV)"),
        incl_new_note=("new vertex: record = interaction nucleon,\n"
                       "$m_N-E_n = V_0 - T$ (median {med:.1f} MeV)"),
    ),
}

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
            "hitnuc", "qel", "Q2",
            "En", "pxn", "pyn", "pzn",
            "pdgi", "Ei", "pxi", "pyi", "pzi",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def load_table(target, tune):
    cfg = TGT[target]
    path = resolve_sf_table(tune, cfg["tgt_pdg"], 2212)
    k, E, k_edges, E_edges, S = read_pke_table(path)
    dk = float(np.diff(k_edges).mean())
    dE = float(np.diff(E_edges).mean())
    raw = float((4.0 * np.pi * (k[:, None] ** 2) * S * dk * dE).sum())
    P = S * (cfg["Z"] / raw) / cfg["Z"]
    print(f"input table {path.name}: raw 4pi k^2 integral = {raw:.3f}; "
          f"rescaled to proton occupancy Z={cfg['Z']}")
    return path.stem, (k, E, P, dk, dE)


def f_restricted(k, P, dk, Z, kmax=PM_MAX):
    sel = (k + dk / 2.0) <= kmax + 1e-9
    w = 4.0 * np.pi * (k[sel, None] ** 2) * P[sel, :]
    return Z * (w * dk).sum(axis=0)


def rebin(E, f, dE, edges):
    """Spread each table column uniformly over its native bin (half-bin lesson)."""
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    out = np.zeros(len(edges) - 1)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        ov = np.clip(np.minimum(E + dE / 2.0, hi) - np.maximum(E - dE / 2.0, lo),
                     0.0, None)
        out[i] = (f * ov).sum() / (hi - lo)
    return out


def build_cache(target, tune, max_files):
    import uproot
    import awkward as ak
    cfg = TGT[target]
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else _m_rec_c12()
    cache_dir = CACHE_ROOT / f"ladder_{target.lower()}{SEL_TAG}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if tune in cfg["stems"]:
        gridlog = GRIDLOG_ROOT / cfg["run_dir"] / f"{cfg['stems'][tune]}.gridlog"
        urls, verb = gst_urls(gridlog, max_files), "streaming"
    else:                                   # local sample (cfg["local_gst"])
        import glob
        pats = cfg["local_gst"][tune]
        pats = [pats] if isinstance(pats, str) else pats
        urls = sorted(u for pat in pats for u in glob.glob(str(REPO / pat)))
        verb = "reading local"
        if not urls:
            raise SystemExit(f"no local gst files for {tune}: "
                             f"{REPO / cfg['local_gst'][tune]}")
    print(f"[{tune}] {verb} {len(urls)} gst file(s) "
          f"(qel && hitnuc==p"
          + ("" if NO_Q2CUT else " && |Q2/1.28-1|<=5%") + ")")
    parts, ntot, nsel = [], 0, 0
    for ipath, url in enumerate(urls):
        a = uproot.open(url)["gst"].arrays(BRANCHES, library="ak")
        keep = ak.to_numpy(a.hitnuc == 2212) & ak.to_numpy(a.qel)
        if not NO_Q2CUT:
            keep &= np.abs(ak.to_numpy(a.Q2) / Q2_CENTER - 1.0) <= Q2_FRAC
        nz = lambda b: ak.to_numpy(a[b])
        omega = nz("Ev") - nz("El")
        qx = nz("pxv") - nz("pxl")
        qy = nz("pyv") - nz("pyl")
        qz = nz("pzv") - nz("pzl")

        En = nz("En")
        pn = np.sqrt(nz("pxn") ** 2 + nz("pyn") ** 2 + nz("pzn") ** 2)
        E2 = (M_P - En - pn ** 2 / (2.0 * m_rec)) * 1000.0
        p2 = pn * 1000.0

        # NB guard against no-proton events: ak.argmax(where(is_p, x, -1))
        # returns index 0 (NOT None) when an event has no proton at all, so
        # without the has-mask a neutron/photon silently poses as the proton
        # (the unguarded v0.1 builders have this defect, ~4% on Fe56).
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
        has4 = (ak.to_numpy(ak.sum(isf, axis=1)) == 1) if PROTON_SEL == "1p" \
               else ak.to_numpy(ak.any(isf, axis=1))
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
        print(f"  ... file {ipath + 1}/{len(urls)}: {ntot:,} events, "
              f"{nsel:,} selected", flush=True)
    out = {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}
    out["ntot"], out["n_sel"] = np.array([ntot]), np.array([nsel])
    np.savez_compressed(cache_dir / f"{tune}.npz", **out)
    surv = float(np.mean(np.isfinite(out["E4"])))
    sel_lab = "qel&&hitp" if NO_Q2CUT else "qel&&hitp&&win"
    print(f"[{tune}] ntot={ntot}  {sel_lab}={nsel} "
          f"({100.0 * nsel / ntot:.2f}%)  post-FSI-p survival {100.0 * surv:.1f}%")


def occ_hist(E, p, n_sel, Z):
    win = p < PM_MAX
    cnt, _ = np.histogram(E[win], bins=EDGES)
    return Z * cnt / (n_sel * BINW)


def make_figure(target, tune, max_files, dutta, table_stem, table):
    cfg = TGT[target]
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else _m_rec_c12()
    tlow = target.lower()
    cache = CACHE_ROOT / f"ladder_{tlow}{SEL_TAG}" / f"{tune}.npz"
    if not cache.exists():
        build_cache(target, tune, max_files)
    c = dict(np.load(cache))
    n_sel = float(c["n_sel"][0])
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):          # restored axis: E_s + p_s^2/(2 M_rec)
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)

    has_table = TUNE_GS[tune][0]
    y_in = None
    if has_table:
        k, E, P, dk, dE = table
        y_in = rebin(E, f_restricted(k, P, dk, cfg["Z"]), dE, EDGES)
    dem, dsf, dstat, dtot = dutta

    h = {s: occ_hist(c[f"E{s}r"], c[f"p{s}"], n_sel, cfg["Z"]) for s in (2, 3, 4)}
    w2 = c["p2"] < PM_MAX
    print(f"[{tune}] windowed restored ladder (E<80, p_s<300; occupancy):")
    if y_in is not None:
        print(f"  I1(table,k<300)={y_in.sum() * BINW:.3f}", end="  ")
    print("  ".join(f"I{s}r={h[s].sum() * BINW:.3f}" for s in (2, 3, 4))
          + f"  I4r/I3r={h[4].sum() / max(h[3].sum(), 1e-12):.3f}")
    print(f"  stage-2 record: median {np.median(c['E2r'][w2]):.2f} MeV, "
          f"p5-p95 [{np.percentile(c['E2r'][w2], 5):.2f}, "
          f"{np.percentile(c['E2r'][w2], 95):.2f}] MeV")

    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    TITLES = ["1 — input table  $f_{k<300}(E)$",
              "2 — struck nucleon (record),  $m_N-E_n$",
              "3 — pre-FSI primary proton,  $\\omega-T_p$",
              "4 — post-FSI leading proton,  $\\omega-T_p$"]

    def draw_data(ax, with_label=False):
        ax.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
                    alpha=0.8, zorder=8)
        ax.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=4, color="black", capsize=2,
                    zorder=9, label=cfg["data_label"] if with_label else None)

    ax = axes[0]
    if y_in is not None:
        ax.stairs(y_in, EDGES, color="C1", linewidth=2.0, zorder=4,
                  label=f"Benhar SF {table_stem} (input)")
    else:
        ax.annotate(f"{TUNE_GS[tune][1]}:\nno 2D SF input table",
                    xy=(0.40, 0.55), xycoords="axes fraction",
                    fontsize=FS_LEGEND - 2, color="0.35")
    draw_data(ax, with_label=True)
    ax.legend(fontsize=FS_LEGEND - 3, title="table axis = restored axis",
              title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, s in zip((1, 2, 3), (2, 3, 4)):
        ax = axes[i]
        if y_in is not None:
            ax.stairs(y_in, EDGES, color="C1", linewidth=1.0, linestyle="--",
                      alpha=0.8, zorder=2)
        ax.stairs(h[s], EDGES, color="C0", linewidth=1.8, zorder=5,
                  label=tune if i == 3 else None)
        draw_data(ax)

    med2 = float(np.median(c["E2r"][w2]))
    pk = max(h[2].max(), h[3].max())
    if tune == "GEM26_22b_05_000":
        note = ("b-tune record: QELEventGenerator keeps\nthe sampled $w$ — "
                "$m_N-E_n=E_{sampled}$\n(restoration)")
    elif tune == "GEM21_11a_05_000":
        note = cfg["gem21_note"].format(med=med2)
    elif tune == "GEM26_44b_05_000":
        note = cfg["incl_note"].format(med=med2)
    elif tune.startswith("GEM26_44b_05_000_lf"):
        note = cfg["incl_lf_note"].format(med=med2)
    elif tune.startswith("GEM26_44b_05_000_locE"):
        note = cfg["incl_new_note"].format(med=med2)
    else:
        note = ("record: FermiMover drops the sampled $w$\n— $\\delta$ at "
                + cfg["sp_note"] + f" (off scale:\npeak bin = {pk:.1f})")
    axes[1].annotate(note, xy=(0.28, 0.55), xycoords="axes fraction",
                     fontsize=FS_LEGEND - 3, color="0.35")
    axes[3].legend(fontsize=FS_LEGEND - 3,
                   title=("thin dashed: input table\n(data axis: $-T_{rec}$, sub-bin)"
                          if y_in is not None else
                          "(data axis: $-T_{rec}$, sub-bin)"),
                   title_fontsize=FS_LEGEND_TITLE - 3, loc="upper right")

    for i, ax in enumerate(axes):
        style_axis(ax, title=TITLES[i],
                   xlabel=r"$E_m+T_{rec}$  (MeV)" if i >= 2 else None,
                   logx=False, logy=False, ymin=None)
        ax.set_xlim(0, 85)
        ax.set_ylim(0, cfg["ymax"])
        if i % 2 == 0:
            ax.set_ylabel(r"$Z\cdot$ d$N/$d$(E_m+T_{rec})\,/\,N_{sel}$   (MeV$^{-1}$)",
                          fontsize=FS_LABEL)

    fig.suptitle(f"{target} restored E$_m$ ladder — {tune}  "
                 f"({TUNE_GS[tune][1]})\n"
                 "qel && hit p"
                 + ("" if NO_Q2CUT else " && $Q^2=1.28\\pm5\\%$")
                 + (" && N$_p$=1" if PROTON_SEL == "1p" else "")
                 + (", NO $Q^2$ cut" if NO_Q2CUT else "")
                 + ", $p_m<300$ MeV/$c$; " + cfg["data_label"],
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    out = OUT_DIR / f"em_ladder_restored{SEL_TAG}_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    print("wrote", out)

    make_shape_figure(target, tune, c, dutta)


def make_shape_figure(target, tune, c, dutta):
    """Per-tune SHAPE comparison: the post-FSI in-window distribution
    normalized by its own in-window event count (unit integral over
    [0, 80) MeV), against the data and the pre-FSI shape normalized the same
    way — the FSI shape distortion with the ~Z x survival scale divided out."""
    import matplotlib.pyplot as plt
    cfg = TGT[target]
    tlow = target.lower()
    dem, dsf, dstat, dtot = dutta

    n_win, y = {}, {}
    for s in (3, 4):
        Er, p = c[f"E{s}r"], c[f"p{s}"]
        win = np.isfinite(Er) & (p < PM_MAX) & (Er >= EDGES[0]) & (Er < EDGES[-1])
        cnt, _ = np.histogram(Er[win], bins=EDGES)
        n_win[s] = int(cnt.sum())
        y[s] = cnt / (n_win[s] * BINW)          # unit integral over the window
    dnorm = 1.0 / (dsf.sum() * BINW)            # data to unit integral too
    print(f"  shape fig: N_in-win pre-FSI={n_win[3]:,}  post-FSI={n_win[4]:,}")

    fig, ax = plt.subplots(figsize=(8.0, 5.8), layout="constrained")
    ax.stairs(y[3], EDGES, color="C0", linewidth=1.6, linestyle="--", zorder=4,
              label=f"pre-FSI shape (N={n_win[3]:,})")
    ax.stairs(y[4], EDGES, color="C3", linewidth=2.0, zorder=5,
              label=f"post-FSI shape (N={n_win[4]:,})")
    ax.errorbar(dem, dsf * dnorm, yerr=dtot * dnorm, fmt="none", ecolor="0.6",
                elinewidth=3, alpha=0.8, zorder=8)
    ax.errorbar(dem, dsf * dnorm, yerr=dstat * dnorm, fmt="s", ms=4,
                color="black", capsize=2, zorder=9,
                label=cfg["data_label"].replace("publ. scale",
                                                "unit-normalized"))
    style_axis(ax, title=None, xlabel=r"$E_m+T_{rec}$  (MeV)",
               logx=False, logy=False, ymin=None)
    ax.set_xlim(0, 85)
    ax.set_ylim(0, None)
    ax.set_ylabel(r"d$N/$d$(E_m+T_{rec})\,/\,N_{\rm in-win}$   (MeV$^{-1}$)",
                  fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right",
              title="each curve: unit integral over [0, 80)",
              title_fontsize=FS_LEGEND_TITLE - 3)
    fig.suptitle(f"{target} post-FSI E$_m$ shape — {tune}  "
                 f"({TUNE_GS[tune][1]})\n"
                 "qel && hit p"
                 + (", NO $Q^2$ cut" if NO_Q2CUT else " && $Q^2$ slice")
                 + "; unit-normalized shapes",
                 fontsize=FS_SUPTITLE - 3)
    out = OUT_DIR / f"em_postfsi_shape{SEL_TAG}_{tlow}_{tune}.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print("  wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Fe56", choices=list(TGT))
    ap.add_argument("--tune", default="GEM26_22a_05_000", choices=sorted(TUNE_GS))
    ap.add_argument("--all-tunes", action="store_true")
    ap.add_argument("--max-files", type=int, default=20)
    ap.add_argument("--proton-sel", default="leading", choices=["leading", "1p"],
                    help="1p: stage 4 = exactly one FS proton, outputs to v0.3")
    ap.add_argument("--no-q2cut", action="store_true",
                    help="drop the Q^2 window (v1.0 construction): reads/"
                         "writes v1.0 cache+figures; --proton-sel leading "
                         "uses the _leading cache dir + figure tag")
    ap.add_argument("--build-only", action="store_true",
                    help="only build missing caches, write no figures")
    args = ap.parse_args()
    PROTON_SEL = args.proton_sel
    NO_Q2CUT = args.no_q2cut
    if PROTON_SEL == "1p":
        CACHE_ROOT = REPO / "results/prd-analyzer-v0.3/cache"
        OUT_DIR = REPO / "results/prd-analyzer-v0.3"
    if NO_Q2CUT:
        CACHE_ROOT = REPO / "results/prd-analyzer-v1.0/cache"
        OUT_DIR = REPO / "results/prd-analyzer-v1.0"
        SEL_TAG = "" if PROTON_SEL == "1p" else "_leading"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    table_stem, table = load_table(args.target, "GEM26_22a_05_000")
    dutta = TGT[args.target]["dutta"]()
    for tune in (sorted(TUNE_GS) if args.all_tunes else [args.tune]):
        if args.build_only:
            cache = (CACHE_ROOT / f"ladder_{args.target.lower()}{SEL_TAG}"
                     / f"{tune}.npz")
            if cache.exists():
                print(f"[{tune}] cache exists: {cache}")
            else:
                build_cache(args.target, tune, args.max_files)
        else:
            make_figure(args.target, tune, args.max_files, dutta,
                        table_stem, table)

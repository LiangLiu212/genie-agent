"""histdiag text readouts for one tune's (e,e'p) figure set (v0.3 layout).

Rebuilds every histogram of the section figures from the caches the
generator scripts read (results/prd-analyzer-v0.1 kinematics cache, the
v0.3 ladder / signed-p_m caches, the v0.2 fsiproton dump) with the same
edges, windows and selections, and writes one `<stem>.txt` next to each
`<stem>.png` (histdiag skill: interpretation on the counts, not the PNG).

Figures covered (stems as written by the generators, C12 shown):
  kin_qel_q2cut_c12[_counts]        describe1d per kinematic panel
  empm_q2cut_c12[_counts|_lin]      describe1d E_m, p_m in the slice
  em_ladder_restored_c12_<tune>     describe1d stages 2-4; stage 3 vs 2;
                                    stage 4 and 3 vs Dutta on the chosen
                                    data convention and occupancy count
  em_postfsi_shape_c12_<tune>       post- vs pre-FSI E_m (shape)
  pm_ladder_c12_<tune>              describe1d stages 2-4 (shell windows);
                                    stage 4 vs 3; stage 4 and 3 vs Dutta
                                    (40 MeV/c data grid)
  pm_ladder_dens_c12_<tune>         pointer to pm_ladder (same counts)
  postfsi_shape_empm_c12_<tune>     post-FSI vs data, both unit-normalized
  fsi_prepost_c12_<tune>            post- vs pre-FSI on the restored axis
                                    and T_p (raw events)
  pmiss_signed_c12_<tune>           + side vs - side, stages 3 and 4

Data enter with their statistical errors (E_m: fig 9 / fig 11 stat column;
|p_m|: fig 6 / fig 7 column 4), MC with sqrt(N) scaled like the occupancy
curve. Figure names per target: FIGS.

Usage (v1.2):
  GENIE_AGENT_INSTALLATION=genie_inclxx pixi run python results/template/make_eep_readouts.py \
      --target C12 --tune GEM26_22b_05_000 --proton-sel 1p --data-conv raw \
      --norm total-qe --out-dir results/prd-analyzer-v1.2
"""
import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "results/template"))
sys.path.insert(0, str(REPO / "results/prd-analyzer-v0"))
import histdiag as hd                                  # noqa: E402
import make_emiss_ladder_q2cut as em                   # noqa: E402
import make_pmiss_ladder_q2cut as pm                   # noqa: E402
import make_pmiss_signed_q2cut as ps                   # noqa: E402
import make_fsi_proton_choice as fp                    # noqa: E402
import make_kin_qel_q2cut as kq                        # noqa: E402
from qe_norm import norm_count                         # noqa: E402

# Dutta figure names per target: (E_m figure, |p_m| figure)
FIGS = {"C12": ("fig 9", "fig 6 p+s"), "Fe56": ("fig 11", "fig 7")}


def header(fh, title, lines):
    fh.write(f"# {title}\n")
    for ln in lines:
        fh.write(f"# {ln}\n")
    fh.write("\n")


def section(fh, title):
    fh.write(f"\n{'=' * 78}\n## {title}\n{'=' * 78}\n")


def restored(c, m_rec):
    with np.errstate(invalid="ignore"):
        for s in (2, 3, 4):
            c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)
    return c


def em_ladder_readouts(out, target, tune, c, n_norm, norm_desc, dutta):
    cfg = em.TGT[target]
    figE, figP = FIGS[target]
    Z = cfg["Z"]
    dem, dsf, dstat, dtot = dutta
    E, B = em.EDGES, em.BINW
    ctr = 0.5 * (E[:-1] + E[1:])
    assert len(dem) == len(ctr) and np.allclose(dem, ctr), "data grid != EDGES"
    f = Z / (n_norm * B)
    cnt = {}
    for s in (2, 3, 4):
        w = (c[f"p{s}"] < em.PM_MAX) & np.isfinite(c[f"E{s}r"])
        cnt[s], _ = np.histogram(c[f"E{s}r"][w], bins=E)
    xname = "E_m+T_rec [MeV]"
    stem = out / f"em_ladder_restored_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"tune {tune}, {target}; selection qel && hit p && Q2 slice && N_p=1; p_s < {em.PM_MAX:.0f} MeV/c",
            f"stages: 2 = record m_N - E_n, 3 = pre-FSI omega - T_p, 4 = post-FSI omega - T_p, restored axis",
            f"occupancy scale Z*cnt/(N*{B:.0f} MeV) with {norm_desc}",
            f"data: Dutta {figE}, convention {em.DATA_CONV} (scale factor {em.DATA_SCALE:g} on S(Em)); "
            f"I(data) = {dsf.sum() * B:.3f}",
            "MC integrals (E<80): " + ", ".join(f"I{s}r = {cnt[s].sum() * f * B:.3f}" for s in (2, 3, 4)),
            "histdiag: raw counts for MC-only reports; scaled values + errors for MC vs data",
        ])
        for s in (2, 3, 4):
            section(fh, f"describe1d stage {s} (raw counts, {int(cnt[s].sum()):,} in window)")
            hd.describe1d(cnt[s], E, name=f"stage {s}", table=True, quiet=True, save=fh)
        section(fh, "compare1d stage 3 (pre-FSI) vs stage 2 (record), raw counts")
        hd.compare1d(cnt[3], cnt[2], E, labels=("stage 3 pre-FSI", "stage 2 record"),
                     xname=xname, quiet=True, save=fh)
        for s in (4, 3):
            section(fh, f"compare1d stage {s} (occupancy scale) vs Dutta {figE} ({em.DATA_CONV}), with errors")
            hd.compare1d(f * cnt[s], dsf, E, e1=f * np.sqrt(cnt[s]), e2=dstat,
                         labels=(f"stage {s} MC", f"Dutta {figE} {em.DATA_CONV}"),
                         xname=xname, quiet=True, save=fh)
    print("wrote", f"{stem}.txt")

    stem = out / f"em_postfsi_shape_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            "post-FSI (stage 4) vs pre-FSI (stage 3) E_m+T_rec, each unit-normalized over [0, 80) in the figure;",
            "compare1d below on the raw counts (its 'shape' quantities scale the reference to the first's integral)",
            f"data comparison: see em_ladder_restored_{target.lower()}_{tune}.txt (stage 4 vs Dutta)",
        ])
        section(fh, "compare1d stage 4 (post-FSI) vs stage 3 (pre-FSI), raw counts")
        hd.compare1d(cnt[4], cnt[3], E, labels=("stage 4 post-FSI", "stage 3 pre-FSI"),
                     xname=xname, quiet=True, save=fh)
        dn = dsf / (dsf.sum() * B)
        section(fh, f"compare1d stage 4 unit-normalized vs Dutta {figE} unit-normalized (errors propagated)")
        n4 = max(cnt[4].sum(), 1)
        hd.compare1d(cnt[4] / (n4 * B), dn, E, e1=np.sqrt(cnt[4]) / (n4 * B),
                     e2=dstat / (dsf.sum() * B),
                     labels=("stage 4 shape", f"Dutta {figE} shape"), xname=xname,
                     quiet=True, save=fh)
    print("wrote", f"{stem}.txt")
    return cnt


def pm_ladder_readouts(out, target, tune, c, n_norm, norm_desc, dutta):
    cfg = pm.TGT[target]
    figE, figP = FIGS[target]
    Z = cfg["Z"]
    dx, dy, de = dutta
    E, B = pm.EDGES, pm.DK
    nb = int(round(pm.PM_SUM / B))            # bins up to 320 MeV/c
    E320 = E[:nb + 1]
    f = Z / (n_norm * B)
    cnt, cnt_all = {}, None
    for s in (2, 3, 4):
        win = pm.in_windows(c[f"E{s}r"], cfg["e_windows"]) & np.isfinite(c[f"p{s}"])
        cnt[s], _ = np.histogram(c[f"p{s}"][win], bins=E)
    w2 = np.isfinite(c["p2"])
    cnt_all, _ = np.histogram(c["p2"][w2], bins=E)
    # data on the 40 MeV/c grid, occupancy axis
    wgt = 4.0 * np.pi * dx ** 2
    edges40 = np.arange(0.0, pm.PM_SUM + 1.0, 40.0)
    ctr40 = 0.5 * (edges40[:-1] + edges40[1:])
    assert len(dx) == len(ctr40) and np.allclose(dx, ctr40), "data grid != 40 MeV/c"
    xname = "|p_m| [MeV/c]"
    stem = out / f"pm_ladder_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"tune {tune}, {target}; selection qel && hit p && Q2 slice && N_p=1; E window {cfg['win_label']}",
            "stages: 2 = record |p_n|, 3 = pre-FSI |p_p - q|, 4 = post-FSI |p_p - q|; native 20 MeV/c bins",
            f"occupancy scale Z*cnt/(N*{B:.0f} MeV/c) with {norm_desc}",
            f"data: Dutta {figP}, convention {pm.DATA_CONV} (fold factor {pm.DATA_FOLD:g}), "
            f"weighted 4 pi p^2 onto the occupancy axis; I(data, <320) = {(dy * dx ** 2).sum() * 4 * np.pi * 40:.3f}",
            "MC integrals (<320): " + ", ".join(f"I{s} = {cnt[s][:nb].sum() * f * B:.3f}" for s in (2, 3, 4)),
        ])
        section(fh, f"describe1d stage 2 record WITHOUT the E window (raw counts, {int(cnt_all.sum()):,})")
        hd.describe1d(cnt_all, E, name="stage 2 unwindowed", table=False, quiet=True, save=fh)
        for s in (2, 3, 4):
            section(fh, f"describe1d stage {s} in the E window (raw counts, {int(cnt[s].sum()):,})")
            hd.describe1d(cnt[s], E, name=f"stage {s}", table=True, quiet=True, save=fh)
        section(fh, "compare1d stage 4 (post-FSI) vs stage 3 (pre-FSI), raw counts, |p_m| < 320")
        hd.compare1d(cnt[4][:nb], cnt[3][:nb], E320, labels=("stage 4 post-FSI", "stage 3 pre-FSI"),
                     xname=xname, quiet=True, save=fh)
        for s in (4, 3):
            c40, _, _ = hd.rebin1d(cnt[s][:nb], E320, 2)
            f40 = Z / (n_norm * 40.0)
            section(fh, f"compare1d stage {s} (occupancy, 40 MeV/c) vs Dutta {figP} ({pm.DATA_CONV}), with errors")
            hd.compare1d(f40 * c40, wgt * dy, edges40, e1=f40 * np.sqrt(c40), e2=wgt * de,
                         labels=(f"stage {s} MC", f"Dutta {figP} {pm.DATA_CONV}"),
                         xname=xname, quiet=True, save=fh)
    print("wrote", f"{stem}.txt")

    stem = out / f"pm_ladder_dens_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"same counts as pm_ladder_{target.lower()}_{tune}.txt: the density figure divides every MC",
            "stage by 4 pi p_c^2 (bin centres) and draws the data as tabulated; no separate histogram.",
        ])
    print("wrote", f"{stem}.txt")

    stem = out / f"postfsi_shape_empm_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"right panel: post-FSI |p_m| (E window, < 320) unit-normalized vs Dutta {figP} unit-normalized;",
            f"left panel: see em_postfsi_shape_{target.lower()}_{tune}.txt (same E_m construction)",
        ])
        c40, _, _ = hd.rebin1d(cnt[4][:nb], E320, 2)
        n4 = max(c40.sum(), 1)
        dsum = (wgt * dy).sum() * 40.0
        section(fh, f"compare1d stage 4 |p_m| shape (40 MeV/c) vs Dutta {figP} shape, both unit integral over [0, 320)")
        hd.compare1d(c40 / (n4 * 40.0), wgt * dy / dsum, edges40,
                     e1=np.sqrt(c40) / (n4 * 40.0), e2=wgt * de / dsum,
                     labels=("stage 4 shape", f"Dutta {figP} shape"), xname=xname,
                     quiet=True, save=fh)
        c40_3, _, _ = hd.rebin1d(cnt[3][:nb], E320, 2)
        section(fh, "compare1d stage 4 vs stage 3 |p_m| shapes (raw counts, 40 MeV/c)")
        hd.compare1d(c40, c40_3, edges40, labels=("stage 4 post-FSI", "stage 3 pre-FSI"),
                     xname=xname, quiet=True, save=fh)
    print("wrote", f"{stem}.txt")


def kin_readouts(out, target, tune):
    kq.TUNES = {tune: kq.TUNES[tune]}         # panel ranges from this tune alone
    cache = kq.load_cut_cache(target, tune)
    npc = cache["n_p"]
    psel = (npc == 1) if kq.PROTON_SEL == "1p" else cache["has_p"].astype(bool)
    stem = out / f"kin_qel_q2cut_{target.lower()}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png  (+ _counts: same counts, raw axis)", [
            f"tune {tune}; qel && Q2 slice (both hit-nucleon species): N = {len(cache['Q2']):,} of qel = "
            f"{int(cache['n_qel'][0]):,} of ntot = {int(cache['ntot'][0]):,}",
            f"proton panels (T_p, theta_p): N_p = 1 -> {int(psel.sum()):,} events",
            "bin ranges: pooled p0.2-p99.8 rounded to the panel step, as in the figure",
        ])
        single = {tune: cache}
        for key, lab, step, nb in kq.PANELS:
            rng = kq.panel_range(single, key, step)
            bins = np.linspace(rng[0], rng[1], nb)
            x = cache[key]
            m = np.isfinite(x)
            if key in ("Tp", "theta_p"):
                m &= psel
            cnt, _ = np.histogram(x[m], bins=bins)
            section(fh, f"describe1d {key} ({lab})")
            hd.describe1d(cnt, bins, name=key, table=False, quiet=True, save=fh)
    print("wrote", f"{stem}.txt")
    for suffix in ("_counts",):
        with open(out / f"kin_qel_q2cut_{target.lower()}{suffix}.txt", "w") as fh:
            header(fh, f"kin_qel_q2cut_{target.lower()}{suffix}.png",
                   [f"same counts as kin_qel_q2cut_{target.lower()}.txt (raw events/bin axis)"])

    stem = out / f"empm_q2cut_{target.lower()}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png  (+ _counts, _lin: same counts, other axes)", [
            f"tune {tune}; qel && Q2 slice && N_p = 1, E_m/p_m UNCUT: N = {int(psel.sum()):,}",
            "grey dashed section-4 window in the figure = 0 < E_m < 80 MeV, p_m < 300 MeV/c (not applied)",
        ])
        m0 = psel
        w = (m0 & (cache["E_miss"] >= 0) & (cache["E_miss"] < 80) & (cache["p_miss"] < 300))
        fh.write(f"# in-window fraction (of N_p = 1): {w.sum() / max(m0.sum(), 1):.3f}\n")
        PANELS2 = [("E_miss", "E_m = omega - T_p [MeV]", 20.0, 55),
                   ("p_miss", "p_m [MeV/c]", 50.0, 55)]
        for key, lab, step, nb in PANELS2:
            rng = kq.panel_range({tune: cache}, key, step)
            bins = np.linspace(rng[0], rng[1], nb)
            m = np.isfinite(cache[key]) & psel
            cnt, _ = np.histogram(cache[key][m], bins=bins)
            section(fh, f"describe1d {key} ({lab})")
            hd.describe1d(cnt, bins, name=key, table=False, quiet=True, save=fh)
    print("wrote", f"{stem}.txt")
    for suffix in ("_counts", "_lin"):
        with open(out / f"empm_q2cut_{target.lower()}{suffix}.txt", "w") as fh:
            header(fh, f"empm_q2cut_{target.lower()}{suffix}.png",
                   [f"same counts as empm_q2cut_{target.lower()}.txt (raw-count / linear-y axis)"])


def fsi_readouts(out, target, tune):
    ev = fp.load(target, tune)
    l, p = ev["l"], ev["p"]
    psel = (ev["np"] == 1) if fp.PROTON_SEL == "1p" else l["has"]
    win = psel & (l["pm"] < fp.PM_MAX) & (l["Er"] >= fp.EM_LO) & (l["Er"] < fp.EM_HI)
    hl, _ = np.histogram(l["Er"][win], bins=fp.EDGES_E)
    hp, _ = np.histogram(p["Er"][win & p["has"]], bins=fp.EDGES_E)
    tp_all = np.concatenate([l["Tp"][win], p["Tp"][win & p["has"]]])
    tp_all = tp_all[np.isfinite(tp_all)]
    lo, hi = np.percentile(tp_all, [0.2, 99.8])
    bins = np.linspace(np.floor(lo * 10) / 10, np.ceil(hi * 10) / 10, 55)
    tl, _ = np.histogram(l["Tp"][win], bins=bins)
    tpre, _ = np.histogram(p["Tp"][win & p["has"]], bins=bins)
    dT = (p["Tp"][win] - l["Tp"][win]) * 1000.0
    dT = dT[np.isfinite(dT)]
    stem = out / f"fsi_prepost_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"tune {tune}; section-4 post-FSI in-window events (qel && hit p && Q2 slice && N_p=1,",
            f"E_m+T_rec in [0,80), p_m < 300): N = {int(win.sum()):,}; leading == vertex descendant "
            f"{100 * (win & ev['same']).sum() / max(win.sum(), 1):.1f} %",
            f"dT_p = T_p(pre) - T_p(post): median {np.median(dT):.2f} MeV, "
            f"fraction |dT_p| <= 1 MeV {np.mean(np.abs(dT) <= 1.0):.3f}",
        ])
        section(fh, "compare1d post-FSI vs pre-FSI on the restored axis (2 MeV bins, raw events)")
        hd.compare1d(hl, hp, fp.EDGES_E, labels=("post-FSI p", "pre-FSI primary p"),
                     xname="E_m+T_rec [MeV]", quiet=True, save=fh)
        section(fh, "compare1d post-FSI vs pre-FSI T_p (raw events)")
        hd.compare1d(tl, tpre, bins, labels=("post-FSI p", "pre-FSI primary p"),
                     xname="T_p [GeV]", quiet=True, save=fh)
    print("wrote", f"{stem}.txt")


def signed_readouts(out, target, tune, n_norm, norm_desc):
    cache = ps.CACHE_ROOT / f"pmiss_signed_{target.lower()}" / f"{tune}.npz"
    c = dict(np.load(cache))
    Z = ps.TGT[target]["Z"]
    stem = out / f"pmiss_signed_{target.lower()}_{tune}"
    with open(f"{stem}.txt", "w") as fh:
        header(fh, f"{stem.name}.png", [
            f"tune {tune}; qel && hit p && Q2 slice && N_p=1, 0 < E_m < 80 MeV; signed p_m = sign(p_m . x_e') |p_m|",
            f"density scale Z*cnt/(N*dp*4 pi p_c^2) with {norm_desc}; data overlay shape-scaled (not compared here)",
        ])
        for s, label in ((3, "pre-FSI primary p"), (4, "post-FSI p")):
            cnt, y = ps.occ_hist(c[f"pm{s}"], c[f"Em{s}"], n_norm, Z)
            nb = len(cnt) // 2
            pos, neg = cnt[nb:], cnt[:nb][::-1]
            A = (pos.sum() - neg.sum()) / max(pos.sum() + neg.sum(), 1)
            section(fh, f"describe1d stage {s} ({label}) signed p_m, raw counts; integrated A = {A:+.4f}")
            hd.describe1d(cnt, ps.EDGES, name=f"stage {s} signed", table=False, quiet=True, save=fh)
            section(fh, f"compare1d stage {s}: + side vs - side (|p_m| bins, raw counts)")
            hd.compare1d(pos, neg, ps.EDGES[nb:], labels=("+ side (toward e')", "- side"),
                         xname="|p_m| [MeV/c]", quiet=True, save=fh)
    print("wrote", f"{stem}.txt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="C12", choices=["C12", "Fe56"])
    ap.add_argument("--tune", default="GEM26_22b_05_000")
    ap.add_argument("--proton-sel", default="1p", choices=["leading", "1p"])
    ap.add_argument("--data-conv", default="raw", choices=["folded", "raw"])
    ap.add_argument("--norm", default="total-qe", choices=["windowed", "total-qe"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--skip", nargs="*", default=[],
                    choices=["em", "pm", "kin", "fsi", "signed"])
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for mod in (em, pm, ps, fp, kq):
        mod.PROTON_SEL = args.proton_sel
    cache_root = REPO / ("results/prd-analyzer-v0.3/cache" if args.proton_sel == "1p"
                         else "results/prd-analyzer-v0.2/cache")
    em.CACHE_ROOT = pm.CACHE_ROOT = ps.CACHE_ROOT = cache_root
    em.set_data_conv(args.data_conv)
    pm.set_data_conv(args.data_conv)

    cfg = em.TGT[args.target]
    m_rec = cfg["m_rec_gev"] if cfg["m_rec_gev"] is not None else em._m_rec_c12()
    c = restored(dict(np.load(cache_root / f"ladder_{args.target.lower()}" / f"{args.tune}.npz")), m_rec)
    n_norm, norm_desc = norm_count(args.norm, args.target, args.tune, c)
    print(f"[{args.tune}] {norm_desc}; data {args.data_conv}")

    if "em" not in args.skip:
        em_ladder_readouts(out, args.target, args.tune, c, n_norm, norm_desc,
                           em.scale_dutta(cfg["dutta"]()))
    if "pm" not in args.skip:
        pm_ladder_readouts(out, args.target, args.tune, c, n_norm, norm_desc,
                           pm.TGT[args.target]["dutta"]())
    if "kin" not in args.skip:
        kin_readouts(out, args.target, args.tune)
    if "fsi" not in args.skip:
        fsi_readouts(out, args.target, args.tune)
    if "signed" not in args.skip:
        signed_readouts(out, args.target, args.tune, n_norm, norm_desc)


if __name__ == "__main__":
    main()

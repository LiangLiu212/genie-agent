#!/usr/bin/env python3
"""(T_p, theta_p) of the recoil proton in GENIE DM-nucleon elastic (DMEL) samples on Ar40.

Reads gntpc rootracker files, one per DM mass, listed in a TSV (mass_GeV, ..., log, ...);
the runlog gives the GHEP path and the rootracker file is <stem>.gtrac.root next to it.
Only events whose EvtCode carries proc:DarkMatter,DMEL are used.

Per event: incoming DM = StdHep entry 0; the observable is the LEADING final-state proton
(status 1, pdg 2212) after intranuclear rescattering -- DMEL on a neutron leaves a neutron
unless FSI charge-exchanges it, so only a fraction of DMEL events have a proton at all
(reported). Also read: the struck nucleon before FSI (status 14) for the truth-level
comparison in the text readout. Overlaid: the free-nucleon two-body relation
cos(theta) = (E + M)/p * sqrt(T/(T + 2M)) at the flux edges; Fermi motion, binding and FSI
smear the sample around it.

    pixi run python results/template/plot_dmel_recoil.py --events-tsv DM_test/dm_mass_scan_e1000_DMEL_events.tsv --out-dir DM_test
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
from matplotlib.colors import LogNorm   # noqa: E402
import uproot   # noqa: E402
import awkward as ak   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_style import (apply_style, new_panels, style_axis,   # noqa: E402
                        FS_LABEL, FS_LEGEND, FS_SUPTITLE, DPI)
import histdiag as hd   # noqa: E402

REPO = Path(__file__).resolve().parents[2]
M_P = 0.938272
M_N = 0.939565


def _angles(v, ref):
    cos = np.einsum("ij,ij->i", v, ref) / (np.linalg.norm(v, axis=1) * np.linalg.norm(ref, axis=1))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def load_sample(log_path: str):
    rec = json.loads(Path(log_path).read_text())
    ghep = rec["outputs"]["primary_output"]
    t = uproot.open(ghep[: -len(".ghep.root")] + ".gtrac.root")["gRooTracker"]
    p4 = t["StdHepP4"].array(library="ak"); pdg = t["StdHepPdg"].array(library="ak")
    st = t["StdHepStatus"].array(library="ak")
    code = np.array([str(c) for c in t["EvtCode/fString"].array(library="np")])
    isel = np.array(["proc:DarkMatter,DMEL;" in c for c in code])
    p4, pdg, st = p4[isel], pdg[isel], st[isel]
    n_dmel = int(isel.sum())
    dm = np.asarray(p4[:, 0, :])[:, :3]
    # leading final-state proton
    selp = (pdg == 2212) & (st == 1)
    has_p = np.asarray(ak.sum(selp, axis=1) > 0)
    pp4 = p4[selp]; ep = pp4[:, :, 3]
    lead = ak.argmax(ep, axis=1, keepdims=True)
    lp = ak.to_numpy(ak.firsts(pp4[lead])[has_p])
    T_p = lp[:, 3] - M_P; th_p = _angles(lp[:, :3], dm[has_p])
    # struck nucleon before FSI (status 14: hadron in the nucleus), first one
    sel14 = (st == 14) & ((pdg == 2212) | (pdg == 2112))
    has14 = np.asarray(ak.sum(sel14, axis=1) > 0)
    n14 = ak.to_numpy(ak.firsts(p4[sel14])[has14]); pdg14 = ak.to_numpy(ak.firsts(pdg[sel14])[has14])
    T_14 = n14[:, 3] - np.where(pdg14 == 2212, M_P, M_N); th_14 = _angles(n14[:, :3], dm[has14])
    hit_p_frac = float(np.mean(pdg14 == 2212)) if len(pdg14) else float("nan")
    return dict(mass=rec["inputs"]["dm_mass"], emin=rec["inputs"]["energy_min"], emax=rec["inputs"]["energy_max"],
                n_dmel=n_dmel, n_total=len(code), T_p=T_p, th_p=th_p, has_p_frac=float(has_p.mean()),
                T_14=T_14, th_14=th_14, hit_p_frac=hit_p_frac)


def two_body_theta(T, E, m, M):
    p = np.sqrt(E**2 - m**2)
    cos = (E + M) / p * np.sqrt(T / (T + 2 * M))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def t_max(E, m, M):
    return 2 * M * (E**2 - m**2) / (m**2 + M**2 + 2 * M * E)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events-tsv", default="DM_test/dm_mass_scan_e1000_DMEL_events.tsv")
    ap.add_argument("--out-dir", default="DM_test")
    ap.add_argument("--stem", default="dmel_recoil_Tp_theta")
    args = ap.parse_args()
    apply_style()

    rows = {}
    for r in csv.DictReader(open(REPO / args.events_tsv), delimiter="\t"):
        rows[float(r["mass_GeV"])] = r["log"]
    samples = [load_sample(rows[m]) for m in sorted(rows)]

    ncols = 5 if len(samples) > 6 else 3; nrows = int(np.ceil(len(samples) / ncols))
    fig, axes = new_panels(ncols=ncols, nrows=nrows, sharey=False)
    T_edges = np.logspace(-3, 3, 61)            # 1 MeV .. 1 TeV
    th_edges = np.logspace(-2, 2, 41)           # 0.01 .. 100 deg
    out_dir = REPO / args.out_dir; out_dir.mkdir(parents=True, exist_ok=True)
    txt = out_dir / f"{args.stem}.txt"; fh = open(txt, "w")
    fh.write("# DMEL recoil proton readouts (histdiag); leading final-state proton after FSI; "
             "T_p log bins 1e-3..1e3 GeV, theta_p log bins 1e-2..1e2 deg\n")
    for ax, s in zip(axes, samples):
        m, emin, emax, T, th = s["mass"], s["emin"], s["emax"], s["T_p"], s["th_p"]
        H, xe, ye = np.histogram2d(T, th, bins=[T_edges, th_edges])
        ax.pcolormesh(xe, ye, H.T, norm=LogNorm(vmin=1, vmax=max(H.max(), 2)), cmap="viridis")
        Tg = np.logspace(-3, 3, 400)
        for E, ls, lab in ((emin, "--", f"E = {emin:g} GeV"), (emax, ":", f"E = {emax:g} GeV")):
            ok = Tg <= t_max(E, m, M_P)
            ax.plot(Tg[ok], two_body_theta(Tg[ok], E, m, M_P), ls, color="C3", lw=1.5, label=lab)
        style_axis(ax, title=f"m = {m:g} GeV  (p in {100*s['has_p_frac']:.0f}% of {s['n_dmel']})",
                   xlabel="T$_p$ [GeV]", logx=True, logy=True, ymin=None)
        ax.set_xlim(1e-3, 1e3); ax.set_ylim(1e-2, 1e2)
        ax.legend(title="free-p two-body", fontsize=FS_LEGEND - 1, title_fontsize=FS_LEGEND, loc="lower left")
        fh.write(f"\n===== m = {m:g} GeV, flux {emin:g}-{emax:g} GeV: {s['n_dmel']} DMEL events of {s['n_total']}; "
                 f"leading final-state proton in {100*s['has_p_frac']:.1f}%; struck nucleon is a proton in {100*s['hit_p_frac']:.1f}% =====\n")
        fh.write(f"T_p [GeV] (post-FSI leading p): min {T.min():.4g} median {np.median(T):.4g} mean {T.mean():.4g} max {T.max():.4g}; "
                 f"free-p kinematic max at E={emax:g}: {t_max(emax, m, M_P):.4g}\n")
        fh.write(f"theta_p [deg]: min {th.min():.4g} median {np.median(th):.4g} mean {th.mean():.4g} max {th.max():.4g}\n")
        T14, th14 = s["T_14"], s["th_14"]
        fh.write(f"struck nucleon before FSI: T median {np.median(T14):.4g} max {T14.max():.4g} GeV; theta median {np.median(th14):.4g} deg\n")
        cT, _ = np.histogram(T, T_edges); cth, _ = np.histogram(th, th_edges)
        hd.describe1d(cT, T_edges, name="T_p [GeV] (log bins)", quiet=True, save=fh)
        hd.describe1d(cth, th_edges, name="theta_p [deg] (log bins)", quiet=True, save=fh)
        hd.describe2d(H, xe, ye, xname="T_p", yname="theta_p", quiet=True, save=fh)
    for ax in axes[len(samples):]:
        ax.set_visible(False)
    for r in range(nrows):
        axes[r * ncols].set_ylabel(r"$\theta_p$ [deg]", fontsize=FS_LABEL)
    fig.suptitle("GENIE rc-v380 GDM18_00a_00_000: DM-nucleon elastic (DMEL) on Ar40, leading final-state proton "
                 "(T$_p$, $\\theta_p$ to the DM direction), after FSI\nflat DM flux per panel, z = 0.5, g = 1.0; "
                 "colour = events per bin (log); dashed/dotted = free-proton two-body relation at the flux edges",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    png = out_dir / f"{args.stem}.png"; fig.savefig(png, dpi=DPI); plt.close(fig); fh.close()
    print(f"wrote {png}\n      {txt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

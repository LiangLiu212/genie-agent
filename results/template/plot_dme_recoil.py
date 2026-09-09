#!/usr/bin/env python3
"""(T_e, theta_e) of the recoil electron in GENIE DM-electron elastic (DME) samples.

Reads gntpc rootracker files (gst cannot convert DME events), one per DM mass, listed
in a TSV with columns mass_GeV, flux_emin_GeV, jobid, log, cross_sections (the runlog
gives the GHEP path; the rootracker file is <stem>.gtrac.root next to it).

Per event: the incoming DM is StdHep entry 0, the recoil electron the status-1 e-;
T_e = E_e - m_e, theta_e = angle(p_e, p_DM). Overlaid: the two-body relation
cos(theta_e) = (E + m_e)/p * sqrt(T_e / (T_e + 2 m_e)) at the flux edges (dashed),
which bounds the populated band. One 2D panel per mass (log axes: T_e spans
decades across masses) + histdiag readouts of the 2D map and both projections.

    pixi run python results/template/plot_dme_recoil.py --events-tsv DM_test/dm_mass_scan_e1000_DME_events.tsv --out-dir DM_test
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
M_E = 0.000510999


def load_sample(log_path: str):
    """Return (mass, emin, emax, T_e[GeV], theta_e[deg]) for one DME run."""
    rec = json.loads(Path(log_path).read_text())
    ghep = rec["outputs"]["primary_output"]
    rt = ghep[: -len(".ghep.root")] + ".gtrac.root"
    t = uproot.open(rt)["gRooTracker"]
    p4 = t["StdHepP4"].array(library="ak"); pdg = t["StdHepPdg"].array(library="ak")
    st = t["StdHepStatus"].array(library="ak")
    code = t["EvtCode/fString"].array(library="np")
    assert all("proc:DarkMatter,DME;" in str(c) for c in code), "non-DME events in file"
    dm = np.asarray(p4[:, 0, :])                                 # incoming DM (px,py,pz,E)
    sel = (pdg == 11) & (st == 1)
    assert ak.all(ak.sum(sel, axis=1) == 1), "expected exactly one final-state e- per event"
    e = np.asarray(ak.firsts(p4[sel]))
    T = e[:, 3] - M_E
    cos = np.einsum("ij,ij->i", e[:, :3], dm[:, :3]) / (np.linalg.norm(e[:, :3], axis=1) * np.linalg.norm(dm[:, :3], axis=1))
    theta = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    return rec["inputs"]["dm_mass"], rec["inputs"]["energy_min"], rec["inputs"]["energy_max"], T, theta


def two_body_theta(T, E, m):
    """theta_e [deg] for recoil kinetic energy T from a DM of energy E, mass m."""
    p = np.sqrt(E**2 - m**2)
    cos = (E + M_E) / p * np.sqrt(T / (T + 2 * M_E))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events-tsv", default="DM_test/dm_mass_scan_e1000_DME_events.tsv")
    ap.add_argument("--out-dir", default="DM_test")
    ap.add_argument("--stem", default="dme_recoil_Te_theta")
    args = ap.parse_args()
    apply_style()

    rows = {}
    for r in csv.DictReader(open(REPO / args.events_tsv), delimiter="\t"):
        rows[float(r["mass_GeV"])] = r["log"]          # last row per mass wins
    samples = [load_sample(rows[m]) for m in sorted(rows)]

    ncols = 3; nrows = int(np.ceil(len(samples) / ncols))
    fig, axes = new_panels(ncols=ncols, nrows=nrows, sharey=False)
    T_edges = np.logspace(-4, 3, 71)            # 0.1 MeV .. 1 TeV, 10 bins/decade
    th_edges = np.logspace(-3, 2, 51)           # 1 mdeg .. 100 deg
    out_dir = REPO / args.out_dir; out_dir.mkdir(parents=True, exist_ok=True)
    txt = out_dir / f"{args.stem}.txt"
    fh = open(txt, "w")
    fh.write("# DME recoil electron readouts (histdiag); T_e log bins 1e-4..1e3 GeV, theta_e log bins 1e-3..1e2 deg\n")
    for ax, (m, emin, emax, T, th) in zip(axes, samples):
        H, xe, ye = np.histogram2d(T, th, bins=[T_edges, th_edges])
        ax.pcolormesh(xe, ye, H.T, norm=LogNorm(vmin=1, vmax=max(H.max(), 2)), cmap="viridis")
        Tg = np.logspace(-4, np.log10(T.max() * 1.5), 400)
        for E, ls, lab in ((emin, "--", f"E = {emin:g} GeV"), (emax, ":", f"E = {emax:g} GeV")):
            ok = Tg <= 2 * M_E * (E**2 - m**2) / (m**2 + M_E**2 + 2 * M_E * E)   # kinematic T_max
            ax.plot(Tg[ok], two_body_theta(Tg[ok], E, m), ls, color="C3", lw=1.5, label=lab)
        style_axis(ax, title=f"m = {m:g} GeV  (n = {len(T)})", xlabel="T$_e$ [GeV]",
                   logx=True, logy=True, ymin=None)
        ax.set_xlim(1e-4, 1e3); ax.set_ylim(1e-3, 1e2)
        ax.legend(title="two-body curve", fontsize=FS_LEGEND - 1, title_fontsize=FS_LEGEND, loc="lower left")
        # readouts
        cT, _ = np.histogram(T, T_edges); cth, _ = np.histogram(th, th_edges)
        fh.write(f"\n===== m = {m:g} GeV, flux {emin:g}-{emax:g} GeV, {len(T)} DME events =====\n")
        fh.write(f"T_e [GeV]: min {T.min():.4g} median {np.median(T):.4g} mean {T.mean():.4g} max {T.max():.4g}; "
                 f"kinematic T_max at E={emax:g}: {2*M_E*(emax**2-m**2)/(m**2+M_E**2+2*M_E*emax):.4g}\n")
        fh.write(f"theta_e [deg]: min {th.min():.4g} median {np.median(th):.4g} mean {th.mean():.4g} max {th.max():.4g}\n")
        hd.describe1d(cT, T_edges, name="T_e [GeV] (log bins)", quiet=True, save=fh)
        hd.describe1d(cth, th_edges, name="theta_e [deg] (log bins)", quiet=True, save=fh)
        hd.describe2d(H, xe, ye, xname="T_e", yname="theta_e", quiet=True, save=fh)
    for ax in axes[len(samples):]:
        ax.set_visible(False)
    for r in range(nrows):
        axes[r * ncols].set_ylabel(r"$\theta_e$ [deg]", fontsize=FS_LABEL)
    fig.suptitle("GENIE rc-v380 GDM18_00a_00_000: DM-electron elastic on Ar40, recoil electron "
                 "(T$_e$, $\\theta_e$ to the DM direction)\nflat DM flux per panel, z = 0.5, g = 1.0; "
                 "colour = events per bin (log); dashed/dotted = two-body relation at the flux edges",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    png = out_dir / f"{args.stem}.png"; fig.savefig(png, dpi=DPI); plt.close(fig)
    fh.close()
    print(f"wrote {png}\n      {txt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

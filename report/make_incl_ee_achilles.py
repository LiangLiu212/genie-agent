"""Overlay ACHILLES (QE spectral function) on the GENIE vs (e,e') data figure.

Single panel: 12C, E = 2.5 GeV, theta = 15 deg (Zeller:1973ge) — archive data,
the three full-EM GENIE tunes of report/make_incl_ee_comparison.py, a dashed
QE-only projection of the SF tune (GEM26_22b: Benhar SF + UnifiedQEL, the
direct GENIE counterpart of ACHILLES' model), and the ACHILLES sample.

GENIE normalization is Recipe A (see make_incl_ee_comparison.py). ACHILLES
events are generated *inside* the theta window (HardCuts AngleTheta [14,16]),
and achilles reports sigma within cuts (log prints nb; the NuHepMC file
attribute declares pb), so
  dsigma/dOmega/domega |_bin = sigma_cut * N_bin / (N_gen * dOmega * domega)
with dOmega = 2pi*(cos 14 - cos 16) — the same window the GENIE theta mask
selects, no acceptance correction needed for unweighted events.

ACHILLES sample: /exp/dune/app/users/liangliu/ACHILLES/runs/e_C12_2500MeV_15deg
(100k events, seed 20260819, QESpectral only — no RES/DIS, so the curve is
expected to die off past the QE peak). The 120 MB NuHepMC ascii is parsed once
and cached as omega_theta_cache.npz next to it.

Usage:
  pixi run python report/make_incl_ee_achilles.py
"""

import math
import re
import sys
from pathlib import Path

import numpy as np
import uproot

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "report"))
sys.path.insert(0, str(REPO / "results" / "template"))
from make_incl_ee_comparison import (DTHETA, OMEGA_BIN, E38_TO_NB,
                                     load_data, spline_sum_at)
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_SUPTITLE, DPI)

E_BEAM, THETA, TARGET = 2.5, 15.0, "12C"

# GENIE 500k full-EM samples + splines (run-manifest.jsonl, 2026-08-17; jobids
# gevgen-eminus_C12_20260817-{174204-1d5-71f27f,174627-ba3-07789e,203307-d6f-345eea})
RUNS = REPO / "genie-agent" / "genie-runs"
GENIE_SAMPLES = [  # (label, spline.xml, gst.root)
    ("LFG+Rosenbluth",
     RUNS / "GEM26_11a_09_000-2026-08-17" / "eminus_C12_20260817-164234-04a.xml",
     RUNS / "GEM26_11a_09_000-2026-08-17" / "eminus_C12_20260817-174204-1d5.gst.root"),
    ("SuSAv2",
     RUNS / "GEM21_11a_09_000-2026-08-17" / "eminus_C12_20260817-164328-034.xml",
     RUNS / "GEM21_11a_09_000-2026-08-17" / "eminus_C12_20260817-174627-ba3.gst.root"),
    ("SF+UnifiedQEL",
     RUNS / "GEM26_22b_09_000-2026-08-17" / "eminus_C12_20260817-164329-09f.xml",
     RUNS / "GEM26_22b_09_000-2026-08-17" / "eminus_C12_20260817-203307-d6f.gst.root"),
]
QE_ONLY_LABEL = "SF+UnifiedQEL"  # tune that also gets a dashed QE-only curve

ACHILLES_DIR = Path("/exp/dune/app/users/liangliu/ACHILLES/runs/e_C12_2500MeV_15deg")
ACHILLES_HEPMC = ACHILLES_DIR / "e_C12_2500MeV_15deg.hepmc"
ACHILLES_LOG = ACHILLES_DIR / "achilles_run.log"
ACHILLES_CACHE = ACHILLES_DIR / "omega_theta_cache.npz"


def achilles_arrays():
    """(omega GeV, theta deg) of the scattered electron per event, cached."""
    if ACHILLES_CACHE.exists():
        c = np.load(ACHILLES_CACHE)
        return c["omega"], c["theta"]
    om, th, n_ev = [], [], 0
    with open(ACHILLES_HEPMC) as f:
        for line in f:
            if line.startswith("E "):
                n_ev += 1
            elif line.startswith("P "):
                # P id mother pid px py pz E m status   (U MEV MM)
                t = line.split()
                if t[3] == "11" and t[9] == "1":
                    px, py, pz, E = (float(x) for x in t[4:8])
                    om.append((2500.0 - E) / 1000.0)
                    th.append(math.degrees(math.acos(
                        pz / math.sqrt(px * px + py * py + pz * pz))))
    om, th = np.array(om), np.array(th)
    if len(om) != n_ev:
        raise RuntimeError(f"{len(om)} scattered electrons for {n_ev} events")
    np.savez(ACHILLES_CACHE, omega=om, theta=th)
    return om, th


def achilles_sigma_nb():
    """Final 'Total xsec' (nb, within cuts) from the run log."""
    m = re.findall(r"Total xsec: ([0-9.eE+-]+) \+/- ([0-9.eE+-]+)",
                   ACHILLES_LOG.read_text())
    if not m:
        raise RuntimeError(f"no 'Total xsec' line in {ACHILLES_LOG}")
    return float(m[-1][0]), float(m[-1][1])


def genie_spectra(gst_path, spline_xml, edges):
    """(full-EM spec, QE-only spec) in nb/sr/GeV — Recipe A, one gst read."""
    a = uproot.open(gst_path)["gst"].arrays(
        ["Ev", "El", "cthl", "qel", "wght"], library="np")
    omega = a["Ev"] - a["El"]
    th = np.degrees(np.arccos(np.clip(a["cthl"], -1, 1)))
    mask = np.abs(th - THETA) < DTHETA
    total_native, _ = spline_sum_at(spline_xml, E_BEAM)
    sig_nb = total_native * 3.8937937e10 * E38_TO_NB
    dOmega = 2 * math.pi * (math.cos(math.radians(THETA - DTHETA))
                            - math.cos(math.radians(THETA + DTHETA)))
    w = a["wght"]
    norm = sig_nb / (w.sum() * dOmega * np.diff(edges))
    full, _ = np.histogram(omega[mask], bins=edges, weights=w[mask])
    qe, _ = np.histogram(omega[mask & a["qel"]], bins=edges,
                         weights=w[mask & a["qel"]])
    return full * norm, qe * norm


def main():
    om_d, sig_d, err_d = load_data(TARGET, E_BEAM, THETA)
    edges = np.arange(0.0, om_d.max() + 2 * OMEGA_BIN, OMEGA_BIN)
    dOmega = 2 * math.pi * (math.cos(math.radians(THETA - DTHETA))
                            - math.cos(math.radians(THETA + DTHETA)))

    apply_style()
    fig, axes = new_panels(ncols=1)
    ax = axes[0]
    ax.errorbar(om_d, sig_d, yerr=err_d, fmt="o", ms=3, capsize=2,
                color="black", label="data", zorder=5)

    for i, (label, spl, gst) in enumerate(GENIE_SAMPLES):
        full, qe = genie_spectra(gst, spl, edges)
        ax.stairs(full, edges, color=COLORS[i], lw=1.6, label=f"GENIE {label}")
        if label == QE_ONLY_LABEL:
            ax.stairs(qe, edges, color=COLORS[i], lw=1.2, ls="--",
                      label="GENIE SF (QE only)")

    om_a, th_a = achilles_arrays()
    sig_a, dsig_a = achilles_sigma_nb()
    in_win = np.abs(th_a - THETA) < DTHETA
    counts, _ = np.histogram(om_a[in_win], bins=edges)
    spec_a = sig_a * counts / (len(om_a) * dOmega * np.diff(edges))
    ax.stairs(spec_a, edges, color=COLORS[3], lw=2.0,
              label="ACHILLES QE SF")
    print(f"ACHILLES: {in_win.sum()}/{len(om_a)} events in window, "
          f"sigma_cut = {sig_a:.2f} +/- {dsig_a:.2f} nb")

    style_axis(ax, title=f"$^{{12}}$C  E = {E_BEAM:g} GeV, "
                         f"$\\theta$ = {THETA:g}°$\\pm${DTHETA:g}°",
               xlabel="$\\omega$  [GeV]", ymin=None)
    ax.set_ylabel("$d\\sigma/d\\Omega\\,d\\omega$  [nb/sr/GeV]",
                  fontsize=FS_LABEL)
    handles, labels = ax.get_legend_handles_labels()
    order = [labels.index("data")] + \
            [i for i, l in enumerate(labels) if l != "data"]
    ax.set_xlim(-0.02, om_d.max() + OMEGA_BIN)      # stop at the data range
    ax.set_ylim(0, ax.get_ylim()[1] * 1.30)         # headroom for the legend
    ax.legend([handles[i] for i in order], [labels[i] for i in order],
              fontsize=FS_LEGEND, loc="upper right")
    fig.suptitle("ACHILLES vs GENIE vs (e,e') data", fontsize=FS_SUPTITLE)
    fig.tight_layout()
    out = REPO / "report" / "incl_ee_achilles_c12.png"
    fig.savefig(out, dpi=DPI)
    print(f"saved {out}")


if __name__ == "__main__":
    main()

"""Overlay GENIE electron samples on QES-archive inclusive (e,e') data.

One panel per (target, beam) setting: archive dsigma/dOmega/domega points vs
absolutely-normalized GENIE omega spectra in a theta acceptance bin around the
spectrometer angle.

Normalization (report/genie-event-normalization.md, Recipe A):
  dsigma/dOmega/domega |_bin = sigma_tot * N(theta cut & omega bin)
                               / (N_gen * dOmega * domega)
with sigma_tot for the FULL sample (all channels), dOmega = 2pi*(cos th_min -
cos th_max), and the theta cut living only in the numerator (no acceptance
correction needed for unweighted events).

sigma_tot for a full-EM run is the sum over every <spline> in the gmkspl XML
evaluated at the beam energy. Spline knots are in GENIE natural units (GeV^-2);
1 GeV^-2 = (hbar c)^2 = 0.38937937 GeV^2 mb = 3.8937937e10 x 1e-38 cm^2.
The distinct gst XSec values (1e-38 cm^2) of the qel hit-p/hit-n channels are
used as a consistency CHECK against the QEL-EM splines at E (they must agree
to ~5%; residual is spline interpolation). 1e-38 cm^2 = 1e-5 nb.

Usage (after the gevgen runs are converted to gst):
  pixi run python report/make_incl_ee_comparison.py \
      --setting 12C:2.5:15 --setting 56Fe:2.7:15 \
      --sample "12C:LFG+Rosenbluth:<spline.xml>:<gst.root>" \
      --sample "56Fe:LFG+Rosenbluth:<spline.xml>:<gst.root>" ...
"""

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import uproot

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "results" / "template"))
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

DTHETA = 1.0          # theta acceptance half-width (deg)
OMEGA_BIN = 0.015     # GeV, matches the archive's typical omega spacing
E38_TO_NB = 1e-5      # 1e-38 cm^2 in nb
GEV2_TO_E38 = 3.8937937e10   # 1 GeV^-2 = (hbar c)^2 in units of 1e-38 cm^2


def load_data(target, e_beam, theta):
    """Archive points (omega, sigma, err) for one setting."""
    om, sig, err = [], [], []
    for line in (REPO / "data" / "qes-archive" / f"{target}.dat").read_text().splitlines():
        t = line.split()
        if len(t) >= 8 and float(t[2]) == e_beam and float(t[3]) == theta:
            om.append(float(t[4])); sig.append(float(t[5])); err.append(float(t[6]))
    return np.array(om), np.array(sig), np.array(err)


def spline_sum_at(spline_xml, e_beam):
    """Sum of every <spline> in a gmkspl XML at E (native GeV^-2) + the QEL-EM
    proton/neutron spline values there (for the gst consistency check).
    Interpolates log(xsec) vs E — smoother than linear for coarse knot grids."""
    root = ET.parse(spline_xml).getroot()
    total, qel = 0.0, {}
    for sp in root.iter("spline"):
        E = np.array([float(k.find("E").text) for k in sp.iter("knot")])
        x = np.array([float(k.find("xsec").text) for k in sp.iter("knot")])
        pos = x > 0
        if not pos.any() or e_beam < E[pos].min():
            continue
        v = float(np.exp(np.interp(e_beam, E[pos], np.log(x[pos]))))
        total += v
        name = sp.get("name", "")
        if "QEL" in name:
            if "2212" in name:
                qel["p"] = qel.get("p", 0.0) + v
            elif "2112" in name:
                qel["n"] = qel.get("n", 0.0) + v
    return total, qel


def genie_spectrum(gst_path, spline_xml, e_beam, theta, edges):
    """Absolutely-normalized dsigma/dOmega/domega (nb/sr/GeV) on omega bins."""
    t = uproot.open(gst_path)["gst"]
    a = t.arrays(["Ev", "El", "cthl", "qel", "hitnuc", "XSec", "wght"],
                 library="np")
    n_gen = len(a["El"])
    omega = a["Ev"] - a["El"]
    th = np.degrees(np.arccos(np.clip(a["cthl"], -1, 1)))

    # sigma_tot: spline sum at E, GeV^-2 -> 1e-38 cm^2 by the physical constant
    total_native, qel_native = spline_sum_at(spline_xml, e_beam)
    sig_tot_e38 = total_native * GEV2_TO_E38

    # consistency check: gst QE channel XSec (1e-38 cm^2) vs the QEL splines at E
    for nuc, key in ((2212, "p"), (2112, "n")):
        m = a["qel"] & (a["hitnuc"] == nuc)
        if m.any() and qel_native.get(key):
            gst_val = np.unique(a["XSec"][m])
            if len(gst_val) != 1:
                raise RuntimeError(f"QE {key} channel XSec not unique: {gst_val}")
            dev = gst_val[0] / (qel_native[key] * GEV2_TO_E38) - 1
            if abs(dev) > 0.05:
                raise RuntimeError(
                    f"gst QE-{key} XSec off spline by {dev:+.1%} in {gst_path}")

    mask = np.abs(th - theta) < DTHETA
    w = a["wght"]
    counts, _ = np.histogram(omega[mask], bins=edges, weights=w[mask])
    dOmega = 2 * math.pi * (math.cos(math.radians(theta - DTHETA))
                            - math.cos(math.radians(theta + DTHETA)))
    spec = sig_tot_e38 * E38_TO_NB * counts / (w.sum() * dOmega * np.diff(edges))
    return spec, int(mask.sum()), sig_tot_e38


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", action="append", required=True,
                    help="target:E_beam:theta, e.g. 12C:2.5:15")
    ap.add_argument("--sample", action="append", required=True,
                    help="target:label:spline.xml:gst.root")
    ap.add_argument("-o", "--output", default=str(REPO / "report" / "incl_ee_q2cut0p25.png"))
    args = ap.parse_args()

    settings = []
    for s in args.setting:
        tgt, e, th = s.split(":")
        settings.append((tgt, float(e), float(th)))
    samples = []
    for s in args.sample:
        tgt, label, spl, gst = s.split(":", 3)
        samples.append((tgt, label, Path(spl), Path(gst)))

    apply_style()
    fig, axes = new_panels(ncols=len(settings), sharey=False)
    nuc_tex = {"12C": "$^{12}$C", "56Fe": "$^{56}$Fe"}
    for ax, (tgt, e_beam, theta) in zip(axes, settings):
        om, sig, err = load_data(tgt, e_beam, theta)
        edges = np.arange(0.0, om.max() + 2 * OMEGA_BIN, OMEGA_BIN)
        centers = 0.5 * (edges[:-1] + edges[1:])
        ax.errorbar(om, sig, yerr=err, fmt="o", ms=3, capsize=2, color="black",
                    label="data", zorder=5)
        i = 0
        for stgt, label, spl, gst in samples:
            if stgt != tgt:
                continue
            spec, n_cut, sig_tot = genie_spectrum(gst, spl, e_beam, theta, edges)
            ax.stairs(spec, edges, color=COLORS[i % len(COLORS)], lw=1.6,
                      label=label)
            print(f"{tgt} {label}: {n_cut} events in |theta-{theta:g}|<{DTHETA:g} deg, "
                  f"sigma_tot={sig_tot:.4g}e-38 cm^2")
            i += 1
        style_axis(ax, title=f"{nuc_tex[tgt]}  E = {e_beam:g} GeV, "
                             f"$\\theta$ = {theta:g}°$\\pm${DTHETA:g}°",
                   xlabel="$\\omega$  [GeV]", ymin=None)
        ax.legend(fontsize=FS_LEGEND)
    axes[0].set_ylabel("$d\\sigma/d\\Omega\\,d\\omega$  [nb/sr/GeV]",
                       fontsize=FS_LABEL)
    fig.suptitle("GENIE (full EM, EM-MinQ2Limit = 0.25) vs QES-archive inclusive "
                 "(e,e') data", fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(args.output, dpi=DPI)
    print(f"saved {args.output}")


if __name__ == "__main__":
    main()

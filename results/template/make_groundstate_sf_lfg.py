"""Ground-state study: spectral function vs Local Fermi Gas (Rosenbluth EM-QES, C12).

Two tunes with IDENTICAL Rosenbluth QEL-EM physics, differing only in the C12
ground-state nuclear model:
  - GEM26_11a : genie::LocalFGM/Default          (Local Fermi Gas)
  - GEM26_22a : genie::SpectralFunc/Default       (Benhar 2D spectral function)
Both: e- on C12, 2.445 GeV, 1000 EMQE events.

The gmkspl total cross-section splines are numerically identical for the two
models (Pauli blocking in the integrated xsec uses the shared CommonParam[FermiGas]
kF; the momentum distribution P(k,E) only enters at event generation). So the
ground-state effect is visible only in the per-event kinematics shown here: the
struck-nucleon momentum |p_n| (left) and Q^2 (right). Reads the gst ROOT trees
with uproot; follows the personal plot style (results/template/plot_style.py).
"""
import sys, glob
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis, COLORS,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

# tune dir prefix -> (legend label, color)
SERIES = [
    ("GEM26_11a", "LFG  (LocalFGM)",    "C0"),
    ("GEM26_22a", "SF  (SpectralFunc)", "C1"),
]
RUNGLOB = "genie-agent/genie-runs/{tune}_00_000-*/*.gst.root"

def latest_gst(tune):
    hits = sorted(glob.glob(RUNGLOB.format(tune=tune)))
    return hits[-1] if hits else None

def load(tune):
    f = latest_gst(tune)
    if not f:
        print("  MISSING", tune)
        return None
    d = uproot.open(f)["gst"].arrays(["Q2", "pxn", "pyn", "pzn"], library="np")
    pmag = np.sqrt(d["pxn"]**2 + d["pyn"]**2 + d["pzn"]**2) * 1000.0  # MeV/c
    return np.asarray(d["Q2"], float), pmag

PBINS = np.linspace(0.0, 1000.0, 51)                       # |p_n|  [MeV/c]
QBINS = np.logspace(np.log10(0.01), np.log10(1.0), 40)     # Q^2  [(GeV/c)^2]

apply_style()
fig, axes = new_panels(ncols=2, sharey=False)
axp, axq = axes

for tune, label, color in SERIES:
    r = load(tune)
    if r is None:
        continue
    q2, pmag = r
    axp.hist(pmag, bins=PBINS, histtype="step", linewidth=1.8, color=color, label=label)
    axq.hist(q2, bins=QBINS, histtype="step", linewidth=1.8, color=color, label=label)

style_axis(axp, title="struck-nucleon momentum",
           xlabel=r"|p$_n$|  [MeV/c]", logx=False, logy=True, ymin=0.5)
style_axis(axq, title="momentum transfer",
           xlabel=r"Q$^2$  [(GeV/c)$^2$]", logx=True, logy=True, ymin=0.5)
axp.set_ylabel("events / bin", fontsize=FS_LABEL)
axq.set_ylabel("events / bin", fontsize=FS_LABEL)
axp.legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)

fig.suptitle("Rosenbluth EM-QES ground state: spectral function vs Local Fermi Gas\n"
             "e⁻ on C12, 2.445 GeV, 1000 EMQE events  (GEM26_11a vs GEM26_22a)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/groundstate_sf_lfg.png"
fig.savefig(out, dpi=130)
print("wrote", out)

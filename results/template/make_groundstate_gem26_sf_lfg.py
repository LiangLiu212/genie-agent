"""Initial hit-nucleon momentum and missing (removal) energy, SF vs LFG (C12, grid).

The ground-state signature, from the gst initial hit-nucleon branches:
  - |p_n|  = `pn` (GeV -> MeV/c)
  - E_rm   = M_N - `En`  (removal/missing energy; ~the spectral function's E axis)
Aggregates all 6 E91-013 energy points per config (~600k events each). LFG (GEM26_11a) vs
SF (GEM26_22a). Emits a log-y view and a linear (normal-axes) view. Personal plot style.
"""
import sys
sys.path.insert(0, "results/template")
import numpy as np
import uproot
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE)

STAGE = "/tmp/claude-12900/gem26"
M_P, M_N = 0.938272, 0.939565

MAP = {}
for ln in open("/tmp/gst_map.txt"):
    cfg, cut, E, b = ln.split()
    MAP[(cfg, cut, E)] = b

def load(cfg):
    pn, erm = [], []
    for (c, cut, E), b in MAP.items():
        if c != cfg:
            continue
        d = uproot.open(f"{STAGE}/{b}")["gst"].arrays(["pn", "En", "hitnuc"], library="np")
        mN = np.where(d["hitnuc"] == 2212, M_P, M_N)
        pn.append(d["pn"] * 1000.0)
        erm.append((mN - d["En"]) * 1000.0)
    return np.concatenate(pn), np.concatenate(erm)

pnL, ermL = load("11a")
pnS, ermS = load("22a")
PBINS = np.linspace(0.0, 1000.0, 51)
EBINS = np.linspace(0.0, 80.0, 41)

def make_fig(out, logy):
    apply_style()
    fig, axes = new_panels(ncols=2, sharey=False)
    fig.set_size_inches(11, 5.5)
    axp, axe = axes
    for pn, erm, col, lab in [(pnL, ermL, "C0", "LFG  (LocalFGM)"),
                              (pnS, ermS, "C1", "SF  (SpectralFunc)")]:
        axp.hist(pn, bins=PBINS, histtype="step", linewidth=1.8, color=col, label=lab)
        axe.hist(erm, bins=EBINS, histtype="step", linewidth=1.8, color=col, label=lab)
    ymin = 0.5 if logy else None
    style_axis(axp, title="initial hit-nucleon momentum", xlabel=r"|p$_n$|  [MeV/c]",
               logx=False, logy=logy, ymin=ymin)
    style_axis(axe, title="missing (removal) energy", xlabel=r"E$_{rm}$ = M$_N$ − E$_n$  [MeV]",
               logx=False, logy=logy, ymin=ymin)
    for ax in (axp, axe):
        ax.set_ylabel("events / bin", fontsize=FS_LABEL)
    axp.legend(title="ground state", fontsize=FS_LEGEND, title_fontsize=FS_LEGEND_TITLE)
    fig.suptitle("Hit-nucleon momentum & missing energy — SF vs LFG\n"
                 "e⁻ on C12, GEM26 Rosenbluth · ~600k ev/config (6 E91-013 points)",
                 fontsize=FS_SUPTITLE)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print("wrote", out)

make_fig("results/groundstate_gem26_sf_lfg.png", logy=True)
make_fig("results/groundstate_gem26_sf_lfg_linear.png", logy=False)

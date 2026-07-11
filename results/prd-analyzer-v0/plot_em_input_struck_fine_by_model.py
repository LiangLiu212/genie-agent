"""Per-model fine-binned input vs struck nucleon (README 10b1 / 10b2):
one figure for SF + UnifiedQEL (22b, Benhar input) and one for
SF(2024) + UnifiedQEL (33b, 2024 input).

Each figure shows three curves in the 10b convention (occupancy scale,
hitnuc = p, no cuts, p_m < 300):

  input      the model's own table f_{k<300}(E), on its NATIVE grid;
  E_m        the struck-nucleon record, E_2 = M_p - En - T_rec -- what any
             (e,e'p)-convention reconstruction sees;
  m_N - E_n  the record with T_rec = p_n^2/(2 M_11B) added back.

The third curve lands on the input table exactly (block edges / quasiparticle
peaks restored), which pins the mechanism: the b-chain writes the struck
nucleon with En = m_N - E_sampled (static-spectator closure). This is the
SpectralFunc special case of genie::utils::BindHitNucleon (QELUtils.cxx:
"the SpectralFunc nuclear model returns a removal energy which includes the
kinetic energy of the final-state nucleus"): Mf = sqrt((Mi+E-mNi)^2 - k^2),
ENi = Mi - sqrt(Mf^2+k^2) == mNi - E. Under the tables' own convention (the
E axis is the recoil-free removal energy -- the 2024 ground-state peak sits
exactly at S_p) the reconstructed E_m therefore comes out LOWER than the
table by T_rec(k): 0.5 / 2.0 / 4.4 MeV at k = 100 / 200 / 300 MeV/c,
k-correlated -- a downward smearing, not a shift.

Reads cache/ladder/<model>.npz (build_cache_ladder.py).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
import fig9_common as F
from fig9_common import Z, PM_MAX
from acceptance import M_REC

FIGS = [
    dict(model="UnifiedQEL", table="old", tag="22b",
         out="results/prd-analyzer-v0/em_input_struck_fine_22b.png",
         input_label="Benhar input (native 5-MeV steps)",
         panels=[dict(lo=5.0, hi=40.0, bw=0.25, title="p-shell region  (0.25-MeV bins)"),
                 dict(lo=13.0, hi=22.0, bw=0.10, title="block edges  (0.1-MeV bins)")],
         ymax=3.0, legend_loc="lower right"),
    dict(model="UnifiedQEL2024", table="new", tag="33b",
         out="results/prd-analyzer-v0/em_input_struck_fine_33b.png",
         input_label="2024 input (native 0.025/0.1 MeV)",
         panels=[dict(lo=5.0, hi=40.0, bw=0.25, title="p-shell region  (0.25-MeV bins)"),
                 dict(lo=13.5, hi=22.0, bw=0.05, title="quasiparticle peaks  (0.05-MeV bins)")],
         ymax=30.0, legend_loc="upper right"),
]

tabs = F.load_input_tables()
dem, dsf, dstat, dtot = F.load_dutta()


def input_native(key):
    k, E, P, dk, dE = tabs[key]
    f = F.f_restricted(k, P, dk)
    dE = np.broadcast_to(np.asarray(dE, dtype=float), E.shape)
    edges = np.concatenate([[E[0] - dE[0] / 2.0], E - dE / 2.0 + dE])
    return f, edges


def hists(model, edges, bw):
    """(E_m, m_N - E_n) occupancy-scale histograms of the struck nucleon."""
    c = dict(np.load(f"{S.CACHE_DIR}/ladder/{model}.npz"))
    nh = float(c["n_hitp"][0])
    win = c["p2"] < PM_MAX
    e2 = c["E2"][win]
    rr = e2 + c["p2"][win] ** 2 / (2.0 * M_REC * 1e3)     # + T_rec  ->  m_N - E_n
    h = lambda x: Z * np.histogram(x, bins=edges)[0] / (nh * bw)
    return h(e2), h(rr), e2, rr


apply_style()
for spec in FIGS:
    m = spec["model"]
    f_in, e_in = input_native(spec["table"])

    fig, axes = new_panels(ncols=2, nrows=1, sharey=False)
    for ax, pan in zip(axes, spec["panels"]):
        edges = np.arange(pan["lo"], pan["hi"] + pan["bw"] / 2, pan["bw"])
        y2, yr, e2, rr = hists(m, edges, pan["bw"])
        ax.stairs(dsf, F.EDGES, color="0.82", linewidth=1.4, zorder=1,
                  label="Dutta Fig. 9 (5-MeV bins)")
        ax.stairs(f_in, e_in, color="0.4", linewidth=1.1, linestyle="-.",
                  zorder=3, label=spec["input_label"])
        ax.stairs(y2, edges, color=S.color(m), linewidth=2.0, zorder=5,
                  label=r"struck $E_m = m_N - E_n - T_{rec}$")
        ax.stairs(yr, edges, color="0.1", linewidth=1.0, zorder=6,
                  label=r"struck $+T_{rec}$ restored ($= m_N - E_n$)")
        style_axis(ax, title=pan["title"], xlabel=r"$E_m$  (MeV)",
                   logx=False, logy=True, ymin=None)
        ax.set_xlim(pan["lo"], pan["hi"])
        ax.set_ylim(5e-3, spec["ymax"])
    axes[0].set_ylabel(r"$Z\cdot$ d$N/$d$E_m\,/\,N_p$   (MeV$^{-1}$)",
                       fontsize=FS_LABEL)
    axes[0].legend(fontsize=FS_LEGEND - 3, loc=spec["legend_loc"],
                   title=S.label(m), title_fontsize=FS_LEGEND_TITLE - 3)
    axes[1].annotate("record = table $-\\,T_{rec}(k)$,  $T_{rec}=p_n^2/2M_{^{11}B}$\n"
                     "(BindHitNucleon SpectralFunc branch: $E_n = m_N - E$)",
                     xy=(0.03, 0.92), xycoords="axes fraction", va="top",
                     fontsize=FS_LEGEND - 4, color="0.25")

    # printout: how sharply the +T_rec curve restores the table
    lo_edge = 15.0 if spec["table"] == "old" else 13.0
    print(f"[{spec['tag']}] frac below table edge {lo_edge} MeV:"
          f"  E_m {np.mean(e2 < lo_edge):.3f}  ->  +T_rec {np.mean(rr < lo_edge):.4f}")

    fig.suptitle(f"input vs struck nucleon — {S.label(m)} ({spec['tag']})\n"
                 r"occupancy scale, hitnuc$\,$=$\,$p, no cuts, $p_m<300$ MeV/$c$",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    fig.savefig(spec["out"], dpi=DPI)
    print("wrote", spec["out"])

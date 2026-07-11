"""E_m budget at ladder stage 3 (pre-FSI primary proton) -- SF + UnifiedQEL only.

The four ingredients of the stage-3 missing energy

    E_m3 = omega - T_p3 - T_rec3,        omega = E_beam - E_e'

drawn as per-N_p-normalized distributions from the ladder cache
(cache/ladder/UnifiedQEL.npz, built by v0's build_cache_ladder.py; proton
channel hitnuc == p, no cuts beyond the sample's t05 generation cut
Q^2 >= 1.18):

    E_e'     [GeV]  scattered-electron energy (`El`, FSI-blind)
    omega    [GeV]  energy transfer  = 2.445 - E_e'  (monochromatic beam)
    T_p3     [GeV]  pre-FSI primary-proton kinetic energy (`T3`)
    T_rec3   [MeV]  residual-nucleus (11B) kinetic energy  p3^2 / (2 M_REC)

Consistency check (printed): T_rec recovered from the cache identity
(E_beam - El) - T3 - E3/1000 must equal p3^2/(2 M_REC) to float precision --
this validates both the monochromatic-beam assumption (Ev == 2.445 for every
event) and the inlined M_REC against what build_cache_ladder.py actually used.

    pixi run python results/prd-analyzer-v0.1/plot_em_components_prefsi.py
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0.1")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_SUPTITLE, DPI)
import samples as S

MODEL = "UnifiedQEL"                  # SF + UnifiedQEL (Variant 05), this study only
OUT = "results/prd-analyzer-v0.1/em_components_prefsi.png"

E_BEAM = 2.445                        # [GeV] campaign beam energy (samples.py)
# 11B recoil mass [GeV], same formula as v0 acceptance.py::M_REC (AME2020 atomic
# mass minus 5 electron masses); validated below against the cache identity.
M_REC = 11.0093054 * 0.93149410242 - 5 * 0.00051099895

c = dict(np.load(f"{S.CACHE_DIR}/ladder/{MODEL}.npz"))
n_p = float(c["n_hitp"][0])
El, T3 = c["El"], c["T3"]                        # [GeV]
omega = E_BEAM - El                              # [GeV]
Trec = (c["p3"] / 1000.0) ** 2 / (2.0 * M_REC)   # [GeV]

# identity check: E3 was written as (omega - T3 - Trec)*1000 with omega = Ev - El
trec_ident = omega - T3 - c["E3"] / 1000.0
dev = np.max(np.abs(trec_ident - Trec))
print(f"[{MODEL}] N_p = {int(n_p)} of {int(c['ntot'][0])} streamed "
      f"({100.0 * n_p / float(c['ntot'][0]):.1f}% proton channel)")
print(f"identity |T_rec(ident) - T_rec(p3^2/2M)| max = {dev:.3e} GeV "
      f"(monochromatic beam + M_REC consistent)" if dev < 1e-9 else
      f"WARNING identity deviation {dev:.3e} GeV -- Ev not monochromatic or M_REC off")
em3 = (omega - T3 - Trec) * 1000.0               # [MeV] == c["E3"]
for name, x, unit in [("E_e'", El, "GeV"), ("omega", omega, "GeV"),
                      ("T_p3", T3, "GeV"), ("T_rec3", Trec * 1e3, "MeV"),
                      ("E_m3", em3, "MeV")]:
    print(f"  {name:7s} mean {np.mean(x):8.3f}  median {np.median(x):8.3f}  "
          f"p5-p95 [{np.percentile(x, 5):.3f}, {np.percentile(x, 95):.3f}] {unit}")

# ---- figure: the four E_m ingredients ---------------------------------------------
PANELS = [
    (r"$E_{e'}$  (GeV)",    El,         np.linspace(0.2, 2.4, 56),  False),
    (r"$\omega$  (GeV)",    omega,      np.linspace(0.0, 2.3, 56),  False),
    (r"$T_{p}$  (GeV)",     T3,         np.linspace(0.0, 2.4, 56),  False),
    (r"$T_{rec}$  (MeV)",   Trec * 1e3, np.linspace(0.0, 32.0, 65), True),
]

apply_style()
fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
for ax, (xlabel, x, edges, logy) in zip(axes, PANELS):
    cnt, _ = np.histogram(x, bins=edges)
    ax.stairs(cnt / (n_p * np.diff(edges)), edges, color=S.color(MODEL),
              linewidth=S.lw(MODEL), zorder=S.zorder(MODEL))
    style_axis(ax, title=xlabel, xlabel=xlabel, logx=False, logy=logy,
               ymin=None)
    ax.set_xlim(edges[0], edges[-1])
    if not logy:
        ax.set_ylim(0, None)
    ax.annotate(f"median {np.median(x):.3f}\nmean {np.mean(x):.3f}",
                xy=(0.97, 0.86), xycoords="axes fraction", ha="right",
                fontsize=FS_LEGEND - 2, color="0.4")
    ax.set_ylabel(r"d$N/$d$x\,/\,N_p$", fontsize=FS_LABEL)

fig.suptitle("$E_m$ components at stage 3 (pre-FSI primary proton) — "
             f"{S.label(MODEL)} (GEM26_22b_05)\n"
             r"$E_{m3} = \omega - T_p - T_{rec}$ ·"
             " proton channel, no cuts · per-$N_p$ normalization",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

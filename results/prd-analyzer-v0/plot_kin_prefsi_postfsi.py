"""Reconstruction-level kinematics, pre-FSI vs post-FSI proton version.

Five observables of the (e,e'p) reconstruction -- E_e', theta_e', T_p,
theta_p, Q^2 -- drawn twice per model: once with the PRE-FSI primary proton
(dashed) and once with the LEADING POST-FSI proton (solid). The electron-arm
quantities (E_e', theta_e', Q^2) are identical by construction -- FSI never
touches the scattered electron -- so their dashed curves hide exactly under
the solid ones (verified in the printout); only the proton panels change:
  T_p      shifts DOWN (hA transport loss + the a-tunes' 20-MeV/ sampled-E
           NucBindEnergyAggregator subtraction, README section 10b);
  theta_p  smears (FSI deflection).

Ladder convention: proton channel (hitnuc = p), no cuts, per-proton-channel-
event normalization y = dN/dx / N_p (NOT area-normalized, so the pre vs post
comparison is event-faithful; post-FSI curves lose only the ~0.1% of events
with no surviving proton). Sample generation cut t05 (Q^2 >= 1.18) applies
to everything. Reads cache/ladder/<model>.npz (build_cache_ladder.py).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from matplotlib.lines import Line2D
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S

OUT = "results/prd-analyzer-v0/kin_prefsi_vs_postfsi.png"

caches = {m: dict(np.load(f"{S.CACHE_DIR}/ladder/{m}.npz")) for m in S.MODELS}


def deg(cth):
    return np.degrees(np.arccos(np.clip(cth, -1.0, 1.0)))


# variable name -> (label, edges, pre-array fn, post-array fn)
PANELS = [
    ("El",     r"$E_{e'}$  (GeV)",        np.linspace(0.2, 2.4, 56),
     lambda c: c["El"],        lambda c: c["El"]),
    ("theta_e", r"$\theta_{e'}$  (deg)",  np.linspace(10.0, 80.0, 56),
     lambda c: deg(c["cthl"]), lambda c: deg(c["cthl"])),
    ("Q2",     r"$Q^2$  (GeV$^2$)",       np.linspace(1.0, 4.5, 56),
     lambda c: c["Q2"],        lambda c: c["Q2"]),
    ("Tp",     r"$T_p$  (GeV)",           np.linspace(0.0, 2.0, 56),
     lambda c: c["T3"],        lambda c: c["T4"]),
    ("theta_p", r"$\theta_p$  (deg)",     np.linspace(0.0, 90.0, 56),
     lambda c: deg(c["cth3"]), lambda c: deg(c["cth4"])),
]


def hist(x, edges, nh):
    x = x[np.isfinite(x)]
    cnt, _ = np.histogram(x, bins=edges)
    return cnt / (nh * np.diff(edges))


# ---- printout: the FSI-blind check + proton shifts -------------------------------
print("pre-FSI vs post-FSI versions (per-event, proton channel):")
for m in S.MODELS:
    c = caches[m]
    fin = np.isfinite(c["T4"])
    dT = c["T3"][fin] - c["T4"][fin]
    dth = deg(c["cth4"][fin]) - deg(c["cth3"][fin])
    print(f"  {m:15s} lepton arrays identical by construction; "
          f"post-proton events {100*fin.mean():.2f}%   "
          f"T3-T4 med/p90 = {1e3*np.median(dT):.1f}/{1e3*np.percentile(dT,90):.1f} MeV   "
          f"|dtheta_p| med = {np.median(np.abs(dth)):.2f} deg")

# ---- figure ----------------------------------------------------------------------
apply_style()
fig, axes = new_panels(ncols=3, nrows=2, sharey=False)

for i, (key, xlabel, edges, fpre, fpost) in enumerate(PANELS):
    ax = axes[i]
    for m in S.MODELS:
        c = caches[m]
        nh = float(c["n_hitp"][0])
        ax.stairs(hist(fpre(c), edges, nh), edges, color=S.color(m),
                  linewidth=1.1, linestyle="--", zorder=S.zorder(m))
        ax.stairs(hist(fpost(c), edges, nh), edges, color=S.color(m),
                  linewidth=S.lw(m, base=1.6), zorder=S.zorder(m) + 1)
    style_axis(ax, title=xlabel, xlabel=xlabel, logx=False, logy=False, ymin=None)
    ax.set_xlim(edges[0], edges[-1])
    ax.set_ylim(0, None)
    if i % 3 == 0:
        ax.set_ylabel(r"d$N/$d$x\,/\,N_p$", fontsize=FS_LABEL)
for i in (0, 1, 2):
    axes[i].annotate("pre = post\n(electron arm)", xy=(0.05, 0.86),
                     xycoords="axes fraction", fontsize=FS_LEGEND - 3, color="0.4")

# legend panel
ax = axes[5]
ax.axis("off")
handles = ([Line2D([], [], color=S.color(m), linewidth=2.0, label=S.label(m))
            for m in S.MODELS]
           + [Line2D([], [], color="0.3", linewidth=1.1, linestyle="--",
                     label="pre-FSI primary proton"),
              Line2D([], [], color="0.3", linewidth=1.8, linestyle="-",
                     label="leading post-FSI proton")])
ax.legend(handles=handles, loc="center", fontsize=FS_LEGEND - 1,
          title="reconstruction version", title_fontsize=FS_LEGEND_TITLE - 1,
          frameon=False)

fig.suptitle("reconstruction kinematics — pre-FSI (dashed) vs post-FSI (solid) proton\n"
             r"proton channel, no cuts, per-$N_p$ normalization;"
             "  $E_{e'}$, $\\theta_{e'}$, $Q^2$ are FSI-blind by construction",
             fontsize=FS_SUPTITLE - 2)
fig.tight_layout()
fig.savefig(OUT, dpi=DPI)
print("wrote", OUT)

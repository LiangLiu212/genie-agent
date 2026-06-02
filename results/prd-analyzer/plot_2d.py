"""2D missing energy vs missing momentum for the (e,e'p) selection, both stages, SF vs LFG.

2x2 grid over the t05 (Q²=1.28, E=2.445 GeV) GEM26 samples:
  row 1 = stage 1 (electron cut El & theta_e), row 2 = stage 2 (full coincidence).
  col 1 = LFG (GEM26_11a), col 2 = SF (GEM26_22a).
Each cell is a 2D histogram p_m (x) vs E_m (y) in the paper windows. Uses selection.py.
"""
import sys, glob
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import apply_style, new_panels, FS_LABEL, FS_TITLE, FS_SUPTITLE, FS_TICK
import selection as sel

SCRATCH = "/exp/dune/data/users/liangliu/prd_scratch/t05"

def collect(cfg):
    em, pm, s2 = [], [], []
    for f in sorted(glob.glob(f"{SCRATCH}/*GEM26_{cfg}_05_000*.gst.root")):
        ev = sel.load_events(f)
        m1 = sel.select_electron(ev)
        em.append(ev["E_miss"][m1]); pm.append(ev["p_miss"][m1])
        s2.append(sel.select(ev)[m1])
    return np.concatenate(pm), np.concatenate(em), np.concatenate(s2)

pmL, emL, s2L = collect("11a")
pmS, emS, s2S = collect("22a")

PBINS = np.linspace(0.0, 300.0, 25)   # p_m [MeV/c]
EBINS = np.linspace(0.0, 80.0, 21)    # E_m [MeV]
apply_style()
fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
fig.set_size_inches(13, 10)

allp = np.ones(len(emL), bool)
cells = [
    ("stage 1 · LFG", pmL, emL, np.ones(len(emL), bool)),
    ("stage 1 · SF",  pmS, emS, np.ones(len(emS), bool)),
    ("stage 2 · LFG", pmL, emL, s2L),
    ("stage 2 · SF",  pmS, emS, s2S),
]
for ax, (title, pm, em, mask) in zip(axes, cells):
    h = ax.hist2d(pm[mask], em[mask], bins=[PBINS, EBINS], cmap="viridis", cmin=1)
    ax.set_title(f"{title}   (N={int(mask.sum())})", fontsize=FS_TITLE)
    ax.set_xlabel(r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]", fontsize=FS_LABEL)
    ax.set_ylabel(r"E$_m$ = ω − T$_p$  [MeV]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    fig.colorbar(h[3], ax=ax, label="events / bin")

fig.suptitle("(e,e'p) 2D missing energy vs momentum — e⁻ on C12, Q²=1.28 (t05), SF vs LFG\n"
             "row 1 = stage 1 (electron cut),  row 2 = stage 2 (full coincidence)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer/missing_2d_e_vs_p.png"
fig.savefig(out, dpi=130)
print("wrote", out)

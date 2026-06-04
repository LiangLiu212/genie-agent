"""2D missing energy vs missing momentum for the (e,e'p) selection — 2 stages x 3 models.

From the XRootD-streamed cache (build_cache.py), C12 t05 (Q²=1.28, 2.445 GeV):
  rows = stage 1 (electron cut El & θ_e) / stage 2 (full coincidence);
  cols = LFG / SF / SuSAv2.
Each cell is a 2D histogram p_m (x) vs E_m (y) in the paper windows (raw counts, N per cell).
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer")
import numpy as np
from plot_style import apply_style, new_panels, FS_LABEL, FS_TITLE, FS_SUPTITLE, FS_TICK
import samples as S

PBINS = np.linspace(0.0, 300.0, 25)   # p_m [MeV/c]
EBINS = np.linspace(0.0, 80.0, 21)    # E_m [MeV]

data = {}
for m in S.MODELS:
    c = S.load_cache(m)
    data[m] = (c["p_miss"], c["E_miss"], c["stage2"].astype(bool))

apply_style()
fig, axes = new_panels(ncols=len(S.MODELS), nrows=2, sharey=False)
fig.set_size_inches(5.5 * len(S.MODELS), 10)

cells = []
for use_stage2, slabel in [(False, "stage 1"), (True, "stage 2")]:
    for m in S.MODELS:
        pm, em, s2 = data[m]
        mask = s2 if use_stage2 else np.ones(len(em), bool)
        cells.append((f"{slabel} · {S.label(m)}", pm, em, mask))

for ax, (title, pm, em, mask) in zip(axes, cells):
    h = ax.hist2d(pm[mask], em[mask], bins=[PBINS, EBINS], cmap="viridis", cmin=1)
    ax.set_title(f"{title}   (N={int(mask.sum())})", fontsize=FS_TITLE)
    ax.set_xlabel(r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]", fontsize=FS_LABEL)
    ax.set_ylabel(r"E$_m$ = ω − T$_p$  [MeV]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    fig.colorbar(h[3], ax=ax, label="events / bin")

models_str = ", ".join(S.label(m) for m in S.MODELS)
fig.suptitle(f"(e,e'p) 2D missing energy vs momentum — e⁻ on C12, Q²=1.28 (t05): {models_str}\n"
             "row 1 = stage 1 (electron cut),  row 2 = stage 2 (full coincidence)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer/missing_2d_e_vs_p.png"
fig.savefig(out, dpi=130)
print("wrote", out)

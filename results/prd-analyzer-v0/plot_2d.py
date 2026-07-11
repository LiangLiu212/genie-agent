"""2D missing energy vs missing momentum for the (e,e'p) selection — 3 stages x 5 models.

From the XRootD-streamed cache (build_cache.py), C12 t05 (Q²=1.28, 2.445 GeV):
  rows = stage 1 (electron cut El & θ_e) / stage 2.1 (+ T_p, θ_p free) / stage 2 (full);
  cols = the five models in samples.MODELS (LFG / SF / SuSAv2 / SF(2024)+UQEL / SF+UQEL).
Each cell is a 2D histogram p_m (x) vs E_m (y) in the paper windows (raw counts, N per cell).
"""
import sys
sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import apply_style, new_panels, FS_LABEL, FS_TITLE, FS_SUPTITLE, FS_TICK
import samples as S
import selection as sel

PBINS = np.linspace(0.0, 300.0, 25)   # p_m [MeV/c]
EBINS = np.linspace(0.0, 80.0, 21)    # E_m [MeV]

data = {}
for m in S.MODELS:
    c = S.load_cache(m)
    data[m] = (c["p_miss"], c["E_miss"], sel.cache_stage_masks(c))

STAGES = [("1", "stage 1"), ("2.1", "stage 2.1"), ("2", "stage 2")]

apply_style()
fig, axes = new_panels(ncols=len(S.MODELS), nrows=len(STAGES), sharey=False)
fig.set_size_inches(5.5 * len(S.MODELS), 5 * len(STAGES))

cells = []
for stage, slabel in STAGES:
    for m in S.MODELS:
        pm, em, masks = data[m]
        cells.append((f"{slabel} · {S.label(m)}", pm, em, masks[stage]))

for ax, (title, pm, em, mask) in zip(axes, cells):
    h = ax.hist2d(pm[mask], em[mask], bins=[PBINS, EBINS], cmap="viridis", cmin=1)
    ax.set_title(f"{title}   (N={int(mask.sum())})", fontsize=FS_TITLE)
    ax.set_xlabel(r"p$_m$ = |q⃗ − p⃗$_p$|  [MeV/c]", fontsize=FS_LABEL)
    ax.set_ylabel(r"E$_m$ = ω − T$_p$  [MeV]", fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    fig.colorbar(h[3], ax=ax, label="events / bin")

models_str = ", ".join(S.label(m) for m in S.MODELS)
fig.suptitle(f"(e,e'p) 2D missing energy vs momentum — e⁻ on C12, Q²=1.28 (t05): {models_str}\n"
             "row 1 = stage 1 (electron cut),  row 2 = stage 2.1 (+ T_p, θ_p free),  "
             "row 3 = stage 2 (full coincidence)",
             fontsize=FS_SUPTITLE)
fig.tight_layout()
out = "results/prd-analyzer-v0/missing_2d_e_vs_p.png"
fig.savefig(out, dpi=130)
print("wrote", out)

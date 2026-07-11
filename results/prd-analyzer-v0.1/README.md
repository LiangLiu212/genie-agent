# prd-analyzer v0.1 — convergence iteration

Active successor to [`../prd-analyzer-v0/`](../prd-analyzer-v0/README.md), the exploratory
phase of the (e,e′p) E91-013 replication (five QE-EM models at Q² = 1.28 GeV², HMS/SOS
acceptance, missing energy/momentum vs Dutta Figs 9/10). v0 holds the full narrative,
all exploratory figures, and the scripts that produced them; this directory converges
that work into the final analysis.

**Working convention**: scripts are pulled in from v0 one at a time as they converge,
with their internal `results/prd-analyzer-v0/...` paths updated to
`results/prd-analyzer-v0.1/...`. Every figure in this directory was produced by a
script in this directory.

## Contents

| file | provenance / what it does |
|---|---|
| `samples.py` | pulled from v0 (only `CACHE_DIR` changed) — 5-model registry, XRootD URLs, cache loader, plot roles |
| `plot_em_components_prefsi.py` → `em_components_prefsi.png`, `em_subtractions_prefsi.png` | **E_m budget at ladder stage 3 (pre-FSI primary proton), SF + UnifiedQEL only**. Fig 1: the four ingredients E_e′, ω = 2.445 − E_e′, T_p, and the ¹¹B recoil T_rec = p_m²/2M (slope break at ≈5 MeV = p_m ≈ 320 MeV/c, the SF mean-field→SRC boundary). Fig 2: the subtraction ladder — ω − T_p floors **razor-sharp at exactly 15.000 MeV** (the pke12_tot table's first E-block edge; it *is* the mass-based table axis, v0 §12), while ω − T_p − T_rec (= E_m3, Dutta's recoil-subtracted convention, peak 14.75 MeV) spills down to 3 MeV — below S_p = 15.96 — reproducing the v0 §10b1 `BindHitNucleon` T_rec distortion from the budget angle. Reads `cache/ladder/UnifiedQEL.npz`; validates the monochromatic beam + M_REC against the cache identity at runtime. |

## cache/

The XRootD-streamed selection cache built by v0's `build_cache*.py` (moved here intact —
gitignored, ~1.5 GB, regenerable from the grid gst on `/pnfs`):

- per-model `.npz` (`LFG`, `SF`, `SuSAv2`, `UnifiedQEL`, `UnifiedQEL2024`) — stage-1
  electron-arm selection;
- `superset/` — fixed 2M-event/model supersets; `acceptance/`, `q2window/`, `prefsi/`,
  `sd/`, `ladder/` — the derived per-study selections (see v0 README §Workflow for what
  each contains and which builder makes it).

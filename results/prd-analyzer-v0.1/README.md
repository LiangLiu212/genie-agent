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
| `plot_em_components_prefsi.py` → `em_{components,subtractions}_prefsi_{22b,33b}.png` | **E_m budget at ladder stage 3 (pre-FSI primary proton)**, one UnifiedQEL variant per run (argv `UnifiedQEL` \| `UnifiedQEL2024`). Fig 1: the four ingredients E_e′, ω, T_p, T_rec. Fig 2: the subtraction ladder ω − T_p vs ω − T_p − T_rec (= E_m3). Reads `cache/ladder/<model>.npz`; validates beam + M_REC against the cache identity at runtime. |
| `sf_unifiedqel_em_prefsi.md` | Study page, **22b** (SF + UnifiedQEL): ω − T_p floors razor-sharp at exactly 15.000 MeV (pke12_tot first E-block edge — the mass-based table axis, v0 §12); E_m3 over-subtracts by T_rec, 23.1 % below S_p (v0 §10b1). |
| `sf2024_unifiedqel_em_prefsi.md` | Study page, **33b** (SF(2024) + UnifiedQEL): ω − T_p reads the 2024 table back undistorted — ground-state quasiparticle line at 15.93–15.98 MeV ≈ S_p (v0 §10b2); E_m3 drags it ~0.8 MeV low, 39.9 % below S_p, 0.08 % **negative** (min −15.3 MeV). |

## cache/

The XRootD-streamed selection cache built by v0's `build_cache*.py` (moved here intact —
gitignored, ~1.5 GB, regenerable from the grid gst on `/pnfs`):

- per-model `.npz` (`LFG`, `SF`, `SuSAv2`, `UnifiedQEL`, `UnifiedQEL2024`) — stage-1
  electron-arm selection;
- `superset/` — fixed 2M-event/model supersets; `acceptance/`, `q2window/`, `prefsi/`,
  `sd/`, `ladder/` — the derived per-study selections (see v0 README §Workflow for what
  each contains and which builder makes it).

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

## cache/

The XRootD-streamed selection cache built by v0's `build_cache*.py` (moved here intact —
gitignored, ~1.5 GB, regenerable from the grid gst on `/pnfs`):

- per-model `.npz` (`LFG`, `SF`, `SuSAv2`, `UnifiedQEL`, `UnifiedQEL2024`) — stage-1
  electron-arm selection;
- `superset/` — fixed 2M-event/model supersets; `acceptance/`, `q2window/`, `prefsi/`,
  `sd/`, `ladder/` — the derived per-study selections (see v0 README §Workflow for what
  each contains and which builder makes it).

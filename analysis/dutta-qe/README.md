# dutta-qe — the Dutta E91-013 vs GENIE analysis, as a runnable project

A self-contained summary of the study written up in
[`results/prd-analyzer-v0.3/`](../../results/prd-analyzer-v0.3/README.md)
(selection and figures) and
[`results/normalization/README.md`](../../results/normalization/README.md)
(data conventions): electron–C12/Fe56 quasi-elastic events from the GENIE
full-EM t05 campaigns, selected in the Dutta Q² slice, projected onto
missing energy and missing momentum, and overlaid on the JLab Hall C
E91-013 (e,e′p) data (PRC figs 6/7/9/11). All code here is standalone —
nothing is imported from `results/template/`.

## The analysis in one paragraph

Selection: `qel && hitnuc==p && |Q²/1.28 − 1| ≤ 5%`, post-FSI proton = the
unique proton of exactly-one-proton (N_p = 1) events. Each event is placed
on the restored missing-energy axis `E_m + T_rec` at three stages (struck
nucleon in the record, pre-FSI primary proton, post-FSI proton) and both
projections are compared — on the occupancy scale (histograms
`Z·dN/dx/N_sel`, area = nucleon count, tables and data on their own
scales) and as survivor-normalized shapes (unit integral, FSI scale
divided out). The Dutta p_m data are signed-axis files carrying half the
density per side: they are folded (L+R summed) before any comparison, and
the E_m windows are matched to each dataset (Fe56 fig 7: E_m < 80 MeV;
C12 fig 6: the shell windows 10–25 ∪ 30–50 MeV). Only Q² = 1.28 files are
used; the Q² = 0.64 files are anomalous and excluded.

## Run it

```bash
# stage 0 — events -> cache/<target>/<tune>.npz  (pick one source)
pixi run python analysis/dutta-qe/build_cache.py --seed-from-v03   # instant
pixi run python analysis/dutta-qe/build_cache.py --stream --target C12 --max-files 20

# stage 1 — E_miss figures (ladder + survivor-normalized shape)
pixi run python analysis/dutta-qe/plot_emiss.py --target C12  --all-tunes
pixi run python analysis/dutta-qe/plot_emiss.py --target Fe56 --all-tunes

# stage 2 — p_miss figures (ladder + Dutta-units density + shape)
pixi run python analysis/dutta-qe/plot_pmiss.py --target C12  --all-tunes
pixi run python analysis/dutta-qe/plot_pmiss.py --target Fe56 --all-tunes

# stage 3 — strength integrals / survival table
pixi run python analysis/dutta-qe/summarize.py

# everything (seeds the cache if missing)
pixi run python analysis/dutta-qe/run_all.py
```

Figures and `summary.md` land in `out/`; caches in `cache/` (both
gitignored). `--stream` reads the grid gst files over XRootD and needs a
valid bearer token (`BEARER_TOKEN_FILE`; refresh with
`htgettoken -a htvaultprod.fnal.gov -i dune`). Both cache sources produce
the identical schema, so they are interchangeable per target/tune.

## Modules

| file | role |
|---|---|
| `config.py` | every constant: tunes, targets, Q² slice, windows, masses, paths |
| `events.py` | cache access, restored axis, window masks, histogram helpers |
| `sftable.py` | pke table parser (SpectralFunc format) + windowed marginals |
| `dutta.py` | figs 6/7/9/11 loaders with the resolved conventions |
| `build_cache.py` | stage 0: seed from v0.3 caches or stream gst over XRootD |
| `plot_emiss.py` | stage 1: E_m ladder + shape figures |
| `plot_pmiss.py` | stage 2: p_m ladder, Dutta-units density, shape figures |
| `summarize.py` | stage 3: strength integrals table → `out/summary.md` |
| `style.py` | the house plot style (copy of `results/template/plot_style.py`) |

## Expected numbers (occupancy scale, from the committed study)

- Fe56: I1(table, p panel) = 22.852, I(fig 7 folded) = 18.206
  (data/table = 0.80; 2×fig 7 ≡ fig 11 to 0.03 %); I4/I3 ≈ 0.38–0.42.
- C12: I1 = 4.533, I(fig 6 p+s folded) = 4.917 (data/table = 1.08);
  I4/I3(p panel) 0.41–0.60 — the shell windows expose the ΔT_p taxonomy.
- The |p_m| shapes are nearly FSI-invariant (ground-state measure); the
  E_m shapes separate the FSI models.

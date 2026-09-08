---
name: histdiag
description: Read 1D and 2D histograms as numbers, not pixels — text readouts (moments, quantiles, FWHM, chi2/KS, pull patterns, runs, coarse maps, profiles, heuristic hints) computed from the underlying counts with results/template/histdiag.py. Use whenever a histogram figure is produced or has to be interpreted, two distributions/tunes/samples are compared ("are these the same?", "how do they differ?", "shift or width change?"), a 2D correlation/profile/response histogram is inspected, or a ROOT TH1/TH2 needs reading. Never judge a histogram from its PNG alone.
---

# histdiag: text readouts of histograms

A rendered PNG hides the bin by bin structure and is read unreliably by the
model. `results/template/histdiag.py` prints a text report from the counts
(and returns the same numbers in a dict), so every statement about a
histogram rests on numbers that can be quoted and checked. Its module
docstring lists what each report contains.

## When to use

- **After saving any figure that shows a 1D or 2D histogram.** Run the matching
  readout on the same counts and keep it next to the PNG under the same stem:
  `results/<dir>/<stem>.png` gets `results/<dir>/<stem>.txt` (`save=`).
- **Before writing any sentence about how two histograms differ** (tunes,
  settings, pre/post FSI, data vs MC). Use `compare1d` / `compare2d`, quote
  the numbers behind the hint (chi2/ndf, run sigma, quantile shifts).
- **When the user points at a histogram PNG.** If the data behind it is
  reachable (npz cache, CSV dump, gst/ROOT file, the generator script under
  `results/template/`), rebuild the histogram from the data and read the
  report. Fall back to viewing the PNG only when the data is not reachable,
  and say so.

## Rules

- **Feed raw counts**, before any occupancy / area / density scaling, so the
  Poisson errors are right. The ladder scripts build `np.histogram` counts and
  then scale them (`Z * cnt / (n_sel * binw)`); pass the `cnt`. For weighted
  or already scaled histograms pass `errors=` (sqrt of the sum of w^2 per bin,
  scaled the same way).
- **The second histogram is the reference**: ratios are first/second, pulls are
  positive where the first is above; "shape" quantities scale the reference to
  the first's integral, so they isolate shape from normalization.
- **2D arrays are `H[ix, iy]`** (`numpy.histogram2d` and uproot `to_numpy()`
  convention). `describe2d(..., diagonal=True)` only when y measures x.
- **Hints are heuristics.** Report the numbers that support them, never the
  hint text alone; the run table, regions and bin table are the evidence.
- Thin statistics: coarsen first with `rebin1d` / `rebin2d` (errors combine in
  quadrature) rather than reading noise.
- Run through pixi (`pixi run python ...`); scipy is in the env, so the chi2
  p-values are exact (a Wilson-Hilferty fallback exists without it).

## Using the helper

```python
import sys; sys.path.insert(0, "results/template")
import numpy as np, histdiag as hd

# numpy histograms
c1, _ = np.histogram(a, edges); c2, _ = np.histogram(b, edges)
r = hd.compare1d(c1, c2, edges, labels=("lfon", "lfnever"), xname="E_m",
                 save="results/<dir>/<stem>.txt")
r["hints"], r["chi2_shape"], r["runs"]        # the same numbers, programmatically

H1, xe, ye = np.histogram2d(x1, y1, bins=[xedges, yedges])
H2, _, _ = np.histogram2d(x2, y2, bins=[xe, ye])
hd.describe2d(H2, xe, ye, xname="|p_m|", yname="E_m")
hd.compare2d(H1, H2, xe, ye, labels=("A", "B"), xname="|p_m|", yname="E_m")

# ROOT histograms through uproot
with uproot.open(path) as f:
    counts, edges = f["h1"].to_numpy(); errors = f["h1"].errors()
    H, xe, ye = f["h2"].to_numpy()
hd.describe1d(counts, edges, errors=errors, name="h1", table=True)

# ladder caches (results/prd-analyzer-v1.0/cache/ladder_c12/<tune>.npz):
# reuse the generator's edges/windows so the readout is the same object as the panel
import make_emiss_ladder_q2cut as em      # needs results/prd-analyzer-v0 on sys.path too
cnt, _ = np.histogram(E4r[p4 < em.PM_MAX], bins=em.EDGES)
```

## Reading the report

- `pull shape` pattern `---+++` (or `+++---`) across the peak = a shift;
  `-+-` = narrower, `+-+` = broader; one run = a local bump or deficit;
  no run but |norm sigma| > 3 = a normalization only difference.
- `runs`: `*` marks combined |sigma| >= 3; "[fewer than 10 entries ...]" means
  the Gaussian pull is not reliable there.
- `quantiles A minus B` all about equal = rigid shift; all growing with the
  quantile = a multiplicative scale (the hint says which).
- `[flat topped: ...]`: the peak position is not meaningful, read the regions.
- 2D: the column normalized map is the ridge (where y sits at each x); the
  profile gives `<y>(x)` with a straight line fit and a curvature verdict; the
  "ratio trend along x / y" says whether a difference is a flat normalization
  or grows along an axis; "most significant coarse cells" localize it.
- `caution: slices ... in the first or last bin`: the axis range clips the
  distribution there, so `<y>` and the curvature are biased in those slices.

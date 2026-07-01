---
name: nuisance-paper-figure
description: Build a MicroBooNE data/MC comparison paper figure (the house figure*+overpic+chi2-table style under results/neutrino-theory-experiments/) from NUISANCE .comp.root files via INCLInterface Analysis.GENIE().paper_plot, then compile the final paper PDF with tectonic. Use when the user wants to overlay GENIE Ar tunes on the MicroBooNE CC1Mu1p TKI (delta p_T, delta alpha_T) / CC1MuNp (p_mu, p_p) data, add or regenerate a neutrino-theory comparison figure (axial form factor / FSI / ground state / reference tune), or produce paper/<name>_combined.pdf.
---

# NUISANCE MicroBooNE paper figure

End-to-end: NUISANCE `.comp.root` inputs -> `Analysis.GENIE().paper_plot` ->
6 per-panel PDFs/PNGs -> a `figure*` + chi2-table LaTeX fragment -> the compiled
`paper/<name>_combined.pdf`. Outputs land in
`results/neutrino-theory-experiments/`. Each figure compares GENIE Ar
configurations (and/or the AR23 / MicroBooNE reference tunes) against the
MicroBooNE CC1Mu1p TKI + CC1MuNp data.

Existing figures that follow this exact pattern (use as templates):
`axial_form_factor_combined.tex` (F_A: LQCD vs Deu), `final_state_interaction_combined.tex`
(hA2018 vs INCL), `nuclear_model_combined.tex` (SF vs LFG ground state),
`reference_tune_combined.tex` (best config vs AR23/MicroBooNE).

## Data + code paths

- **NUISANCE inputs:** `/exp/dune/data/users/liangliu/runarea/INCL/nuisance/<tune>.comp.root`
  (one per tune; e.g. `LFG26_24a_00_000.comp.root`, `AR23_20i_00_001.comp.root`,
  `G18_10a_02_12a.comp.root`). Tune-name decoding: see the `inclinterface-paper-plot-run`
  / `incl-tune-naming-convention` memories.
- **Analysis code:** `/exp/dune/app/users/liangliu/GENIEINCLXX/INCLInterface`
  - `Analysis/GENIE.py` -> `GENIE().paper_plot(samples, ps, path)` (calls `Plot2D` + `PlotAR23`)
  - `Analysis/src/PaperTest.py` -> `PaperTest` (loads hists, draws panels) + `save_subplots`
- **chi2 source:** `results/neutrino-theory-experiments/chisq_table.tex` — the master
  `tab:chisq` already lists chi2/ndf (p-value) for all 8 theory configs + `MicroBooNE Tune`
  + `AR23`, columns `2D dpT-daT / dpT / daT / p_mu / p_p`. REUSE these rows; don't recompute.
- **Environment:** the **genie-dev pixi** env, run headless. It needs `pandas`, `vector`,
  `hist` on top of numpy/matplotlib/uproot (already added). Always `MPLBACKEND=Agg`.

## Panel map (left column of the 6x2 figure -> a..f)

`a` = 2D dpT (daT < 45 deg) · `b` = 2D dpT (135 < daT < 180) · `c` = dpT ·
`d` = daT · `e` = p_mu · `f` = p_p.

## Step 1 — generate the per-panel figures

Write a driver in the job tmp dir (one-off; not committed — see
`prefer-skill-over-python-for-oneoff`). Edit `PREFIX_NAME` and `ps`; `samples`
is a label bank (every tune in `ps` must have a label). Run with
`MPLBACKEND=Agg pixi run python <driver>.py` from `genie-dev`.

```python
import os, sys
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib; matplotlib.use("Agg")

INCL = "/exp/dune/app/users/liangliu/GENIEINCLXX/INCLInterface"
sys.path.insert(0, INCL)
import Analysis
from Analysis.src import PaperTest as PT

PATH = "/exp/dune/data/users/liangliu/runarea/INCL/nuisance"
OUT  = "/exp/dune/data/users/liangliu/genie-dev/results/neutrino-theory-experiments"
PREFIX_NAME = "reference_tune"          # <-- figure theme; panels become <PREFIX>_{a..f}

samples = {"samples": {                 # label bank (LaTeX); pick any subset via ps
    "LFG26_14a_00_000": r"N/LFG + $F_A^{\rm Deu}$ + hA2018",
    "LFG26_14b_00_000": r"N/LFG + $F_A^{\rm Deu}$ + INCL",
    "LFG26_24a_00_000": r"N/LFG + $F_A^{\rm LQCD}$ + hA2018",
    "LFG26_24b_00_000": r"N/LFG + $F_A^{\rm LQCD}$ + INCL",
    "AR23_20i_00_001":  "AR23",
    "G18_10a_02_12a":   "MicroBooNE Tune",
    "SF26_11a_00_000":  r"SF + $F_A^{\rm Deu}$ + hA2018",
    "SF26_11b_00_000":  r"SF + $F_A^{\rm Deu}$ + INCL",
    "SF26_21a_00_000":  r"SF + $F_A^{\rm LQCD}$ + hA2018",
    "SF26_21b_00_000":  r"SF + $F_A^{\rm LQCD}$ + INCL",
}}
ps = ["LFG26_24a_00_000", "AR23_20i_00_001", "G18_10a_02_12a"]   # <-- tunes to overlay

os.makedirs(OUT, exist_ok=True)
genie = Analysis.GENIE()
genie.com_output_type = ""
genie.paper_plot(samples, ps, PATH)     # draws the 6x2 fig; also writes its own copies
com = genie.com                         # last Plot2D fig persists here (.fig/.axs)

# (only if AR23/MicroBooNE are in ps) paper_plot dashes them in the 1D panels c-f
# but NOT in the 2D panels a,b -- dash them there too for consistency.
for r in (0, 1):
    for line in com.axs[r, 0].get_lines():
        if line.get_label() in ("AR23", "MicroBooNE Tune"):
            line.set_linestyle("--")

# House style: legend on panel (a) only; strip the legends from (b)-(f).
for r in range(1, 6):
    leg = com.axs[r, 0].get_legend()
    if leg is not None:
        leg.remove()
com.axs[0, 0].legend(fontsize=13)       # refresh (a) so its handles match the dashing

prefix = os.path.join(OUT, PREFIX_NAME)
PT.save_subplots(com.fig, com.axs, prefix=prefix, fmt="png")   # <prefix>_{a..f}.png
PT.save_subplots(com.fig, com.axs, prefix=prefix, fmt="pdf")   # <prefix>_{a..f}.pdf
# (com.fig.savefig(prefix+"_combined.png/.pdf") gives a full-figure preview only --
#  the house figure set does NOT include a _combined raster; drop it before committing.)
```

Colors are matplotlib defaults in `ps` order: 1st = blue, 2nd = orange, 3rd =
green; data = black points. AR23 and the MicroBooNE tune always render dashed.
`Read` `<prefix>_a.png` and `<prefix>_c.png` to confirm: legend only on (a),
references dashed everywhere.

## Step 2 — the house-style LaTeX fragment

Create `results/neutrino-theory-experiments/<PREFIX>_combined.tex`. It is a
**fragment** (no `\documentclass`), meant to be `\input` into the paper. Copy
`reference_tune_combined.tex` and edit the panel keys, caption, and table rows.
Skeleton:

```latex
\begin{figure*}[htbp]
\centering
% row 1: a b c  (each in a 0.3\textwidth minipage)
\begin{minipage}{0.3\textwidth}
\begin{overpic}[width=\linewidth]{<PREFIX>_a.pdf}\put(24,56){\footnotesize\text{(a)}}\end{overpic}
\end{minipage}
% ... b, c ...
\vspace{0.5cm}
% row 2: d e f  (same pattern)
\caption{... blue = <config1>, orange = <config2>, ... data (black points).
Panels (a) dpT for daT<45deg, (b) for 135<daT<180; (c) dpT; (d) daT; (e) p_mu; (f) p_p. ...}
\label{fig:<PREFIX>}
\end{figure*}

\begin{table}[htbp]
\caption{$\chi^2/{\rm ndf}$ ($p$-value) relative to MicroBooNE data for Fig.~\ref{fig:<PREFIX>}.}
\label{tab:chisq_<PREFIX>}
\centering
\resizebox{\columnwidth}{!}{
\begin{tabular}{lrrrrr}
\toprule
Configuration & $\delta p_T$ vs. $\delta \alpha_T$ & $\delta p_T$ & $\delta \alpha_T$ & $p_{\mu}$ & $p_p$ \\
\midrule
<config row, chi2/ndf (p) copied from chisq_table.tex> \\
\bottomrule
\end{tabular}}
\end{table}
```

`\put(24,56)` places the (a)-(f) label top-left; keep it identical to the other
figures. The table columns map to the observables: `2D dpT-daT / dpT / daT /
p_mu / p_p`. Pull each row verbatim from `chisq_table.tex`.

## Step 3 — compile the final paper PDF

The fragment compiles inside a minimal `article` wrapper (loads `amsmath` for
`\text`, `graphicx`, `overpic`, `booktabs`; `\graphicspath` -> the figures dir).
Write the wrapper to job tmp, build with tectonic (see `compile-latex-via-tectonic`),
then copy the result to `paper/<PREFIX>_combined.pdf`:

```latex
% _build_<PREFIX>.tex  (transient, in job tmp)
\documentclass[11pt]{article}
\usepackage[margin=0.6in]{geometry}
\usepackage{amsmath}\usepackage{graphicx}\usepackage{overpic}\usepackage{booktabs}
\graphicspath{{/exp/dune/data/users/liangliu/genie-dev/results/neutrino-theory-experiments/}}
\pagestyle{empty}
\begin{document}
\input{/exp/dune/data/users/liangliu/genie-dev/results/neutrino-theory-experiments/<PREFIX>_combined.tex}
\end{document}
```

```bash
cd <job tmp>
pixi run --manifest-path /exp/dune/data/users/liangliu/texenv/pixi.toml \
         tectonic --outdir . _build_<PREFIX>.tex
cp _build_<PREFIX>.pdf \
   /exp/dune/data/users/liangliu/genie-dev/results/neutrino-theory-experiments/paper/<PREFIX>_combined.pdf
```

`Read` `paper/<PREFIX>_combined.pdf` (page 1) to verify it renders like the other
`paper/*_combined.pdf`: 6-panel full-width figure, legend only on (a), the chi2
table below.

## Committed figure set (per theme)

Exactly these, under `results/neutrino-theory-experiments/`:
`<PREFIX>_{a..f}.pdf`, `<PREFIX>_{a..f}.png`, `<PREFIX>_combined.tex`,
`paper/<PREFIX>_combined.pdf`. NOT the `<PREFIX>_combined.{pdf,png}` matplotlib
preview, and never touch another theme's files. PDF re-runs only differ in
metadata, so `git checkout` panels whose content is unchanged to keep diffs clean.

## Gotchas

- All 8 theory configs + the 2 reference tunes already have chi2 in `chisq_table.tex`
  — only recompute if you add a brand-new tune (paper_plot stores per-observable
  chi2/ndf in `genie.com.chisq[s]`/`.ndf[s]`; order is `[2D, dpT, daT, p_mu, p_p]`
  after `Plot2D`, with `PlotAR23` appending two extra entries afterward).
- A tune missing its `.comp.root` raises in `_load_hist`; confirm every `ps` entry exists.
- The 2D panels a,b draw all curves solid out of the box — the linestyle loop above
  is what makes references dashed there. Skip it for 2-config model-variation figures.
- `genie.com.fig`/`.axs` is the `Plot2D` 6x2 figure (left column = a..f); the separate
  `PlotAR23` 1x2 figure is not stored.

---
name: plot-style
description: Apply the user's personal matplotlib plotting style to result figures. Use whenever the user asks to "use my personal/usual style", "plot in my style", make a figure "look like the others", or produce a results plot meant to match results/spline_q2cut.png. Covers fonts, log scales, colors, multi-panel layout, and save conventions.
---

# Personal plot style

The canonical look for result figures (see `results/spline_q2cut.png`). When the
user asks to plot "in my style", follow these rules. The helper module
`results/template/plot_style.py` encodes them — prefer importing it over
re-typing constants, but the rules below are the source of truth if you hand-roll.

## The rules

**Backend** — always headless: `matplotlib.use("Agg")` before importing pyplot.
Never assume a display.

**Fonts (points)** — large and readable:
- suptitle **18**, panel title **16**, axis labels **16**
- legend title **13**, legend text **12**, tick labels **12**

**Scales** — log-log by default (`set_xscale("log")`, `set_yscale("log")`).
These are cross-section / spline figures spanning many decades.

**Log-axis floor** — clamp non-positive y to `FLOOR = 1e-12` so zeros render on a
log axis; set `ax.set_ylim(FLOOR, None)`. Note in the caption that clamped values
are not physical.

**Grid** — `ax.grid(True, which="both", ls=":", alpha=0.4)` (dotted, both major
and minor, faint).

**Colors** — matplotlib default cycle `C0, C1, C2, C3, ...` in series order; keep
the same color for the same series across panels.

**Layout** — one panel per facet (e.g. per target), `sharey=True`, panel size
`5x5` inches each, `fig.tight_layout()`. Legend on the first (leftmost) panel.

**Markers** — `"-o"`, `ms=3` (line with small dots on the actual knots).

**Output** — save PNG at `dpi=130`. Result figures live under `results/`; their
generator scripts / style live under `results/template/`.

## Using the helper

```python
import sys; sys.path.insert(0, "results/template")
from plot_style import apply_style, new_panels, style_axis, COLORS, FLOOR, \
    FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI

apply_style()
fig, axes = new_panels(ncols=3)               # 5x5 per panel, sharey
for ax, facet in zip(axes, facets):
    for i, (label, E, X) in enumerate(series):
        ax.plot(E, [max(x, FLOOR) for x in X], "-o", ms=3,
                color=COLORS[i % len(COLORS)], label=label)
    style_axis(ax, title=facet, xlabel="E [GeV]")   # log-log, grid, ticks, ylim
axes[0].set_ylabel("xsec  [GENIE units]", fontsize=FS_LABEL)
axes[0].legend(title="<param> [unit]", fontsize=FS_LEGEND,
               title_fontsize=FS_LEGEND_TITLE)
fig.suptitle("<title>", fontsize=FS_SUPTITLE)
fig.tight_layout()
fig.savefig("results/<name>.png", dpi=DPI)
```

Run via `pixi run python <script>` (matplotlib is in the pixi env). After saving,
`Read` the PNG to display it and visually confirm before committing.

## Adjusting the style

If the user tweaks the look ("make titles bigger", "use a different floor"),
update the constants in `plot_style.py` AND the matching rule above so the two
stay in sync — they are meant to describe the same style.

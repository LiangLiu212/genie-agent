"""User's personal matplotlib plot style for genie-agent result figures.

Encodes the look of results/spline_q2cut.png. See the plot-style skill
(.claude/skills/plot-style/SKILL.md) for the written guideline. Import and call
``apply_style()`` once, build a panel grid with ``new_panels()``, and finish
each axis with ``style_axis()``.

The constants here and the rules in the skill describe the SAME style; if you
change one, change the other.
"""

import matplotlib

# Font sizes (points)
FS_SUPTITLE = 18
FS_TITLE = 16
FS_LABEL = 16
FS_LEGEND_TITLE = 13
FS_LEGEND = 12
FS_TICK = 12

# Figure / output defaults
PANEL_SIZE = (5, 5)      # width, height per panel (inches)
DPI = 130

# Log-axis floor: clamp non-positive values so log scales render.
FLOOR = 1e-12

# Default color cycle (matplotlib C0..C5; same series -> same color across panels).
COLORS = ["C0", "C1", "C2", "C3", "C4", "C5"]


def apply_style():
    """Force a non-interactive backend (headless-safe). Call before pyplot use."""
    matplotlib.use("Agg")


def new_panels(ncols=3, nrows=1, sharey=True):
    """Create a figure + axes grid sized from PANEL_SIZE.

    Returns (fig, axes) where axes is always a flat list.
    """
    import matplotlib.pyplot as plt
    w, h = PANEL_SIZE
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(w * ncols, h * nrows),
                             sharey=sharey)
    try:
        axes = list(axes.ravel())
    except AttributeError:        # single Axes
        axes = [axes]
    return fig, axes


def style_axis(ax, title=None, xlabel=None, ylabel=None,
               logx=False, logy=False, ymin=FLOOR):
    """Apply the shared per-axis styling (scales, fonts, grid, ticks, ylim)."""
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    if title is not None:
        ax.set_title(title, fontsize=FS_TITLE)
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontsize=FS_LABEL)
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=FS_LABEL)
    ax.tick_params(labelsize=FS_TICK)
    ax.grid(True, which="both", ls=":", alpha=0.4)
    if logy and ymin is not None:
        ax.set_ylim(ymin, None)
    return ax

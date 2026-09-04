"""GEM26_44b_05_000 EMQE C12 splines: old convention vs the new vertex, local
energy on / never.

Reads GENIE gmkspl spline XMLs (knots of E [GeV] vs xsec [1e-38 cm^2]) and
draws sigma(E) for the e-p and e-n QEL-EM splines, plus the ratios to the old
spline; prints the values interpolated at E = 2.445 GeV.

Usage:
  pixi run python results/template/make_spline_44b_locE.py \
      --old  <07-31 spline.xml> --on <locE-on spline.xml> --never <locE-never spline.xml>
Writes results/prd-analyzer-v1.0/spline_gem26_44b_locE.png
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis, FS_LABEL,
                        FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/prd-analyzer-v1.0/spline_gem26_44b_locE.png"
E_REF = 2.445


def read_splines(path):
    """-> {spline name: (E [GeV], xsec [1e-38 cm2])}"""
    out = {}
    for sp in ET.parse(path).getroot().iter("spline"):
        E, x = [], []
        for k in sp.iter("knot"):
            E.append(float(k.find("E").text))
            x.append(float(k.find("xsec").text))
        out[sp.get("name")] = (np.array(E), np.array(x))
    return out


def short(name):
    return "e-p" if "nucl:1000060120;tgt:1000060120;N:2212" in name or ";N:2212" in name else \
           "e-n" if ";N:2112" in name else name


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--on", required=True)
    ap.add_argument("--never", required=True)
    args = ap.parse_args()
    series = [("old chain (2026-07-31)", args.old, "C0", "-"),
              ("new vertex, local energy on", args.on, "C3", "-"),
              ("new vertex, never", args.never, "C2", "--")]
    data = {lab: read_splines(p) for lab, p, _, _ in series}
    names = sorted(next(iter(data.values())).keys())
    print("splines:", [short(n) for n in names])

    apply_style()
    fig, axes = new_panels(ncols=2, nrows=2, sharey=False)
    for j, name in enumerate(names):
        ax, axr = axes[j], axes[j + 2]
        E0, x0 = data[series[0][0]][name]
        for lab, _, color, ls in series:
            E, x = data[lab][name]
            ax.plot(E, x, ls, marker="o", ms=3, color=color, label=lab)
            if lab != series[0][0]:
                x0i = np.interp(E, E0, x0)
                ok = x0i > 0
                axr.plot(E[ok], x[ok] / x0i[ok], ls, marker="o", ms=3, color=color, label=lab)
            v = np.interp(E_REF, E, x)
            print(f"  {short(name)}  {lab:30s}  sigma({E_REF} GeV) = {v:.4e} x1e-38 cm2"
                  + ("" if lab == series[0][0] else
                     f"   ratio to old {v / np.interp(E_REF, E0, x0):.4f}"))
        axr.axhline(1.0, color="0.5", ls=":", lw=1.0)
        style_axis(ax, title=f"QEL-EM {short(name)}: $\\sigma(E)$", xlabel=None,
                   logx=False, logy=True, ymin=None)
        style_axis(axr, title=f"{short(name)}: ratio to the old spline",
                   xlabel=r"$E_e$  [GeV]", logx=False, logy=False, ymin=None)
        ax.axvline(E_REF, color="0.5", ls=":", lw=1.0)
        axr.axvline(E_REF, color="0.5", ls=":", lw=1.0)
        axr.set_ylim(0.6, 1.1)
    axes[0].set_ylabel(r"$\sigma$  [10$^{-38}$ cm$^2$]", fontsize=FS_LABEL)
    axes[2].set_ylabel("ratio", fontsize=FS_LABEL)
    axes[0].legend(fontsize=FS_LEGEND - 2, title="GEM26_44b_05_000, gmkspl -n 30 -e 3",
                   title_fontsize=FS_LEGEND_TITLE - 2, loc="lower right")
    fig.suptitle("GEM26_44b_05_000 EMQE splines, e$^-$ on C12: old chain vs new vertex\n"
                 "(local energy on / never); dotted: E = 2.445 GeV",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    fig.savefig(OUT, dpi=DPI)
    print("wrote", OUT)

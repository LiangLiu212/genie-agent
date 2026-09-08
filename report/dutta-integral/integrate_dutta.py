"""Integrate the Dutta E91-013 (e,e'p) author data over E_miss and p_miss.

Data: the 14 files in data/Dipingkar-dutta-data-prc_figs/ (PRC figs 6, 7,
9, 11). Columns, per the author's description:
  figs 6/7:   Pm (MeV/c), S(Pm) (MeV^-3), Err_Pm (MeV/c), Err_Spm (MeV^-3)
  figs 9/11:  Em (MeV),   S(Em) (MeV^-1), Err_Em (MeV),   Err_Sem (MeV^-1)
S(Pm) and S(Em) are the y-axis quantities of the figures: S(Pm) is S^D
integrated over the panel's E_m range (10-25 MeV fig 6 top, 30-50 MeV fig 6
bottom, 0-80 MeV fig 7); S(Em) is S^D integrated over p_m from -300 to
+300 MeV/c. Err_Pm / Err_Em (column 3) is 0.5% of x in every file (sign
follows x in most files, positive magnitude in the Q^2 = 3.25 files and in
fig7_q1p2 row 1); it does not enter the integrals. Column 4 is the
statistical error on S and is the only error propagated here.

Convention (author-confirmed for fig 9: the C12 count is 3.04, i.e. HALF of
the plain sum  Sum S(Em) dEm = 6.08): the signed p_m axis counts each |p_m|
twice. S(Em) was formed by integrating 4 pi p_m^2 S^D over p_m from -300 to
+300 MeV/c, and the p_m files carry the full |p_m| density on each side. So

  E_m spectra (figs 9, 11):
      plotted sum = Sum_i S(Em)_i dE_i        (as plotted; = 2 N)
      N           = plotted sum / 2           nucleons in the window
      Grid: 16 bins, centres 2.5..77.5 MeV, width 5 MeV, edges 0..80.

  p_m distributions (figs 6, 7):
      N           = 4 pi Sum_{p>0} S(Pm)_i p_i^2 dp_i   positive half only
                    (the files are exactly left-right symmetrized; summing
                    both sides would double count, like the plotted E_m sum)
      plotted sum = Sum_i S(Pm)_i dp_i over the signed axis (the quantity the
                    paper's rescale-to-Q^2 = 1.8 convention equalizes)
      Grid: 16 signed bins, centres -300..+300 MeV/c, width 40 MeV/c, so
      |p_m| edges 0..320.

Consistency: N(fig 7, Q^2 = 1.28) = 9.103 and N(fig 11) = 9.100 -- the two
projections of the same Fe56 S^D agree to 0.03%. Both N are RAW distorted
strengths, about T * Z / f_corr with the paper's Table III transparencies
and PWIA correlation factors (C12: 0.60 * 6 / 1.11 = 3.24; Fe56:
0.44 * 26 / 1.26 = 9.08, taking the IPSM window strength as Z) -- there is
no renormalization to full occupancy. The script prints this expectation
next to the Q^2 = 1.28 E_m results.

Windows (--em-window / --pm-window) clip partial bins exactly by the
overlapping width fraction; the p^2 weight uses the bin centre (rectangle
rule on the native grid). Errors are the stat-only column 4 in quadrature --
they understate the published bars (report/dutta-e91013-figures.md, section
5); no scale factor is applied.

Usage (from the repo root):
  pixi run python report/dutta-integral/integrate_dutta.py
  pixi run python report/dutta-integral/integrate_dutta.py --em-window 10 25
  pixi run python report/dutta-integral/integrate_dutta.py --pm-window 0 200 \
      --files fig6_top_q1p2 fig6_bot_q1p2 --csv out.csv
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "data" / "Dipingkar-dutta-data-prc_figs"

DE_MEV = 5.0      # E_m bin width, figs 9/11
DP_MEVC = 40.0    # p_m bin width, figs 6/7

# every file, in figure order: stem -> (nucleus, kind, range the author
# already integrated over -- E_m [MeV] for the p_m files, p_m [MeV/c] for the
# E_m files -- Q^2 [(GeV/c)^2], caveat)
FILES = {
    "fig6_top_q0p6": ("C12", "pm", (10, 25), 0.64, "anomalous (x1.3 high) -- exclude"),
    "fig6_top_q1p2": ("C12", "pm", (10, 25), 1.28, ""),
    "fig6_top_q1p8": ("C12", "pm", (10, 25), 1.8, "rescale reference"),
    "fig6_top_q3p2": ("C12", "pm", (10, 25), 3.25, ""),
    "fig6_bot_q0p6": ("C12", "pm", (30, 50), 0.64, "anomalous (x1.3 high) -- exclude"),
    "fig6_bot_q1p2": ("C12", "pm", (30, 50), 1.28, ""),
    "fig6_bot_q1p8": ("C12", "pm", (30, 50), 1.8, "rescale reference"),
    "fig6_bot_q3p2": ("C12", "pm", (30, 50), 3.25, ""),
    "fig7_q0p6": ("Fe56", "pm", (0, 80), 0.64, ""),
    "fig7_q1p2": ("Fe56", "pm", (0, 80), 1.28, ""),
    "fig7_q1p8": ("Fe56", "pm", (0, 80), 1.8, "rescale reference"),
    "fig7_q3p2": ("Fe56", "pm", (0, 80), 3.25, ""),
    "fig9_q1p2": ("C12", "em", (-300, 300), 1.28, "raw distorted S^D (N ~ T Z / f_corr)"),
    "fig11_q1p2": ("Fe56", "em", (-300, 300), 1.28, "raw distorted S^D (N ~ T Z / f_corr)"),
}

# Paper Table III transparency at Q^2 = 1.28 (stat error) and the PWIA
# correlation factor f_corr, per nucleus -- for the raw-strength expectation
# T * Z / f_corr printed next to the full-window E_m results.
TRANSPARENCY_Q1P28 = {"C12": (0.60, 0.02, 6, 1.11), "Fe56": (0.44, 0.01, 26, 1.26)}


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def bin_overlap(centres, width, lo, hi):
    """Fraction of each bin [c - w/2, c + w/2) inside [lo, hi]."""
    left = centres - width / 2.0
    right = centres + width / 2.0
    ov = np.clip(np.minimum(right, hi) - np.maximum(left, lo), 0.0, width)
    return ov / width


def integrate_em(x, y, e, window):
    """E_m file: plotted sum  Sum S dE  over the window, and N = sum / 2."""
    w = bin_overlap(x, DE_MEV, *window) * DE_MEV
    S = float((y * w).sum())
    dS = float(np.sqrt(((e * w) ** 2).sum()))
    return {"N": S / 2.0, "dN": dS / 2.0, "plotted": S, "dplotted": dS}


def integrate_pm(x, y, e, window):
    """p_m file: N = 4 pi Sum_{p>0} S p^2 dp over |p_m| in the window, and
    the plotted 1D sum  Sum S dp  over the signed axis."""
    ax = np.abs(x)
    w = bin_overlap(ax, DP_MEVC, *window) * DP_MEVC     # clipped width per bin
    pos = x > 0
    k = 4.0 * np.pi * ax ** 2 * w
    N = float((y[pos] * k[pos]).sum())
    dN = float(np.sqrt(((e[pos] * k[pos]) ** 2).sum()))
    S = float((y * w).sum())
    dS = float(np.sqrt(((e * w) ** 2).sum()))
    return {"N": N, "dN": dN, "plotted": S, "dplotted": dS}


def check_symmetry(stem, x, y):
    """The p_m files are documented as exactly L-R symmetrized; warn if not
    (N is then the positive half only, not the |p_m| density)."""
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    if not (np.allclose(xs, -xs[::-1]) and np.allclose(ys, ys[::-1])):
        print(f"warning: {stem} is not left-right symmetric; N uses the "
              "positive half only", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("--files", nargs="+", metavar="STEM",
                    help="file stems to integrate (default: all 14)")
    ap.add_argument("--em-window", nargs=2, type=float, default=(0.0, 80.0),
                    metavar=("LO", "HI"),
                    help="E_m window [MeV] for figs 9/11 (default 0 80)")
    ap.add_argument("--pm-window", nargs=2, type=float, default=(0.0, 320.0),
                    metavar=("LO", "HI"),
                    help="|p_m| window [MeV/c] for figs 6/7 (default 0 320)")
    ap.add_argument("--csv", metavar="PATH", help="also write a CSV table")
    args = ap.parse_args()

    stems = args.files or list(FILES)
    unknown = [s for s in stems if s not in FILES]
    if unknown:
        sys.exit(f"unknown file stem(s): {unknown}; choose from {list(FILES)}")

    em_lo, em_hi = args.em_window
    pm_lo, pm_hi = args.pm_window
    rows = []
    for stem in stems:
        nucleus, kind, prewin, q2, note = FILES[stem]
        x, y, e = load(stem)
        if kind == "em":
            r = integrate_em(x, y, e, (em_lo, em_hi))
            window = (f"E_m {em_lo:g}-{em_hi:g} MeV, "
                      f"p_m {prewin[0]}..{prewin[1]} MeV/c")
            kind_label = "E_m"
        else:
            check_symmetry(stem, x, y)
            r = integrate_pm(x, y, e, (pm_lo, pm_hi))
            window = (f"|p_m| {pm_lo:g}-{pm_hi:g} MeV/c, "
                      f"E_m {prewin[0]}-{prewin[1]} MeV")
            kind_label = "p_m"
        rows.append(dict(stem=stem, nucleus=nucleus, q2=q2, kind=kind_label,
                         window=window, N=r["N"], N_err=r["dN"],
                         plotted_sum=r["plotted"], plotted_sum_err=r["dplotted"],
                         note=note))

    # ---- print
    print(f"data: {DATA}")
    print(f"E_m window {em_lo:g}-{em_hi:g} MeV (figs 9/11);  "
          f"|p_m| window {pm_lo:g}-{pm_hi:g} MeV/c (figs 6/7)\n")
    hdr = (f"{'file':15s} {'nucl':5s} {'Q2':>5s} {'kind':4s} "
           f"{'N (nucleons)':>12s} {'+-':>8s}  {'plotted sum':>12s} {'+-':>10s}  note")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['stem']:15s} {r['nucleus']:5s} {r['q2']:5.2f} {r['kind']:4s} "
              f"{r['N']:12.4f} {r['N_err']:8.4f}  "
              f"{r['plotted_sum']:12.4e} {r['plotted_sum_err']:10.2e}  {r['note']}")
    print("\nN: E_m files = (Sum S dE) / 2 -- the plotted S(Em) counts each |p_m| "
          "twice (signed -300..300 integral);\n   p_m files = 4pi Sum S p^2 dp over "
          "the positive half only.\nplotted sum: Sum S dE (E_m files, = 2N) or "
          "Sum S dp over the signed axis (p_m files).")

    # expectation for the full-window E_m spectra: raw distorted strength
    if (em_lo, em_hi) == (0.0, 80.0):
        for r in rows:
            if r["kind"] == "E_m" and r["q2"] == 1.28:
                T, dT, Z, f = TRANSPARENCY_Q1P28[r["nucleus"]]
                exp = T * Z / f
                print(f"{r['stem']:15s} expected raw strength T*Z/f_corr = "
                      f"{T}*{Z}/{f} = {exp:.2f} (+-{dT * Z / f:.2f} stat on T); "
                      f"N/expected = {r['N'] / exp:.3f}")

    # ---- csv
    if args.csv:
        keys = ["stem", "nucleus", "q2", "kind", "window", "N", "N_err",
                "plotted_sum", "plotted_sum_err", "note"]
        with open(args.csv, "w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=keys)
            wr.writeheader()
            for r in rows:
                wr.writerow({k: r[k] for k in keys})
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()

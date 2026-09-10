"""Write the LaTeX version of report/dutta-integral/README.md.

The prose mirrors the README; every table body is generated from the
author data files in data/Dipingkar-dutta-data-prc_figs/ (column 1 = x,
column 2 = y as published, column 4 = statistical error) with the same
conventions as integrate_dutta.py, so the numbers cannot drift from the
markdown. Figures are the published-vs-table composites in figures/.

Run from anywhere:  pixi run python report/dutta-integral/make_report_tex.py
Output:             report/dutta-integral/dutta-integral.tex
Compile (from report/dutta-integral/, the repo's tectonic env):
    pixi run --manifest-path /exp/dune/data/users/liangliu/texenv/pixi.toml \\
        tectonic --outdir . dutta-integral.tex
"""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = REPO / "data" / "Dipingkar-dutta-data-prc_figs"
OUT = HERE / "dutta-integral.tex"

DE_MEV, DP_MEVC = 5.0, 40.0


def load(stem):
    x, y, _, e = np.loadtxt(DATA / f"{stem}.dat", unpack=True)
    return x, y, e


def sci(v, digits=5):
    """1.31822e-09 -> $1.31822\\times10^{-9}$."""
    m, ex = f"{v:.{digits}e}".split("e")
    return rf"${m}\times10^{{{int(ex)}}}$"


def tt(name):
    return r"\texttt{" + name.replace("_", r"\_") + "}"


# ---------------------------------------------------------------- E_m tables
def em_table(stem):
    x, y, e = load(stem)
    rows = [rf"{i + 1} & {xi:.1f} & {yi:.5f} \\" for i, (xi, yi) in enumerate(zip(x, y))]
    S, dS = y.sum(), np.sqrt((e ** 2).sum())
    body = "\n".join(rows)
    table = rf"""\begin{{center}}
\begin{{tabular}}{{rrr}}
\toprule
bin & $E_m$ (MeV) & $S(E_m)$ (MeV$^{{-1}}$) \\
\midrule
{body}
\midrule
\textbf{{sum}} & & \textbf{{{S:.5f}}} \\
\bottomrule
\end{{tabular}}
\end{{center}}"""
    sums = rf"""\begin{{center}}
\begin{{tabular}}{{ll}}
\toprule
quantity & value \\
\midrule
$\sum S(E_m)$, plain sum of the tabulated values & $\mathbf{{{S:.5f} \pm {dS:.5f}}}$ MeV$^{{-1}}$ \\
$\sum S(E_m)\,\Delta E$ with $\Delta E = 5$ MeV (the plotted area, 0--80 MeV) & $\mathbf{{{S * DE_MEV:.4f} \pm {dS * DE_MEV:.4f}}}$ \\
$\tfrac12 \sum S(E_m)\,\Delta E$ & ${S * DE_MEV / 2:.4f} \pm {dS * DE_MEV / 2:.4f}$ \\
\bottomrule
\end{{tabular}}
\end{{center}}"""
    return table, sums


# ---------------------------------------------------------------- p_m tables
def pm_table(stem, ylabel):
    x, y, e = load(stem)
    k4 = 4 * np.pi * y * x ** 2 * DP_MEVC
    k2 = 2 * np.pi * y * x ** 2 * DP_MEVC
    rows = [rf"{i + 1} & ${xi:+.0f}$ & {sci(yi)} & {a:.4f} & {b:.4f} \\"
            for i, (xi, yi, a, b) in enumerate(zip(x, y, k4, k2))]
    body = "\n".join(rows)
    return rf"""\begin{{center}}\small\renewcommand{{\arraystretch}}{{0.95}}
\begin{{tabular}}{{rrrrr}}
\toprule
bin & $p_m$ (MeV/c) & {ylabel} & $4\pi\,S(p_m)\,p_m^2\,\Delta p$ & $2\pi\,S(p_m)\,p_m^2\,\Delta p$ \\
\midrule
{body}
\midrule
\textbf{{sum, all 16 bins}} & & \textbf{{{sci(y.sum())}}} & \textbf{{{k4.sum():.4f}}} & \textbf{{{k2.sum():.4f}}} \\
\bottomrule
\end{{tabular}}
\end{{center}}"""


def pm_sums(stems, heads):
    cols = []
    for stem in stems:
        x, y, e = load(stem)
        S, dS = y.sum(), np.sqrt((e ** 2).sum())
        pos = x > 0
        k = 4 * np.pi * x[pos] ** 2 * DP_MEVC
        N, dN = (y[pos] * k).sum(), np.sqrt(((e[pos] * k) ** 2).sum())
        cols.append((S, dS, S * DP_MEVC, dS * DP_MEVC, N, dN))
    spec = "l" + "l" * len(stems)
    head = " & ".join(["quantity"] + heads) + r" \\"
    r1 = " & ".join([r"$\sum S(p_m)$, plain sum (MeV$^{-3}$)"]
                    + [rf"{sci(c[0])} $\pm$ {sci(c[1], 1)}" for c in cols]) + r" \\"
    r2 = " & ".join([r"$\sum S(p_m)\,\Delta p$, signed axis (MeV$^{-2}$)"]
                    + [rf"{sci(c[2], 4)} $\pm$ {sci(c[3], 1)}" for c in cols]) + r" \\"
    r3 = " & ".join([r"$4\pi\sum_{p_m>0} S\,p_m^2\,\Delta p$, positive half"]
                    + [rf"$\mathbf{{{c[4]:.4f} \pm {c[5]:.4f}}}$" for c in cols]) + r" \\"
    return rf"""\begin{{center}}\small
\begin{{tabular}}{{{spec}}}
\toprule
{head}
\midrule
{r1}
{r2}
{r3}
\bottomrule
\end{{tabular}}
\end{{center}}"""


# ---------------------------------------------------------------- document
c12_em, c12_em_sums = em_table("fig9_q1p2")
fe_em, fe_em_sums = em_table("fig11_q1p2")
c12_p = pm_table("fig6_top_q1p2", r"$S(p_m)$, p-shell (MeV$^{-3}$)")
c12_s = pm_table("fig6_bot_q1p2", r"$S(p_m)$, s-shell (MeV$^{-3}$)")
fe_pm = pm_table("fig7_q1p2", r"$S(p_m)$ (MeV$^{-3}$)")
c12_pm_sums = pm_sums(["fig6_top_q1p2", "fig6_bot_q1p2"], ["p-shell window", "s-shell window"])
fe_pm_sums = pm_sums(["fig7_q1p2"], ["value"])

C = r"\texorpdfstring{$^{12}$C}{C12}"
FE = r"\texorpdfstring{$^{56}$Fe}{Fe56}"
Q2 = r"\texorpdfstring{$Q^2 = 1.28$ (GeV/c)$^2$}{Q2 = 1.28 (GeV/c)2}"

doc = rf"""\documentclass[11pt]{{article}}
\usepackage[margin=2.2cm]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{amsmath,amssymb}}
\usepackage{{placeins}}
\usepackage{{needspace}}
\usepackage[hidelinks]{{hyperref}}
\setlength{{\parskip}}{{0.4em}}
\setlength{{\emergencystretch}}{{3em}}
\makeatletter\setlength{{\@fptop}}{{0pt}}\makeatother   % float pages start at the top
\graphicspath{{{{figures/}}}}

\title{{Dutta E91-013: integrals of the (e,e$'$p) spectral-function data}}
\author{{Liang Liu}}
\date{{\today}}

\begin{{document}}
\maketitle

Summary of what the author data tables behind the Dutta \emph{{et al.}} JLab
Hall~C \textbf{{E91-013}} paper
(\href{{https://arxiv.org/abs/nucl-ex/0303011}}{{nucl-ex/0303011}}, {C} /
{FE} / $^{{197}}$Au quasi-elastic (e,e$'$p)) integrate to, and on which
scale. This document is the write-up that goes with {tt("integrate_dutta.py")}
(the integrator) and {tt("make_published_vs_table.py")} (the published-vs-table
figures of section~1); it is generated by {tt("make_report_tex.py")} from the
same data files as the markdown version ({tt("README.md")}).

\begin{{itemize}}
\item Paper source: {tt("papers/nucl-ex_0303011/")} (tex {tt("longpaper2.tex")};
  every \texttt{{tex:line}} below anchors to it); published figure renders in
  {tt("papers/nucl-ex_0303011/figures/")}.
\item Author data: {tt("data/Dipingkar-dutta-data-prc_figs/")} --- 14 files,
  exactly figs~6, 7, 9, 11 of the paper.
\item Earlier per-figure report: \texttt{{report/\allowbreak dutta-e91013-figures.md}}. Its
  normalization reading of figs~9/11 (``$\approx Z$, full-occupancy scale'')
  is the old one; the sections after section~1 here supersede it.
\end{{itemize}}

Sections 4 (the conventions behind the factor $\tfrac12$ and the
positive-half 3D integral; nucleon counts against $T \cdot Z / f_\mathrm{{corr}}$)
and 5 (windowed integrals, shell occupancies, caveats) are still to be
written.

\section{{\texorpdfstring{{$E_m$ and $p_m$}}{{Em and pm}} for C12 and Fe56: each published figure next to its data table}}

\subsection{{The four figures, published vs table}}

Left: the paper's render (autocropped). Right: the same quantity drawn from
the \texttt{{.dat}} files on the paper's axes --- points with the tabulated
statistical errors, \textbf{{no rescaling}} (no $\tfrac12$ on the $E_m$ files,
no L+R fold on the $p_m$ files; those conventions are the subject of the next
sections). The $p_m$ replots use the house colour cycle with fig~6's marker
shapes per $Q^2$ (fig~7 in print assigns markers differently; the legends
identify the sets). Numbers quoted below come from
{tt("dutta_published_vs_table.txt")}: a per-file ratio to the $Q^2 = 1.8$
reference and a histdiag \texttt{{describe1d}} readout of all 14 files,
computed on the tabulated values.

\paragraph{{{C} missing energy (fig~9).}}
The 16 tabulated points are the published ones: $0.571 \pm 0.005$ MeV$^{{-1}}$
at $E_m = 17.5$ MeV, 0.269 at 22.5, the s-shell bump peaking at 0.077 at
37.5, and three exact zeros below 15 MeV. The IPSM curve exists only in
print. The one visible difference is the error bars: the file's column~4 is
statistical (0.8\,\% at the peak), while the published bars at 17.5 and
22.5 MeV are several times larger (pixel-measured in
{tt("dutta-e91013-figures.md")} \S5).

\begin{{figure}}[htbp]
\centering
\includegraphics[width=\textwidth]{{dutta_fig9_c12_em_published_vs_table.png}}
\caption{{Fig.~9 of the paper (left) and the 16 points of {tt("fig9_q1p2.dat")} (right).}}
\end{{figure}}

\paragraph{{{C} missing momentum, p-shell and s-shell windows (fig~6).}}
Three of the four $Q^2$ sets sit on the published points: relative to the
$Q^2 = 1.8$ reference file the bin-wise median ratio is 1.01 ($Q^2 = 1.28$)
and 0.97 (3.25) in the p-shell panel, 1.14 and 1.20 in the s-shell panel,
with the signed-axis sums equal to within 5--8\,\%. The \textbf{{$Q^2 = 0.64$
files do not}}: their median ratio to the reference is 1.27 (p-shell) and
1.33 (s-shell) with a $p_m$-dependent spread (1.07--1.44), whereas in print
all four $Q^2$ coincide within marker size. Those two files are excluded from
every integral in this document (open question tracked in
{tt("open_questions.md")}). The $\ell = 1$ dip at $p_m = 0$ in the p-shell
window and the $\ell = 0$ peak in the s-shell window (tex:920--922) are in
the tables as printed: in the $Q^2 = 1.28$ file the p-shell dip bin is 0.31 of
its peak at $|p_m| = 100$ MeV/c.

\begin{{figure}}[htbp]
\centering
\includegraphics[width=\textwidth]{{dutta_fig6_c12_pm_published_vs_table.png}}
\caption{{Fig.~6 of the paper (left) and the eight {tt("fig6_*.dat")} files (right), four $Q^2$ sets per panel.}}
\end{{figure}}

\paragraph{{{FE} missing energy (fig~11).}}
The table reproduces the published points ($0.810 \pm 0.009$ MeV$^{{-1}}$ at
$E_m = 12.5$ MeV, then a monotone fall to 0.055 at 77.5; two exact zeros
below 10 MeV). The three theory curves (IPSM, Benhar, TIMORA) exist only in
print.

\begin{{figure}}[htbp]
\centering
\includegraphics[width=\textwidth]{{dutta_fig11_fe56_em_published_vs_table.png}}
\caption{{Fig.~11 of the paper (left) and the 16 points of {tt("fig11_q1p2.dat")} (right).}}
\end{{figure}}

\paragraph{{{FE} missing momentum (fig~7).}}
All four files coincide as printed: median ratios to the $Q^2 = 1.8$
reference 1.17 (0.64), 1.09 (1.28), 1.08 (3.25), signed-axis sums equal to
within 5\,\% (the caption's normalization). No fig~6-type anomaly here.
Bin-wise statistical errors are 1--5\,\%, largest at $|p_m| = 20$ and
300 MeV/c.

\begin{{figure}}[htbp]
\centering
\includegraphics[width=\textwidth]{{dutta_fig7_fe56_pm_published_vs_table.png}}
\caption{{Fig.~7 of the paper (left) and the four {tt("fig7_*.dat")} files (right).}}
\end{{figure}}
\FloatBarrier

\subsection{{Reproduce}}

From the repo root:
\begin{{verbatim}}
pixi run python report/dutta-integral/make_published_vs_table.py
# -> figures/dutta_fig{{9,6,11,7}}_*_published_vs_table.png
#    figures/dutta_published_vs_table.txt
pixi run python report/dutta-integral/make_report_tex.py      # -> dutta-integral.tex
cd report/dutta-integral && pixi run \
    --manifest-path /exp/dune/data/users/liangliu/texenv/pixi.toml \
    tectonic --outdir . dutta-integral.tex                    # -> dutta-integral.pdf
\end{{verbatim}}
The script reads the \texttt{{.dat}} files directly, uses the house plot style
({tt("results/template/plot_style.py")}) and writes its histdiag readout with
{tt("results/template/histdiag.py")}; the published renders come from
{tt("papers/nucl-ex_0303011/figures/")}.

\section{{Missing energy at {Q2}: the tabulated points and their sums}}

\subsection{{{C} (fig~9)}}

The 16 rows of {tt("fig9_q1p2.dat")} (column~1 = bin centre, column~2 =
$S(E_m)$ as plotted):

{c12_em}

Sums over the 16 points (errors: column~4 in quadrature, statistical only):

{c12_em_sums}

Where the strength sits: the two p-shell bins at 17.5 and 22.5 MeV carry
69.1\,\% of the sum, the four s-shell bins 30--50 MeV carry 21.4\,\%, the dip
bin at 27.5 MeV 4.7\,\% and the tail above 50 MeV 4.9\,\%. The author's
integral for this figure is \textbf{{3.04}}, i.e.\ half of
$\sum S(E_m)\,\Delta E$; why the plotted area is twice the nucleon count (the
signed $-300 \ldots +300$ MeV/c $p_m$ axis) is the subject of section~3.

Reproduce (the plotted sum and its half are the \texttt{{plotted sum}} and
\texttt{{N}} columns):
\begin{{verbatim}}
pixi run python report/dutta-integral/integrate_dutta.py --files fig9_q1p2
\end{{verbatim}}

\subsection{{{FE} (fig~11)}}

The 16 rows of {tt("fig11_q1p2.dat")} (column~1 = bin centre, column~2 =
$S(E_m)$ as plotted):

{fe_em}

Sums over the 16 points (errors: column~4 in quadrature, statistical only):

{fe_em_sums}

Where the strength sits: the three bins 10--25 MeV carry 52.0\,\% of the sum,
25--50 MeV 33.7\,\%, and the tail 50--80 MeV 14.2\,\% (the last bin alone
1.5\,\%), against 4.9\,\% above 50 MeV for carbon. No author-quoted integral
exists for this figure; the same $\tfrac12$ convention as for fig~9 gives
9.10, to be cross-checked against the fig~7 momentum-distribution integral in
section~4.

Reproduce:
\begin{{verbatim}}
pixi run python report/dutta-integral/integrate_dutta.py --files fig11_q1p2
\end{{verbatim}}

\section{{Missing momentum at {Q2}: the tabulated points and their integrals}}

The $p_m$ files are tabulated on the signed axis, 16 bins of
$\Delta p = 40$ MeV/c centred at $-300 \ldots +300$ MeV/c, and every file is
exactly left--right symmetric, $y(-p_m) \equiv y(+p_m)$ to full precision.
Two integrals are quoted per file:
\begin{{itemize}}
\item \textbf{{the plotted area}} $\sum S(p_m)\,\Delta p$ over all 16 signed
  bins (MeV$^{{-2}}$) --- the quantity the paper's rescale-to-$Q^2 = 1.8$
  caption equalizes;
\item \textbf{{the 3D integral}} $N = 4\pi \sum_{{p_m > 0}} S(p_m)\,p_m^2\,\Delta p$
  over the \textbf{{positive half only}} ($p_m$ at the bin centre, rectangle
  rule), dimensionless --- the number of protons in the file's $E_m$ window.
  Summing both halves would count each $|p_m|$ twice, since the files are
  symmetrized.
\end{{itemize}}
Errors are column~4 in quadrature (statistical only). All numbers are the
\texttt{{plotted sum}} / \texttt{{N}} columns of {tt("integrate_dutta.py")}.

\subsection{{{C} (fig~6, p-shell and s-shell windows)}}

The 16 rows of {tt("fig6_top_q1p2.dat")} (p-shell window) and
{tt("fig6_bot_q1p2.dat")} (s-shell window), column~1 = bin centre, column~2 =
$S(p_m)$ as plotted, with the per-bin 3D weights ($\Delta p = 40$ MeV/c, $p_m$
at the bin centre). As for iron, the $2\pi$ column summed over all 16 signed
bins is the 3D integral $N$ and the $4\pi$ column over all 16 bins is twice
that.

\needspace{{22\baselineskip}}
\paragraph{{p-shell window, $10 < E_m < 25$ MeV.}}
{c12_p}

\needspace{{22\baselineskip}}
\paragraph{{s-shell window, $30 < E_m < 50$ MeV.}}
{c12_s}

{c12_pm_sums}

\needspace{{26\baselineskip}}
\subsection{{{FE} (fig~7, full 0--80 MeV window)}}

The 16 rows of {tt("fig7_q1p2.dat")}, with the per-bin 3D weights
($\Delta p = 40$ MeV/c, $p_m$ at the bin centre): the $2\pi$ column summed
over all 16 signed bins is the 3D integral $N$; the $4\pi$ column over all 16
bins is twice that, since the file is symmetric and each $|p_m|$ appears on
both sides:

{fe_pm}

{fe_pm_sums}

Reproduce:
\begin{{verbatim}}
pixi run python report/dutta-integral/integrate_dutta.py \
    --files fig6_top_q1p2 fig6_bot_q1p2 fig7_q1p2
\end{{verbatim}}

\end{{document}}
"""

OUT.write_text(doc)
print("wrote", OUT)

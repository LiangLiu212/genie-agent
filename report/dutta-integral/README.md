# Dutta E91-013: integrals of the (e,e′p) spectral-function data

Summary of what the author data tables behind the Dutta *et al.* JLab Hall C
**E91-013** paper ([nucl-ex/0303011](https://arxiv.org/abs/nucl-ex/0303011),
¹²C / ⁵⁶Fe / ¹⁹⁷Au quasi-elastic (e,e′p)) integrate to, and on which scale.
This document is the write-up that goes with
[`integrate_dutta.py`](integrate_dutta.py) (the integrator) and
[`make_published_vs_table.py`](make_published_vs_table.py) (the
published-vs-table figures of section 1).

- Paper source: [`papers/nucl-ex_0303011/`](../../papers/nucl-ex_0303011/paper_nucl-ex_0303011.md)
  (tex `longpaper2.tex`; every `tex:line` below anchors to it); published
  figure renders in `papers/nucl-ex_0303011/figures/`
- Author data: [`data/Dipingkar-dutta-data-prc_figs/`](../../data/Dipingkar-dutta-data-prc_figs)
  — 14 files, exactly figs 6, 7, 9, 11 of the paper
- Earlier per-figure report: [`report/dutta-e91013-figures.md`](../dutta-e91013-figures.md).
  Its normalization reading of figs 9/11 ("≈ Z, full-occupancy scale") is the
  old one; the sections after section 1 here supersede it.

Sections:

1. [E_m and p_m for C12 and Fe56: the paper's definitions, and each published figure next to its data table](#1-e_m-and-p_m-for-c12-and-fe56-from-the-paper-and-from-the-data-tables)
2. Missing energy at Q² = 1.28 for ¹²C (fig 9) and ⁵⁶Fe (fig 11): the tabulated points and their sums (section 2 below)
3. Missing momentum at Q² = 1.28 for ¹²C (fig 6) and ⁵⁶Fe (fig 7): the tabulated points and their integrals for every Q² (section 3 below)
4. *(to be written)* the conventions behind the factor ½ and the positive-half 3D integral; nucleon counts against T·Z/f_corr
5. *(to be written)* windowed integrals (shell occupancies) and caveats

---

## 1. E_m and p_m for C12 and Fe56, from the paper and from the data tables

### 1.1 What the paper measures

For an electron knocking a proton out of nucleus A with energy transfer ω and
three-momentum transfer **q**, leaving a scattered proton p′ and a residual
nucleus A−1, the paper defines (tex:221–227)

    E_m = ω − T_p′ − T_{A−1}          missing energy
    p_m = p_p′ − q                    missing momentum (vector)

with T_p′ and T_{A−1} the kinetic energies of the knocked-out proton and the
recoiling nucleus. The spectral function S(E_s, **p**_m) is "the probability of
finding a proton with separation energy E_s and momentum **p**_m inside that
nucleus" (tex:700–702).

The experimental spectral function is built bin by bin in (E_m, p_m)
(tex:852–856): counts in each bin are weighted by the inverse off-shell e–p
cross section and kinematic factors (σ_cc1), divided by luminosity and by the
SIMC phase space H(E_m, p_m), and multiplied by a SIMC radiative-correction
factor C^rad(E_m, p_m); the model spectral function is iterated until the
result no longer depends on it. The result is a **distorted** spectral
function S^D: "these corrected spectral functions still include distortions
due the effects of final state nuclear interactions, including absorption"
(tex:871–873). Nothing in the paper renormalizes S^D back to full occupancy.

The paper shows two projections of S^D (tex:881–884): "the missing momentum
was integrated over in order to obtain the energy spectral functions and the
missing energy was integrated over to obtain momentum distributions". The
acceptance window in both variables is |p_m| ≤ 300 MeV/c and E_m ≤ 80 MeV
(tex:1086–1087, the transparency window).

### 1.2 Kinematics of the data used here

The two missing-energy figures exist only at **Q² = 1.28 (GeV/c)²**; the two
momentum-distribution figures overlay four Q² settings. Table I of the paper
(tex:682–685) gives for the Q² = 1.28 setting:

| beam energy | central e′ energy / angle | central proton energy | proton angles (conjugate in bold) | Q² | ε |
|---|---|---|---|---|---|
| 2.445 GeV | 1.725 GeV / 32.0° | 700 MeV | 31.5, 35.5, 39.5, **43.5**, 47.5, 51.4, 55.4° | 1.28 (GeV/c)² | 0.81 |

Two more numbers from the paper belong to the same setting and enter the
later sections: the nuclear transparencies at Q² = 1.28, **T(C) = 0.60(2)**
and **T(Fe) = 0.44(1)** (Table III, tex:1227, statistical errors), and the
short-range-correlation factors applied to the PWIA yield, **1.11 ± 0.03 (C)**
and **1.26 ± 0.08 (Fe)** (tex:1134–1135).

### 1.3 The four figures and the 14 data files

| figure | nucleus | quantity plotted (y) | integrated over | x grid | Q² sets in the files | files |
|---|---|---|---|---|---|---|
| fig 6 top | ¹²C | ∫S^D dE_m, p-shell window | 10 < E_m < 25 MeV | p_m = −300 … +300 MeV/c, 16 bins of 40 MeV/c | 0.64, 1.28, 1.8, 3.25 | `fig6_top_{q0p6,q1p2,q1p8,q3p2}.dat` |
| fig 6 bottom | ¹²C | ∫S^D dE_m, s-shell window | 30 < E_m < 50 MeV | same | same | `fig6_bot_{…}.dat` |
| fig 7 | ⁵⁶Fe | ∫S^D dE_m | 0 < E_m < 80 MeV | same | same | `fig7_{…}.dat` |
| fig 9 | ¹²C | ∫S^D d³p_m | −300 < p_m < 300 MeV/c (signed) | E_m = 2.5 … 77.5 MeV, 16 bins of 5 MeV | 1.28 only | `fig9_q1p2.dat` |
| fig 11 | ⁵⁶Fe | ∫S^D d³p_m | −300 < p_m < 300 MeV/c (signed) | same | 1.28 only | `fig11_q1p2.dat` |

Caption facts: fig 6 (tex:891–893) and fig 7 (tex:901–902) are "normalized so
that the integral of the measured spectral functions over |p_m| < 300 MeV/c is
equal to the integral of the spectral function at Q² of 1.8 (GeV/c)²" — a
shape-comparison convention across Q²; the Q² = 1.8 file is therefore the
unrescaled reference. Figs 9 (tex:965–966) and 11 (tex:999–1004) carry no
normalization statement at all; they are compared with IPSM (and, for iron,
Benhar and TIMORA) curves that exist only in print.

Columns of every file, per the author's description: x, y as plotted, an
x-uncertainty of 0.5 % of x (unused; one sign glitch in `fig7_q1p2.dat` row 1),
and the **statistical** error on y. Units: y in MeV⁻³ for the p_m files and
MeV⁻¹ for the E_m files. The E_m files' y is S^D integrated over the *signed*
p_m axis from −300 to +300 MeV/c (author's column description; this is what
makes the later factor 2).

Two structural facts about the tables:

- every p_m file is **exactly left–right symmetrized**, y(−p_m) ≡ y(+p_m) to
  full precision, so each holds 8 independent values (the ± asymmetry the
  paper discusses at tex:922 is absent by construction);
- the E_m files are **zero below the first shell**: fig 9 has no strength
  below E_m = 15 MeV (three empty bins), fig 11 none below 10 MeV (two).

### 1.4 Each published figure next to its data table

Left: the paper's render (autocropped). Right: the same quantity drawn from
the `.dat` files on the paper's axes — points with the tabulated statistical
errors, **no rescaling** (no ½ on the E_m files, no L+R fold on the p_m
files; those conventions are the subject of the next sections). The p_m
replots use the house colour cycle with fig 6's marker shapes per Q²
(fig 7 in print assigns markers differently; the legends identify the sets).
Numbers quoted below come from
[`dutta_published_vs_table.txt`](figures/dutta_published_vs_table.txt): a
per-file ratio to the Q² = 1.8 reference and a histdiag `describe1d` readout
of all 14 files, computed on the tabulated values.

**¹²C missing energy (fig 9)**

![fig 9 published vs table](figures/dutta_fig9_c12_em_published_vs_table.png)

The 16 tabulated points are the published ones: 0.571 ± 0.005 MeV⁻¹ at
E_m = 17.5 MeV, 0.269 at 22.5, the s-shell bump peaking at 0.077 at 37.5, and
three exact zeros below 15 MeV. The IPSM curve exists only in print. The one
visible difference is the error bars: the file's column 4 is statistical
(0.8 % at the peak), while the published bars at 17.5 and 22.5 MeV are
several times larger (pixel-measured in
[`dutta-e91013-figures.md` §5](../dutta-e91013-figures.md)).

**¹²C missing momentum, p-shell and s-shell windows (fig 6)**

![fig 6 published vs table](figures/dutta_fig6_c12_pm_published_vs_table.png)

Three of the four Q² sets sit on the published points: relative to the
Q² = 1.8 reference file the bin-wise median ratio is 1.01 (Q² = 1.28) and
0.97 (3.25) in the p-shell panel, 1.14 and 1.20 in the s-shell panel, with the
signed-axis sums equal to within 5–8 %. The **Q² = 0.64 files do not**: their
median ratio to the reference is 1.27 (p-shell) and 1.33 (s-shell) with a
p_m-dependent spread (1.07–1.44), whereas in print all four Q² coincide within
marker size. Those two files are excluded from every integral in this
document (open question tracked in
[`open_questions.md`](../../papers/nucl-ex_0303011/open_questions.md)).
The ℓ = 1 dip at p_m = 0 in the p-shell window and the ℓ = 0 peak in the
s-shell window (tex:920–922) are in the tables as printed: in the Q² = 1.28
file the p-shell dip bin is 0.31 of its peak at |p_m| = 100 MeV/c.

**⁵⁶Fe missing energy (fig 11)**

![fig 11 published vs table](figures/dutta_fig11_fe56_em_published_vs_table.png)

The table reproduces the published points (0.810 ± 0.009 MeV⁻¹ at
E_m = 12.5 MeV, then a monotone fall to 0.055 at 77.5; two exact zeros below
10 MeV). The three theory curves (IPSM, Benhar, TIMORA) exist only in print.

**⁵⁶Fe missing momentum (fig 7)**

![fig 7 published vs table](figures/dutta_fig7_fe56_pm_published_vs_table.png)

All four files coincide as printed: median ratios to the Q² = 1.8 reference
1.17 (0.64), 1.09 (1.28), 1.08 (3.25), signed-axis sums equal to within 5 %
(the caption's normalization). No fig 6-type anomaly here. Bin-wise
statistical errors are 1–5 %, largest at |p_m| = 20 and 300 MeV/c.

### 1.5 Reproduce

From the repo root:

```bash
pixi run python report/dutta-integral/make_published_vs_table.py
# -> figures/dutta_fig{9,6,11,7}_*_published_vs_table.png, dutta_published_vs_table.txt
```

The script reads the `.dat` files directly, uses the house plot style
(`results/template/plot_style.py`) and writes its histdiag readout with
`results/template/histdiag.py`; the published renders come from
`papers/nucl-ex_0303011/figures/`.

---

## 2. Missing energy at Q² = 1.28 (GeV/c)²: the tabulated points and their sums

### 2.1 ¹²C (fig 9)

The 16 rows of `fig9_q1p2.dat` (column 1 = bin centre, column 2 = S(E_m) as
plotted):

| bin | E_m (MeV) | S(E_m) (MeV⁻¹) |
|---|---|---|
| 1 | 2.5 | 0.00000 |
| 2 | 7.5 | 0.00000 |
| 3 | 12.5 | 0.00000 |
| 4 | 17.5 | 0.57130 |
| 5 | 22.5 | 0.26883 |
| 6 | 27.5 | 0.05668 |
| 7 | 32.5 | 0.06362 |
| 8 | 37.5 | 0.07718 |
| 9 | 42.5 | 0.06606 |
| 10 | 47.5 | 0.05315 |
| 11 | 52.5 | 0.02708 |
| 12 | 57.5 | 0.01514 |
| 13 | 62.5 | 0.00608 |
| 14 | 67.5 | 0.00436 |
| 15 | 72.5 | 0.00359 |
| 16 | 77.5 | 0.00297 |
| **sum** | | **1.21604** |

Sums over the 16 points (errors: column 4 in quadrature, statistical only):

| quantity | value |
|---|---|
| Σ S(E_m), plain sum of the tabulated values | **1.21604 ± 0.00578 MeV⁻¹** |
| Σ S(E_m) ΔE with ΔE = 5 MeV (the plotted area, 0–80 MeV) | **6.0802 ± 0.0289** |
| ½ Σ S(E_m) ΔE | 3.0401 ± 0.0145 |

Where the strength sits: the two p-shell bins at 17.5 and 22.5 MeV carry
69.1 % of the sum, the four s-shell bins 30–50 MeV carry 21.4 %, the dip bin
at 27.5 MeV 4.7 % and the tail above 50 MeV 4.9 %. The author's integral for
this figure is **3.04**, i.e. half of Σ S(E_m) ΔE; why the plotted area is
twice the nucleon count (the signed −300…+300 MeV/c p_m axis) is the subject
of section 3.

Reproduce (the plotted sum and its half are the `plotted sum` and `N`
columns):

```bash
pixi run python report/dutta-integral/integrate_dutta.py --files fig9_q1p2
```

### 2.2 ⁵⁶Fe (fig 11)

The 16 rows of `fig11_q1p2.dat` (column 1 = bin centre, column 2 = S(E_m) as
plotted):

| bin | E_m (MeV) | S(E_m) (MeV⁻¹) |
|---|---|---|
| 1 | 2.5 | 0.00000 |
| 2 | 7.5 | 0.00000 |
| 3 | 12.5 | 0.80983 |
| 4 | 17.5 | 0.63965 |
| 5 | 22.5 | 0.44406 |
| 6 | 27.5 | 0.36284 |
| 7 | 32.5 | 0.28453 |
| 8 | 37.5 | 0.23175 |
| 9 | 42.5 | 0.20011 |
| 10 | 47.5 | 0.14872 |
| 11 | 52.5 | 0.13002 |
| 12 | 57.5 | 0.11820 |
| 13 | 62.5 | 0.08474 |
| 14 | 67.5 | 0.06965 |
| 15 | 72.5 | 0.06070 |
| 16 | 77.5 | 0.05527 |
| **sum** | | **3.64006** |

Sums over the 16 points (errors: column 4 in quadrature, statistical only):

| quantity | value |
|---|---|
| Σ S(E_m), plain sum of the tabulated values | **3.64006 ± 0.01579 MeV⁻¹** |
| Σ S(E_m) ΔE with ΔE = 5 MeV (the plotted area, 0–80 MeV) | **18.2003 ± 0.0790** |
| ½ Σ S(E_m) ΔE | 9.1001 ± 0.0395 |

Where the strength sits: the three bins 10–25 MeV carry 52.0 % of the
sum, 25–50 MeV 33.7 %, and the tail 50–80 MeV 14.2 % (the last
bin alone 1.5 %), against 4.9 % above 50 MeV for carbon. No author-quoted
integral exists for this figure; the same ½ convention as for fig 9 gives
9.10, to be cross-checked against the fig 7 momentum-distribution integral
in section 4.

Reproduce:

```bash
pixi run python report/dutta-integral/integrate_dutta.py --files fig11_q1p2
```

---

## 3. Missing momentum at Q² = 1.28 (GeV/c)²: the tabulated points and their integrals

The p_m files are tabulated on the signed axis, 16 bins of Δp = 40 MeV/c
centred at −300 … +300 MeV/c, and every file is exactly left–right symmetric
(section 1.3). Two integrals are quoted per file:

- **the plotted area** Σ S(p_m) Δp over all 16 signed bins (MeV⁻²) — the
  quantity the paper's rescale-to-Q² = 1.8 caption equalizes;
- **the 3D integral** N = 4π Σ_{p_m>0} S(p_m) p_m² Δp over the **positive
  half only** (p_m at the bin centre, rectangle rule), dimensionless — the
  number of protons in the file's E_m window. Summing both halves would count
  each |p_m| twice, since the files are symmetrized.

Errors are column 4 in quadrature (statistical only). All numbers are the
`plotted sum` / `N` columns of `integrate_dutta.py`.

### 3.1 ¹²C (fig 6, p-shell and s-shell windows)

The 16 rows of `fig6_top_q1p2.dat` (p-shell window) and `fig6_bot_q1p2.dat`
(s-shell window), column 1 = bin centre, column 2 = S(p_m) as plotted, with
the per-bin 3D weights (Δp = 40 MeV/c, p_m at the bin centre). As for iron,
the 2π column summed over all 16 signed bins is the 3D integral N and the
4π column over all 16 bins is twice that.

**p-shell window, 10 < E_m < 25 MeV**

| bin | p_m (MeV/c) | S(p_m), p-shell 10 < E_m < 25 MeV (MeV⁻³) | 4π S(p_m) p_m² Δp | 2π S(p_m) p_m² Δp |
|---|---|---|---|---|
| 1 | -300 | 1.31822e-09 | 0.0596 | 0.0298 |
| 2 | -260 | 4.15417e-09 | 0.1412 | 0.0706 |
| 3 | -220 | 1.13985e-08 | 0.2773 | 0.1387 |
| 4 | -180 | 2.61633e-08 | 0.4261 | 0.2130 |
| 5 | -140 | 4.86048e-08 | 0.4789 | 0.2394 |
| 6 | -100 | 5.89047e-08 | 0.2961 | 0.1480 |
| 7 | -60 | 4.55982e-08 | 0.0825 | 0.0413 |
| 8 | -20 | 1.81916e-08 | 0.0037 | 0.0018 |
| 9 | +20 | 1.81916e-08 | 0.0037 | 0.0018 |
| 10 | +60 | 4.55982e-08 | 0.0825 | 0.0413 |
| 11 | +100 | 5.89047e-08 | 0.2961 | 0.1480 |
| 12 | +140 | 4.86048e-08 | 0.4789 | 0.2394 |
| 13 | +180 | 2.61633e-08 | 0.4261 | 0.2130 |
| 14 | +220 | 1.13985e-08 | 0.2773 | 0.1387 |
| 15 | +260 | 4.15417e-09 | 0.1412 | 0.0706 |
| 16 | +300 | 1.31822e-09 | 0.0596 | 0.0298 |
| **sum, all 16 bins** | | **4.28667e-07** | **3.5306** | **1.7653** |

**s-shell window, 30 < E_m < 50 MeV**

| bin | p_m (MeV/c) | S(p_m), s-shell 30 < E_m < 50 MeV (MeV⁻³) | 4π S(p_m) p_m² Δp | 2π S(p_m) p_m² Δp |
|---|---|---|---|---|
| 1 | -300 | 7.38319e-10 | 0.0334 | 0.0167 |
| 2 | -260 | 1.29075e-09 | 0.0439 | 0.0219 |
| 3 | -220 | 3.29055e-09 | 0.0801 | 0.0400 |
| 4 | -180 | 7.72794e-09 | 0.1259 | 0.0629 |
| 5 | -140 | 1.72738e-08 | 0.1702 | 0.0851 |
| 6 | -100 | 3.00671e-08 | 0.1511 | 0.0756 |
| 7 | -60 | 4.34589e-08 | 0.0786 | 0.0393 |
| 8 | -20 | 5.10294e-08 | 0.0103 | 0.0051 |
| 9 | +20 | 5.10294e-08 | 0.0103 | 0.0051 |
| 10 | +60 | 4.34589e-08 | 0.0786 | 0.0393 |
| 11 | +100 | 3.00671e-08 | 0.1511 | 0.0756 |
| 12 | +140 | 1.72738e-08 | 0.1702 | 0.0851 |
| 13 | +180 | 7.72794e-09 | 0.1259 | 0.0629 |
| 14 | +220 | 3.29055e-09 | 0.0801 | 0.0400 |
| 15 | +260 | 1.29075e-09 | 0.0439 | 0.0219 |
| 16 | +300 | 7.38319e-10 | 0.0334 | 0.0167 |
| **sum, all 16 bins** | | **3.09754e-07** | **1.3868** | **0.6934** |

| quantity | p-shell window | s-shell window |
|---|---|---|
| Σ S(p_m), plain sum of the 16 values (MeV⁻³) | 4.28667e-07 ± 4.3e-09 | 3.09754e-07 ± 3.8e-09 |
| Σ S(p_m) Δp, Δp = 40 MeV/c, signed axis (MeV⁻²) | 1.7147e-05 ± 1.7e-07 | 1.2390e-05 ± 1.5e-07 |
| 4π Σ_{p_m>0} S(p_m) p_m² Δp, positive half | **1.7653 ± 0.0198** | **0.6934 ± 0.0065** |

### 3.2 ⁵⁶Fe (fig 7, full 0–80 MeV window)

The 16 rows of `fig7_q1p2.dat`, with the per-bin 3D weights (Δp = 40 MeV/c,
p_m at the bin centre): the 2π column summed over all 16 signed bins is the
3D integral N; the 4π column over all 16 bins is twice that, since the file
is symmetric and each |p_m| appears on both sides:

| bin | p_m (MeV/c) | S(p_m), 0 < E_m < 80 MeV (MeV⁻³) | 4π S(p_m) p_m² Δp | 2π S(p_m) p_m² Δp |
|---|---|---|---|---|
| 1 | -300 | 9.66999e-09 | 0.4375 | 0.2187 |
| 2 | -260 | 2.45150e-08 | 0.8330 | 0.4165 |
| 3 | -220 | 6.71838e-08 | 1.6345 | 0.8172 |
| 4 | -180 | 1.41263e-07 | 2.3006 | 1.1503 |
| 5 | -140 | 2.10452e-07 | 2.0734 | 1.0367 |
| 6 | -100 | 2.52322e-07 | 1.2683 | 0.6342 |
| 7 | -60 | 2.69957e-07 | 0.4885 | 0.2443 |
| 8 | -20 | 3.33847e-07 | 0.0671 | 0.0336 |
| 9 | +20 | 3.33847e-07 | 0.0671 | 0.0336 |
| 10 | +60 | 2.69957e-07 | 0.4885 | 0.2443 |
| 11 | +100 | 2.52322e-07 | 1.2683 | 0.6342 |
| 12 | +140 | 2.10452e-07 | 2.0734 | 1.0367 |
| 13 | +180 | 1.41263e-07 | 2.3006 | 1.1503 |
| 14 | +220 | 6.71838e-08 | 1.6345 | 0.8172 |
| 15 | +260 | 2.45150e-08 | 0.8330 | 0.4165 |
| 16 | +300 | 9.66999e-09 | 0.4375 | 0.2187 |
| **sum, all 16 bins** | | **2.61842e-06** | **18.2057** | **9.1029** |

| quantity | value |
|---|---|
| Σ S(p_m), plain sum of the 16 values (MeV⁻³) | 2.61842e-06 ± 2.4e-08 |
| Σ S(p_m) Δp, Δp = 40 MeV/c, signed axis (MeV⁻²) | 1.0474e-04 ± 9.4e-07 |
| 4π Σ_{p_m>0} S(p_m) p_m² Δp, positive half | **9.1029 ± 0.0498** |

### 3.3 The same integrals for every Q² set

| panel | E_m window | Q² (GeV/c)² | Σ S(p_m) Δp, signed axis (MeV⁻²) | 4π Σ_{p_m>0} S p_m² Δp | note |
|---|---|---|---|---|---|
| fig6_top (¹²C) | 10–25 MeV | 0.64 | 2.3319e-05 ± 1.8e-07 | **2.3683 ± 0.0214** | excluded: ×1.3 above the published panel |
| fig6_top (¹²C) | 10–25 MeV | 1.28 | 1.7147e-05 ± 1.7e-07 | **1.7653 ± 0.0198** |  |
| fig6_top (¹²C) | 10–25 MeV | 1.8 | 1.8032e-05 ± 1.9e-07 | **1.7529 ± 0.0140** | rescale reference (caption) |
| fig6_top (¹²C) | 10–25 MeV | 3.25 | 1.6510e-05 ± 5.0e-07 | **1.7409 ± 0.0358** |  |
| fig6_bot (¹²C) | 30–50 MeV | 0.64 | 1.5136e-05 ± 1.8e-07 | **0.8225 ± 0.0069** | excluded: ×1.3 above the published panel |
| fig6_bot (¹²C) | 30–50 MeV | 1.28 | 1.2390e-05 ± 1.5e-07 | **0.6934 ± 0.0065** |  |
| fig6_bot (¹²C) | 30–50 MeV | 1.8 | 1.1538e-05 ± 1.9e-07 | **0.6077 ± 0.0060** | rescale reference (caption) |
| fig6_bot (¹²C) | 30–50 MeV | 3.25 | 1.2304e-05 ± 6.2e-07 | **0.7759 ± 0.0169** |  |
| fig7 (⁵⁶Fe) | 0–80 MeV | 0.64 | 1.0468e-04 ± 9.0e-07 | **9.6246 ± 0.0693** |  |
| fig7 (⁵⁶Fe) | 0–80 MeV | 1.28 | 1.0474e-04 ± 9.4e-07 | **9.1029 ± 0.0498** |  |
| fig7 (⁵⁶Fe) | 0–80 MeV | 1.8 | 1.0001e-04 ± 1.6e-06 | **8.1500 ± 0.0540** | rescale reference (caption) |
| fig7 (⁵⁶Fe) | 0–80 MeV | 3.25 | 1.0182e-04 ± 2.4e-06 | **8.9114 ± 0.1095** |  |

The signed-axis areas of a panel agree across Q² to 5 % (fig 7) and 5–8 %
(fig 6, Q² = 0.64 aside), as the caption's normalization implies. The 3D
integrals behave differently per panel: the three usable p-shell sets agree
to 1.4 % (1.741–1.765), while the s-shell sets spread over 0.61–0.78 and the
iron sets over 8.2–9.6, because those Q² sets differ at large |p_m|, where
the p_m² weight is largest.

Reproduce:

```bash
pixi run python report/dutta-integral/integrate_dutta.py --files fig6_top_q1p2 fig6_bot_q1p2 fig7_q1p2
```

"""S^D extraction (plan step 4): the experimental (distorted) spectral function
from GENIE events via Dutta's PWIA estimator, on an ABSOLUTE per-nucleus scale.

Per (Em, pm) bin:   S^D = [sigma_tot/N_gen * sum_i 1/(E_p,i p_p,i sigma_cc1,i)] / H(bin)
    weights   1/deforest(...)      [sr^2 / (ub MeV^2)]     (deforest.py, flag 0)
    sigma_tot from the production's own spline [ub]        (build_cache_sd.py)
    H         flat companion MC    [MeV^2 sr^2]            (phase_space_h.py)
    ->  S^D in MeV^-4;  y(Em) = sum_l S^D * (4pi/3)(pm_hi^3 - pm_lo^3) over pm < 300
        in MeV^-1 -- the fig9 observable, with NO area matching.

Event masks match the H fiducials exactly: variant (a) q2win + the El bounds
stored in H_q2win.npz; variant (b) the acceptance cache as-is. Bins with
nflat < 50 are masked (acceptance edges, as in the experiment); the H MC error
(Herr) is propagated. For variant (b) the pm sphere is only partially covered:
y(Em) sums the unmasked bins and leans on the isotropy of S in the pm
direction; rows with < 95 % Vol3 coverage are drawn open.

Figures:
    sd_2d_maps.png        2 x 5 grid of S^D(Em, pm) maps (q2win / accept rows)
    sd_extraction_fig9.png  y(Em) absolute overlay on Dutta fig9 + ratio panel.
        The data are occupancy-normalized (integral 6.08 ~ Z, open question);
        GENIE S^D is absolute distorted strength, expected LOWER by roughly the
        transparency-like factor -- the dashed guide marks T/1.11 = 0.54.
        UnifiedQEL is additionally extracted through the acceptance fiducial
        (open circles): agreement of the two fiducials (H volumes differing by
        orders of magnitude) validates the estimator chain end-to-end.

Prints the window integrals int S^D dEm d3pm (0 <= Em < 80, pm < 300) per
model vs the paper's absorbed scale (0.60/1.11 x 6 ~ 3.2) and the data file's
occupancy integral (6.08).
"""
import sys

sys.path.insert(0, "results/template")
sys.path.insert(0, "results/prd-analyzer-v0")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis,
                        FS_LABEL, FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)
import samples as S
from deforest import deforest

CACHE = f"{S.CACHE_DIR}/sd"
DATA = "data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat"
NFLAT_MIN = 50
PM_INT_MAX = 300.0      # fig9 pm integration window [MeV/c]


def extract(model, variant):
    """Returns (Smap, Serr, usable) on the H grid -- S^D in MeV^-4."""
    c = dict(np.load(f"{CACHE}/{model}_{variant}.npz"))
    h = dict(np.load(f"{CACHE}/H_{variant}.npz"))
    em_e, pm_e = h["em_edges"], h["pm_edges"]

    m = np.ones(len(c["El"]), bool)
    if variant == "q2win":                       # the H fiducial's El bounds
        lo, hi = h["el_bounds"] / 1e3
        m &= (c["El"] >= lo) & (c["El"] <= hi)

    w = 1.0 / deforest(c["El"][m] * 1e3, np.radians(c["theta_e"][m]),
                       c["Q2"][m] * 1e6, c["nu"][m], c["qmag"][m],
                       c["Ep"][m], c["pp"][m], c["p_miss"][m],
                       c["sin_gamma"][m], c["cos_phi"][m], flag=0)
    Em, pm = c["E_miss"][m], c["p_miss"][m]

    num = np.histogram2d(Em, pm, bins=(em_e, pm_e), weights=w)[0]
    num2 = np.histogram2d(Em, pm, bins=(em_e, pm_e), weights=w ** 2)[0]
    scale = float(c["sigma_ub"][0]) / float(c["ntot"][0])

    usable = (h["nflat"] >= NFLAT_MIN) & (num > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        Smap = np.where(usable, scale * num / h["H"], np.nan)
        rel2 = num2 / num ** 2 + (h["Herr"] / h["H"]) ** 2
        Serr = np.where(usable, np.abs(Smap) * np.sqrt(rel2), np.nan)
    return Smap, Serr, usable, em_e, pm_e


def em_curve(Smap, Serr, usable, pm_e):
    """y(Em) = sum_l S^D Vol3(l) over pm < PM_INT_MAX; returns (y, yerr, coverage)."""
    sel = pm_e[1:] <= PM_INT_MAX
    vol3 = (4.0 * np.pi / 3.0) * (pm_e[1:] ** 3 - pm_e[:-1] ** 3)
    v = vol3[sel]
    Sm, Se, us = Smap[:, sel], Serr[:, sel], usable[:, sel]
    y = np.nansum(np.where(us, Sm, 0.0) * v, axis=1)
    yerr = np.sqrt(np.nansum((np.where(us, Se, 0.0) * v) ** 2, axis=1))
    coverage = (us * v).sum(axis=1) / v.sum()
    return y, yerr, coverage


# ---------------------------------------------------------------- run all extractions
res = {}
for m in S.MODELS:
    res[m] = {v: extract(m, v) for v in ("q2win", "accept")}
em_e = res[S.MODELS[0]]["q2win"][3]
pm_e = res[S.MODELS[0]]["q2win"][4]
em_c = 0.5 * (em_e[:-1] + em_e[1:])

# data + its uncertainty prescription (open_questions.md)
dem, dsf, _, dstat = np.loadtxt(DATA, unpack=True)
dtot = np.sqrt(dstat**2 + (0.02 * dsf)**2 + (0.05 * dsf)**2)
dtot[np.isclose(dem, 17.5)] = 0.081 * dsf[np.isclose(dem, 17.5)]
dtot[np.isclose(dem, 22.5)] = 0.047 * dsf[np.isclose(dem, 22.5)]

# ---------------------------------------------------------------- figure 1: 2D maps
apply_style()
import matplotlib.pyplot as plt              # noqa: E402
from matplotlib.colors import LogNorm        # noqa: E402

fig, axes = plt.subplots(2, 5, figsize=(22, 9), sharex=True, sharey=True)
vmax = max(np.nanmax(res[m]["q2win"][0]) for m in S.MODELS)
for j, m in enumerate(S.MODELS):
    for i, v in enumerate(("q2win", "accept")):
        Smap = res[m][v][0]
        pc = axes[i, j].pcolormesh(em_e, pm_e, Smap.T,
                                   norm=LogNorm(vmin=vmax * 1e-5, vmax=vmax),
                                   cmap="viridis")
        axes[i, j].set_title(f"{S.label(m)} [{v}]", fontsize=11)
        if i == 1:
            axes[i, j].set_xlabel(r"E$_m$  [MeV]", fontsize=FS_LABEL - 2)
        if j == 0:
            axes[i, j].set_ylabel(r"p$_m$  [MeV/c]", fontsize=FS_LABEL - 2)
fig.colorbar(pc, ax=axes, shrink=0.85, label=r"S$^D$(E$_m$, p$_m$)  [MeV$^{-4}$]")
fig.suptitle("extracted distorted spectral function — PWIA estimator, absolute scale",
             fontsize=FS_SUPTITLE)
fig.savefig("results/prd-analyzer-v0/sd_2d_maps.png", dpi=DPI)
print("wrote results/prd-analyzer-v0/sd_2d_maps.png")

# ---------------------------------------------------------------- figure 2: fig9 overlay
fig2, (axT, axR) = plt.subplots(2, 1, figsize=(8.5, 9), sharex=True,
                                height_ratios=[2.4, 1.0])
I_DATA = dsf.sum() * 5.0
rows = slice(4, 20)                          # Em in [0, 80): aligns 1:1 with the data bins
print(f"\nwindow integrals  int S^D dEm d3pm  (0<=Em<80, pm<300)   "
      f"[data occupancy integral = {I_DATA:.2f}, paper absorbed scale ~ 3.24]")
for m in S.MODELS:
    y, yerr, cov = em_curve(*[res[m]["q2win"][k] for k in (0, 1, 2)], pm_e)
    axT.stairs(y[rows], em_e[4:21], color=S.color(m), linewidth=S.lw(m, base=1.8),
               zorder=S.zorder(m), label=S.label(m))
    axT.errorbar(em_c[rows], y[rows], yerr=yerr[rows], fmt="none",
                 ecolor=S.color(m), elinewidth=1.0, zorder=S.zorder(m))
    nz = dsf > 0
    r = y[rows][nz] / dsf[nz]
    rerr = r * np.sqrt((yerr[rows][nz] / y[rows][nz]) ** 2 + (dtot[nz] / dsf[nz]) ** 2)
    axR.errorbar(dem[nz], r, yerr=rerr, fmt="o", ms=4, color=S.color(m),
                 zorder=S.zorder(m))
    I = (y[rows] * 5.0).sum()
    Ierr = np.sqrt(((yerr[rows]) ** 2).sum()) * 5.0
    print(f"  {m:15s} I = {I:5.3f} +- {Ierr:5.3f}   I/6.08 = {I/I_DATA:5.3f}   "
          f"I/3.24 = {I/3.24:5.3f}")

# UnifiedQEL through the acceptance fiducial (partial pm-sphere coverage ->
# a lower bound on the full pm<300 integral; the rigorous cross-check below
# compares the two fiducials over their COMMON usable bins)
yb, yberr, covb = em_curve(*[res["UnifiedQEL"]["accept"][k] for k in (0, 1, 2)], pm_e)
vis = yb[rows] > 0
axT.errorbar(em_c[rows][vis], yb[rows][vis], yerr=yberr[rows][vis], fmt="o",
             ms=5, mfc="white", mec=S.color("UnifiedQEL"),
             ecolor=S.color("UnifiedQEL"), zorder=8,
             label="UnifiedQEL, acceptance fiducial (partial $p_m$ cov.)")

axT.errorbar(dem, dsf, yerr=dtot, fmt="none", ecolor="0.6", elinewidth=3,
             alpha=0.8, zorder=9)
axT.errorbar(dem, dsf, yerr=dstat, fmt="s", ms=5, color="black", capsize=2,
             zorder=10, label="Dutta Fig. 9 (occupancy-normalized)")

style_axis(axT, title=r"$^{12}$C(e,e'p), $Q^2$ = 1.28 (GeV/$c$)$^2$ — absolute S$^D$",
           xlabel=None, logx=False, logy=False, ymin=None)
axT.set_ylabel(r"$\int_{p_m<300} S^{D}\,d^3p_m$   (MeV$^{-1}$)", fontsize=FS_LABEL)
axT.set_xlim(0, 85)
axT.set_ylim(0, 0.7)
axT.legend(fontsize=FS_LEGEND - 2, title="PWIA estimator, q2win fiducial",
           title_fontsize=FS_LEGEND_TITLE - 2)

axR.axhline(1.0, color="0.4", lw=1.0)
axR.axhline(0.60 / 1.11, color="0.4", lw=1.0, ls="--")
axR.text(81, 0.60 / 1.11, "T/1.11 = 0.54", fontsize=10, va="bottom", ha="right",
         color="0.3")
style_axis(axR, title=None, xlabel=r"$E_m$  (MeV)", logx=False, logy=False, ymin=None)
axR.set_ylabel("GENIE / data", fontsize=FS_LABEL - 2)
axR.set_ylim(0, 1.6)
fig2.suptitle("S$^D$ extraction vs Dutta Fig. 9 — absolute, no area matching\n"
              "data occupancy-normalized (∫=6.08) vs GENIE absolute distorted strength",
              fontsize=FS_SUPTITLE - 2)
fig2.tight_layout()
fig2.savefig("results/prd-analyzer-v0/sd_extraction_fig9.png", dpi=DPI)
print("wrote results/prd-analyzer-v0/sd_extraction_fig9.png")

# cross-fiducial validation over the COMMON usable (Em, pm) bins -- an
# apples-to-apples comparison of the two extractions (no isotropy assumption):
# bin-by-bin S^D from wildly different fiducials and H volumes must agree.
Sa, Sea, ua = res["UnifiedQEL"]["q2win"][:3]
Sb, Seb, ub = res["UnifiedQEL"]["accept"][:3]
common = ua & ub & np.isfinite(Sa) & np.isfinite(Sb)
common[:, pm_e[1:] > PM_INT_MAX] = False
ra = Sa[common] / Sb[common]
pull = (Sa[common] - Sb[common]) / np.sqrt(Sea[common] ** 2 + Seb[common] ** 2)
print(f"\ncross-fiducial S^D bin comparison (UnifiedQEL, {common.sum()} common bins, "
      f"pm < {PM_INT_MAX:.0f}):")
print(f"  median a/b = {np.median(ra):.3f}   p10/p90 = {np.percentile(ra,10):.3f}/"
      f"{np.percentile(ra,90):.3f}   median |pull| = {np.median(np.abs(pull)):.2f}")

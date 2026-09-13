#!/usr/bin/env python3
"""
tball_pdf.py: probability density of T_ball, the struck proton's kinetic energy in INCL's
ground state, analytic vs sampled.

Ball (INCL ground state, strict or fuzzy -- same marginal):  |p|^3 uniform on [0, p_F^3]
    f(p) = 3 p^2 / p_F^3,   T = sqrt(p^2 + m^2) - m,  dp/dT = (T + m)/p
    f(T) = 3 (T + m) sqrt(T (T + 2m)) / p_F^3            on [0, T_F]
Truncated ball at the sampled radius (fork ResamplingHitNucleon):  |p|^3 uniform on [p_min(r)^3, p_F^3]
    f(p | r) = 3 p^2 / (p_F^3 - p_min(r)^3)  for p >= p_min(r),   p_min(r) = p_F u(r),  u = F^(1/3)
    f(p)     = (3 p^2 / p_F^3) W(p/p_F),   W(x) = int_{u(r) < x} rho_r(r) / (1 - u(r)^3) dr
    f(T)     = f(p) (T + m)/p
with rho_r(r) the radial density of the struck nucleons, r^2 [rho(r) - rho(R_max)] normalised
(what INCL's sampler generates).
Outputs tball_pdf.png / .txt next to the script.
"""
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "results" / "template"))
import histdiag as hd
from incl_nucleus import INCLNucleus

nuc = INCLNucleus()                      # C12 protons, fuzzy 0.5
m, pF, TF = nuc.m, nuc.pF, nuc.TF
rng = np.random.default_rng(7)
n = 400_000
nucs = nuc.sample(n, rng)
T_ball = nucs.T
T_res = nuc.resample_at_r(nucs.r_vec, rng).T

edges = np.linspace(0.0, TF, 41)
Tc = 0.5 * (edges[1:] + edges[:-1])

def f_ball(T):
    p = np.sqrt(T * (T + 2 * m))
    return 3.0 * (T + m) * p / pF**3

# W(x) on a fine r grid
rf = np.linspace(0.0, nuc.r_max, 200001)
rho_r = rf**2 * (nuc.density(rf) - nuc.density(nuc.r_max)); rho_r /= np.trapezoid(rho_r, rf)
u = nuc.min_p_from_r(rf)
w = rho_r / np.maximum(1.0 - u**3, 1e-12)
Wcum = np.concatenate([[0.0], np.cumsum(0.5 * (w[1:] + w[:-1]) * np.diff(rf))])  # int_0^r
def f_res(T):
    p = np.sqrt(T * (T + 2 * m)); x = p / pF
    # W(x) = int over r with u(r) < x; u is monotonic in r -> r_x = r at which u = x
    r_x = np.interp(x, u, rf)
    W = np.interp(r_x, rf, Wcum)
    return 3.0 * p * (T + m) * W / pF**3

def binned(f):
    Tf = np.linspace(0.0, TF, 40001); y = f(Tf)
    F = np.concatenate([[0.0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(Tf))])
    return np.diff(np.interp(edges, Tf, F)), F[-1]

with open(HERE / "tball_pdf.txt", "w") as fh:
    for name, T, f in (("ball", T_ball, f_ball), ("truncated ball (resample)", T_res, f_res)):
        cnt, _ = np.histogram(T, edges)
        model, norm = binned(f)
        model *= cnt.sum()
        pull = (cnt - model) / np.sqrt(model)
        line = (f"{name}: analytic normalisation {norm:.6f}; <T> sampled {T.mean():.3f} MeV, analytic "
                f"{np.trapezoid(np.linspace(0, TF, 40001) * f(np.linspace(0, TF, 40001)), np.linspace(0, TF, 40001)):.3f}; "
                f"Poisson chi2/ndf = {(pull**2).sum() / cnt.size:.2f}, max |pull| = {np.abs(pull).max():.2f}")
        print(line); fh.write("# " + line + "\n")
        hd.compare1d(cnt, model, edges, labels=(f"sampled {name}", "analytic"), xname="T_ball [MeV]",
                     table=False, quiet=True, save=fh)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
Tf = np.linspace(0, TF, 400)
for T, f, c, lab in ((T_ball, f_ball, "C0", "ball (INCL ground state)"),
                     (T_res, f_res, "C1", "truncated ball at r (fork resampling)")):
    cnt, _ = np.histogram(T, edges, density=True)
    ax.stairs(cnt, edges, fill=True, color=c, alpha=0.35, label=lab + ", sampled")
    ax.plot(Tf, f(Tf), color=c, lw=1.6, label=lab + ", analytic")
ax.axvline(TF, color="k", ls=":", lw=1); ax.text(TF, ax.get_ylim()[1] * 0.98, r" $T_F$", va="top", fontsize=9)
ax.set_xlabel(r"$T_{\rm ball}$ [MeV]"); ax.set_ylabel("probability density [1/MeV]")
ax.set_title(r"$f(T_{\rm ball})$, C12 protons, $p_F$ = 270.3 MeV/c", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="upper left"); ax.grid(alpha=0.3)
fig.savefig(HERE / "tball_pdf.png", dpi=140)
print("wrote", HERE / "tball_pdf.png", "+ .txt")

"""INCL++ ground state as realized in the GENIE record (C12, GEM26_44b) vs the
INCL++ source formulas — position, momentum, local energy, potential.

Model side (INCL++ source, genie_inclxx install; see
docs/incl-ground-state-review.md for the citations):
  density  rho(r) = (1 + alpha x^2) exp(-x^2), x = r/a   (modified harmonic
           oscillator, 6 < A <= 19), HFB parameters for C12:
           proton a = 1.72905 fm, alpha = 0.849882; neutron a = 1.71874, 0.83426
  r-p map  F(R(p)) = (p/p_F)^3 with F the CDF of -R^3 rho'(R) on [0, R_max],
           R_max = 5.65 fm; p_F = 1.37 hbar c = 270.34 MeV/c (global, C12 isospin
           factor 1); p_min(r) = p_F F(r)^{1/3} = the local Fermi momentum
  local E  T_loc(r) = sqrt(p_min(r)^2 + m^2) - m,  m = 938.2796 MeV (INCL mass)
  well     V0 = T_F + S = 38.17 + 6.83 = 45.00 MeV, V(T) = V0 - 0.287 (T - T_F)
           above T_F, clipped at 0 (IsospinEnergyPotential)
Record side (dump_hitnuc CSV of the hit nucleon: p, r, E): the resampling
throws p uniformly in the p_F ball at the sampled r and accepts p > p_min(r)
(KE > local energy), so the prediction per r is a p^2 density truncated below
at p_min(r).  The stored E is on-shell with the INCL mass.

Usage:
  pixi run python results/template/make_incl_groundstate_record.py \
      [--csv results/prd-analyzer-v0.1/cache/hitnuc_c12/GEM26_44b_05_000.csv]
Writes results/prd-analyzer-v1.0/incl_groundstate_record_c12.png and prints
the model-vs-record table.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "results/template")
import numpy as np
from plot_style import (apply_style, new_panels, style_axis, FS_LABEL,
                        FS_LEGEND, FS_LEGEND_TITLE, FS_SUPTITLE, DPI)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/prd-analyzer-v1.0/incl_groundstate_record_c12.png"
CSV = REPO / "results/prd-analyzer-v0.1/cache/hitnuc_c12/GEM26_44b_05_000.csv"

M_INCL = 938.2796                     # G4INCLParticleTable theINCLNucleonMass
P_F = 1.37 * 197.328                  # PhysicalConstants::Pf
R_MAX = 5.65                          # getMaximumNuclearRadius(A=12)
T_F = np.sqrt(P_F ** 2 + M_INCL ** 2) - M_INCL
S_INCL = 6.83
V0 = T_F + S_INCL
ALPHA_E = 0.223                       # NuclearPotentialEnergyIsospin
HFB = {2212: (1.72905, 0.849882), 2112: (1.71874, 0.83426)}   # a [fm], alpha


def mho_tables(a, alpha, n=4000):
    r = np.linspace(0.0, R_MAX, n)
    x = r / a
    rho = (1.0 + alpha * x ** 2) * np.exp(-x ** 2)
    drho = (2.0 * x / a) * (alpha - 1.0 - alpha * x ** 2) * np.exp(-x ** 2)
    g = np.clip(-r ** 3 * drho, 0.0, None)              # reflection-radius pdf
    F = np.concatenate([[0.0], np.cumsum(0.5 * (g[1:] + g[:-1]) * np.diff(r))])
    F /= F[-1]
    pos = r ** 2 * rho                                  # position marginal
    pos_cdf = np.concatenate([[0.0], np.cumsum(0.5 * (pos[1:] + pos[:-1]) * np.diff(r))])
    pos_pdf = pos / pos_cdf[-1]
    p_min = P_F * np.cbrt(F)
    return r, pos_pdf, p_min


def p_percentile(p_min, q):
    """q-th percentile of a p^2 density on [p_min, p_F]."""
    return np.cbrt(p_min ** 3 + q * (P_F ** 3 - p_min ** 3))


def p_mean(p_min):
    return 0.75 * (P_F ** 4 - p_min ** 4) / (P_F ** 3 - p_min ** 3)


def t_of_p(p):
    return np.sqrt(p ** 2 + M_INCL ** 2) - M_INCL


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(CSV))
    ap.add_argument("--ladder", default=str(REPO / "results/prd-analyzer-v1.0/cache/ladder_c12/GEM26_44b_05_000.npz"),
                    help="v1.0 ladder cache (same events, qel && hit-p): gives the "
                         "kinematics-side initial nucleon p_i = |p_p' - q| and "
                         "E_i = m_p - (omega - T_p')")
    args = ap.parse_args()

    d = np.genfromtxt(args.csv, delimiter=",", names=True)
    pdg = d["pdg"].astype(int)
    p = np.sqrt(d["px"] ** 2 + d["py"] ** 2 + d["pz"] ** 2) * 1000.0
    E = d["E"] * 1000.0
    r = d["r"]
    T = t_of_p(p)
    frac = {c: float(np.mean(pdg == c)) for c in (2212, 2112)}
    print(f"N={len(p):,}  proton fraction {frac[2212]:.3f}")

    # ---- model tables per species, then the species-weighted mixture --------
    tab = {c: mho_tables(*HFB[c]) for c in HFB}
    r_grid = tab[2212][0]
    pos_pdf = sum(frac[c] * tab[c][1] for c in HFB)
    p_min_mix = sum(frac[c] * tab[c][2] for c in HFB)      # nearly identical curves

    # ---- record: per-r percentiles ------------------------------------------
    r_edges = np.arange(0.0, R_MAX + 1e-9, 0.25)
    r_ctr = 0.5 * (r_edges[:-1] + r_edges[1:])
    idx = np.digitize(r, r_edges) - 1
    q01 = np.full(len(r_ctr), np.nan); q05 = q01.copy(); q50 = q01.copy()
    pm = q01.copy(); tm = q01.copy(); em = q01.copy(); cnt = np.zeros(len(r_ctr), int)
    for i in range(len(r_ctr)):
        s = idx == i
        cnt[i] = s.sum()
        if s.sum() >= 100:
            q01[i], q05[i], q50[i] = np.percentile(p[s], [1, 5, 50])
            pm[i] = p[s].mean(); tm[i] = T[s].mean(); em[i] = (E[s] - M_INCL).mean()

    # model on the bin centres (per-r truncated-ball predictions)
    pmin_c = np.interp(r_ctr, r_grid, p_min_mix)
    q01_m, q05_m, q50_m = (p_percentile(pmin_c, q) for q in (0.01, 0.05, 0.50))
    pm_m = p_mean(pmin_c)

    # marginal |p| prediction: integrate the truncated ball over the r marginal
    p_edges = np.arange(0.0, 300.0 + 1e-9, 5.0)
    p_ctr = 0.5 * (p_edges[:-1] + p_edges[1:])
    w_r = pos_pdf * np.gradient(r_grid)
    dens = np.zeros(len(p_ctr))
    for wr, pmn in zip(w_r, p_min_mix):
        if pmn >= P_F - 1e-9:          # r -> R_max: nothing left to accept
            continue
        ok = (p_ctr > pmn) & (p_ctr < P_F)
        dens[ok] += wr * 3.0 * p_ctr[ok] ** 2 / (P_F ** 3 - pmn ** 3)
    dens /= (dens * np.diff(p_edges)).sum()
    ball = np.where(p_ctr < P_F, 3.0 * p_ctr ** 2 / P_F ** 3, 0.0)

    # ---- printed comparison --------------------------------------------------
    r_mean_model = float((r_grid * pos_pdf * np.gradient(r_grid)).sum())
    print(f"<r>: record {r.mean():.3f} fm   model r^2 rho(MHO, HFB) {r_mean_model:.3f} fm"
          f"   RMS record {np.sqrt(np.mean(r**2)):.3f}")
    p_mean_model = float((p_ctr * dens * np.diff(p_edges)).sum())
    print(f"<|p|>: record {p.mean():.1f}   model (truncated ball) {p_mean_model:.1f}"
          f"   pure ball {0.75 * P_F:.1f} MeV/c;  record max {p.max():.1f} vs p_F {P_F:.2f}")
    print(f"E - m_INCL  vs  T = sqrt(p^2+m_INCL^2) - m_INCL:  mean diff "
          f"{np.mean((E - M_INCL) - T):.3f} MeV, max |diff| {np.max(np.abs((E - M_INCL) - T)):.3f}")
    print(f"T_F = {T_F:.2f} MeV, S = {S_INCL}, V0 = {V0:.2f} MeV")
    print("\n  r bin      N     p1%: rec  model   p5%: rec  model   <p>: rec  model   T_loc(r)")
    for i in range(len(r_ctr)):
        if cnt[i] < 100:
            continue
        print(f" {r_edges[i]:4.2f}-{r_edges[i+1]:4.2f} {cnt[i]:7d}   {q01[i]:6.1f} {q01_m[i]:6.1f}"
              f"    {q05[i]:6.1f} {q05_m[i]:6.1f}    {pm[i]:6.1f} {pm_m[i]:6.1f}   {t_of_p(pmin_c[i]):6.2f}")

    # ---- figure -----------------------------------------------------------------
    apply_style()
    fig, axes = new_panels(ncols=2, nrows=3, sharey=False)

    ax = axes[0]                                             # position
    h, _ = np.histogram(r, bins=np.arange(0.0, 6.01, 0.1), density=True)
    ax.stairs(h, np.arange(0.0, 6.01, 0.1), color="C0", lw=1.8,
              label=f"record (N={len(r):,})")
    ax.plot(r_grid, pos_pdf, "C1--", lw=1.8,
            label=r"$r^2\rho_{\rm MHO}(r)$, HFB $a,\alpha$ (p/n mix)")
    ax.axvline(R_MAX, color="0.5", ls=":", lw=1.0)
    style_axis(ax, title="position: sampled radius", xlabel=r"$r$  [fm]",
               logx=False, logy=False, ymin=None)
    ax.set_ylabel("density  [fm$^{-1}$]", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 2, loc="upper right",
              title=r"$R_{max}$ = 5.65 fm dotted", title_fontsize=FS_LEGEND_TITLE - 2)

    ax = axes[1]                                             # momentum marginal
    hp, _ = np.histogram(p, bins=p_edges, density=True)
    ax.stairs(hp, p_edges, color="C0", lw=1.8, label="record")
    ax.stairs(dens, p_edges, color="C1", lw=1.8, ls="--",
              label=r"ball truncated at $p_{min}(r)$, $\int dr$")
    ax.stairs(ball, p_edges, color="0.5", lw=1.2, ls=":",
              label=r"pure ball $3p^2/p_F^3$")
    style_axis(ax, title="momentum: hit-nucleon $|p|$",
               xlabel=r"$|p|$  [MeV/c]", logx=False, logy=False, ymin=None)
    ax.set_ylabel("density  [(MeV/c)$^{-1}$]", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 2, loc="upper left",
              title=f"$p_F$ = {P_F:.1f} MeV/c", title_fontsize=FS_LEGEND_TITLE - 2)

    ax = axes[2]                                             # floor vs r
    ax.plot(r_ctr, q01, "o", color="C0", ms=4, label="record 1st percentile")
    ax.plot(r_ctr, q05, "s", color="C2", ms=4, label="record 5th percentile")
    ax.plot(r_ctr, pm, "^", color="C3", ms=4, label=r"record $\langle p\rangle(r)$")
    ax.plot(r_grid, p_min_mix, "k-", lw=1.8, label=r"$p_{min}(r)=p_F F(r)^{1/3}$ (INCL)")
    ax.plot(r_ctr, q01_m, "-", color="C0", lw=1.2, alpha=0.8)
    ax.plot(r_ctr, q05_m, "-", color="C2", lw=1.2, alpha=0.8)
    ax.plot(r_ctr, pm_m, "-", color="C3", lw=1.2, alpha=0.8, label="truncated-ball model (lines)")
    ax.axhline(P_F, color="0.5", ls=":", lw=1.0)
    style_axis(ax, title="acceptance floor: $|p|$ vs $r$", xlabel=r"$r$  [fm]",
               logx=False, logy=False, ymin=None)
    ax.set_ylabel(r"$|p|$  [MeV/c]", fontsize=FS_LABEL)
    ax.set_ylim(0, 300)
    ax.legend(fontsize=FS_LEGEND - 3, loc="lower right")

    ax = axes[3]                                             # energies vs r
    ax.plot(r_grid, t_of_p(p_min_mix), "k-", lw=1.8,
            label=r"$T_{loc}(r)=\sqrt{p_{min}^2+m^2}-m$ (local energy)")
    ax.plot(r_ctr, tm, "^", color="C3", ms=4, label=r"record $\langle T\rangle(r)$")
    ax.plot(r_ctr, em, "x", color="C0", ms=5, label=r"record $\langle E-m_{INCL}\rangle(r)$")
    ax.axhline(T_F, color="C1", ls="--", lw=1.2, label=f"$T_F$ = {T_F:.1f} MeV")
    ax.axhline(V0, color="C4", ls="-.", lw=1.2, label=f"$V_0=T_F+S$ = {V0:.1f} MeV")
    style_axis(ax, title="energies vs $r$ (record is on-shell)", xlabel=r"$r$  [fm]",
               logx=False, logy=False, ymin=None)
    ax.set_ylabel("MeV", fontsize=FS_LABEL)
    ax.set_ylim(0, 50)
    ax.legend(fontsize=FS_LEGEND - 3, loc="lower right")

    # ---- kinematics side: the initial nucleon the QE kinematics conserved ----
    lad = dict(np.load(args.ladder))
    is_p = pdg == 2212
    rp, prec_p, T_p = r[is_p], p[is_p], T[is_p]
    p_kin = lad["p3"]                                   # |p_p' - q|
    M_P = 938.272
    Em_pre = lad["E3"] + lad["p3"] ** 2 / (2.0 * 10.2525481e3)   # omega - T_p'
    assert len(p_kin) == len(rp), "ladder cache and dump (protons) must be the same events"
    print(f"kinematics side (protons): <p_i>={p_kin.mean():.1f} MeV/c, corr(p_i, r)={np.corrcoef(p_kin, rp)[0, 1]:+.3f};"
          f"  E_m(pre-FSI)=omega-T_p': mean {Em_pre.mean():.2f}, min {Em_pre.min():.2f}, max {Em_pre.max():.2f};"
          f"  max|E_m - (V0 - T_rec)| = {np.max(np.abs(Em_pre - (V0 - T_p))):.3f} MeV")
    pk = np.full(len(r_ctr), np.nan); idxp = np.digitize(rp, r_edges) - 1
    for i in range(len(r_ctr)):
        s_ = idxp == i
        if s_.sum() >= 100:
            pk[i] = p_kin[s_].mean()
    pmin_p = np.interp(r_ctr, r_grid, tab[2212][2])
    p_red_model = np.sqrt(np.clip((np.sqrt(pm ** 2 + M_INCL ** 2) - t_of_p(pmin_p)) ** 2 - M_INCL ** 2, 0, None))

    ax = axes[4]                                             # p_i vs r
    hk, _ = np.histogram(p_kin, bins=p_edges, density=True)
    ax.stairs(hp, p_edges, color="C0", lw=1.4, label=r"record $|p|$ (all)")
    ax.stairs(hk, p_edges, color="C3", lw=1.8, label=r"kinematics $|\vec p_{p'}-\vec q\,|$ (protons)")
    style_axis(ax, title="momentum used by the QE kinematics",
               xlabel=r"$|p|$  [MeV/c]", logx=False, logy=False, ymin=None)
    ax.set_ylabel("density  [(MeV/c)$^{-1}$]", fontsize=FS_LABEL)
    ax2 = ax.inset_axes([0.08, 0.42, 0.42, 0.45])
    ax2.plot(r_ctr, pm, "^", color="C0", ms=3, label=r"record $\langle p\rangle(r)$")
    ax2.plot(r_ctr, pk, "v", color="C3", ms=3, label=r"kinematics $\langle p_i\rangle(r)$")
    ax2.plot(r_ctr, p_red_model, "k-", lw=1.0, label=r"$\sqrt{(E_{ball}-T_{loc}(r))^2-m^2}$")
    ax2.set_xlabel(r"$r$ [fm]", fontsize=FS_LEGEND - 3); ax2.set_ylabel("MeV/c", fontsize=FS_LEGEND - 3)
    ax2.tick_params(labelsize=FS_LEGEND - 4); ax2.set_ylim(0, 300)
    ax2.legend(fontsize=FS_LEGEND - 5, loc="lower left", frameon=False)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right")

    ax = axes[5]                                             # E_m pre-FSI
    e_edges = np.arange(0.0, 50.1, 1.0)
    he, _ = np.histogram(Em_pre, bins=e_edges, density=True)
    ax.stairs(he, e_edges, color="C3", lw=1.8, label=r"$E_m=\omega-T_{p'}$ (pre-FSI, protons)")
    hv, _ = np.histogram(V0 - T_p, bins=e_edges, density=True)
    ax.stairs(hv, e_edges, color="k", lw=1.2, ls="--", label=r"$V_0 - T_{rec}$")
    ax.axvline(S_INCL, color="C1", ls=":", lw=1.2, label=f"$S$ = {S_INCL} MeV")
    ax.axvline(V0, color="C4", ls="-.", lw=1.2, label=f"$V_0$ = {V0:.1f} MeV")
    style_axis(ax, title="pre-FSI binding: $E_m = V_0 - T_{rec}$",
               xlabel=r"$E_m$  [MeV]", logx=False, logy=False, ymin=None)
    ax.set_ylabel("density  [MeV$^{-1}$]", fontsize=FS_LABEL)
    ax.legend(fontsize=FS_LEGEND - 3, loc="upper right")

    fig.suptitle("INCL++ ground state in the GENIE record — GEM26_44b_05_000 "
                 "(e$^-$ C12, 500k)\n"
                 "steps/points = record;  lines = INCL++ source formulas",
                 fontsize=FS_SUPTITLE - 2)
    fig.tight_layout()
    fig.savefig(OUT, dpi=DPI)
    print("wrote", OUT)

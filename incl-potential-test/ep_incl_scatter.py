#!/usr/bin/env python3
"""
ep_incl_scatter.py: e + p(INCL ground state) -> e' + p' with the GENIE-INCL vertex
====================================================================================

The bound-nucleon step after ep_phase_space.py (free proton at rest). The target
proton comes from `INCLNucleus` (incl_nucleus.py): r-p correlated position and
momentum, INCL potential V0 = T_F + S, local energy. The vertex follows the fork's
INCL scheme (docs/incl-vertex-local-energy-option-plan.md, "Convention revised",
commit 6bd7803d6):

  1. ground state      (r, p_ball) from the INCL sampler (fuzzy or strict correlation);
                       optionally the fork's truncated-ball redraw at fixed r (--resample)
  2. scattering        two-body phase space e + N -> e' + p' on the LOCAL-FRAME nucleon:
                       on-shell (p_red, E_ball - v_loc(r)) with --local-energy on,
                       (p_ball, E_ball) with --local-energy never  (fork getHitNucleonP4)
  3. energy balance    INCL's InteractionAvatar rule, GENIEAvatar::preInteraction +
                       ViolationLeptonEMomentumFunctor: E_lep' + (E_p' - V(T_p')) must equal
                       E_lep + E_ball - V0. Both products are boosted to the CM of
                       (e + local-frame nucleon), their CM momenta scaled by one factor
                       alpha, boosted back; the proton picks up its energy-dependent
                       potential and, with local energy on, the local-energy fixed point
                       E -> E_scaled + v_loc(r, p) (scaleParticleMomenta). alpha solved by
                       bisection (INCL: RootFinder, |dE| < 1e-4 MeV).
  4. record            initial nucleon = (p_ball, E_ball - V0); lepton and proton = the
                       rescaled ones. Then
                          E_miss = omega - T_p'      (no recoil term, as in the ladders)
                          p_miss = p_p' - q
                       and the closed-form expectation from step 3:
                          E_miss = V0 - T_ball - V(T_p')      (= V0 - T_ball for fast protons)
                          p_miss = p_red (on) / p_ball (never), modulo the local-energy
                                   fixed point of slow outgoing protons.

Pure phase space, no cross section weight: the aim is the bookkeeping of the potential
and the local energy, not a physics spectrum. Kinematics in MeV.

Usage:
    pixi run python incl-potential-test/ep_incl_scatter.py --local-energy on
    pixi run python incl-potential-test/ep_incl_scatter.py --local-energy never
Outputs (next to the script unless --outdir): <stem>.png, <stem>.txt (histdiag readouts),
<stem>.npz (event arrays).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "results" / "template"))
import histdiag as hd                                                     # noqa: E402
from ep_phase_space import boost, load_masses, mass2, missing, scatter    # noqa: E402
from incl_nucleus import INCLNucleus, LOCE_ACCURACY, LOCE_MAX_ITER         # noqa: E402


def incl_energy_balance(nuc, r, k_lab, kp, pp, beta, old_total, local_energy,
                        alpha_lo=0.0, alpha_hi=1.5, n_bisect=60):
    """Port of GENIEAvatar::ViolationLeptonEMomentumFunctor + RootFinder::solve, vectorised.

    kp, pp: lepton and proton lab 4-vectors from the scattering (n,4); beta: the avatar's
    boost vector (n,3) = (k + p_loc)/(E_lep + E_loc); old_total: E_lep + E_ball - V(ball).
    Returns alpha (n,), kp_final (n,4), pp_final (n,4), V_final (n,), ok (n,) bool.
    """
    m = nuc.m
    me2 = mass2(kp)
    kcm = boost(kp, -beta)[:, 1:]
    pcm = boost(pp, -beta)[:, 1:]

    def evaluate(alpha):
        a = alpha[:, None]
        kl = a * kcm
        kp_lab = boost(np.column_stack([np.sqrt(np.sum(kl**2, axis=1) + me2), kl]), beta)
        pl = a * pcm
        pp_lab = boost(np.column_stack([np.sqrt(np.sum(pl**2, axis=1) + m * m), pl]), beta)
        E = pp_lab[:, 0]
        p3 = pp_lab[:, 1:]
        pmag = np.linalg.norm(p3, axis=1)
        phat = p3 / np.where(pmag > 0, pmag, 1.0)[:, None]
        V = nuc.potential_energy(E - m)
        if local_energy:
            # scaleParticleMomenta: energy = E; loop { setEnergy(energy + locE); adjust p; V; locE }
            energy = E.copy()
            locE = nuc.local_energy(r, pmag)          # rpCorrelate(): reflection momentum = |p|
            for _ in range(LOCE_MAX_ITER):
                E = energy + locE
                pmag = np.sqrt(np.maximum(E**2 - m * m, 0.0))
                V = nuc.potential_energy(E - m)
                locE_new = nuc.local_energy(r, pmag)
                done = np.abs(locE_new - locE) <= LOCE_ACCURACY
                locE = locE_new
                if done.all():
                    break
            p3 = phat * pmag[:, None]
        deltaE = (E - V) + kp_lab[:, 0] - old_total
        return deltaE, kp_lab, np.column_stack([E, p3]), V

    n = kp.shape[0]
    lo = np.full(n, alpha_lo)
    hi = np.full(n, alpha_hi)
    f_lo = evaluate(lo)[0]
    f_hi = evaluate(hi)[0]
    for _ in range(20):  # widen the bracket if needed (INCL bracketRoot)
        bad = f_hi < 0
        if not bad.any():
            break
        hi = np.where(bad, hi * 2.0, hi)
        f_hi = evaluate(hi)[0]
    ok = (f_lo <= 0) & (f_hi >= 0)
    for _ in range(n_bisect):
        mid = 0.5 * (lo + hi)
        f_mid = evaluate(mid)[0]
        lo = np.where(f_mid < 0, mid, lo)
        hi = np.where(f_mid < 0, hi, mid)
    alpha = np.where(ok, 0.5 * (lo + hi), 1.0)   # RootFinder failure: cleanUp -> alpha = 1
    deltaE, kp_f, pp_f, V_f = evaluate(alpha)
    return alpha, kp_f, pp_f, V_f, ok, deltaE


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-n", "--nevents", type=int, default=200_000)
    ap.add_argument("--ebeam", type=float, default=2.445, help="electron beam energy [GeV]")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--local-energy", choices=["on", "never"], default="on",
                    help="vertex local energy (local-energy-BB first-collision/always vs never)")
    ap.add_argument("--rp-coefficient", type=float, default=None,
                    help="r-p correlation coefficient (default INCL: 0.5 protons; 1 = strict)")
    ap.add_argument("--resample", action="store_true",
                    help="apply the fork's truncated-ball momentum redraw at fixed r (GENIE event loop)")
    ap.add_argument("--A", type=int, default=12)
    ap.add_argument("--Z", type=int, default=6)
    ap.add_argument("--outdir", type=Path, default=HERE)
    ap.add_argument("--stem", default=None)
    args = ap.parse_args(argv)
    stem_name = args.stem or f"ep_incl_{'C' if args.Z == 6 else 'Z' + str(args.Z)}{args.A}_lf{args.local_energy}" \
        + ("_resample" if args.resample else "") \
        + (f"_rp{args.rp_coefficient:g}" if args.rp_coefficient is not None else "")
    local_on = args.local_energy == "on"

    m_e_gev, _, msrc = load_masses()
    m_e = m_e_gev * 1e3
    rng = np.random.default_rng(args.seed)
    n = args.nevents
    nuc = INCLNucleus(A=args.A, Z=args.Z, species="proton", rp_coefficient=args.rp_coefficient)
    m = nuc.m
    print(nuc.describe())
    print(f"electron mass {m_e:.6f} MeV from {msrc}; E_beam = {args.ebeam} GeV; N = {n}; seed = {args.seed}; "
          f"local energy = {args.local_energy}; resample = {args.resample}")

    # ---- 1. ground state -----------------------------------------------------------
    nucs = nuc.sample(n, rng)
    if args.resample:
        nucs = nuc.resample_at_r(nucs.r_vec, rng)
    r, p_ball, E_ball, T_ball = nucs.r, nucs.p, nucs.E, nucs.T
    V_ball = nuc.potential_energy(T_ball)          # = V0 for every ball nucleon (T <= T_F)
    floor = nuc.pF * nuc.min_p_from_r(r)
    print(f"ground state: <r> = {r.mean():.3f} fm, rms r = {np.sqrt((r**2).mean()):.3f}, <p> = {p_ball.mean():.2f} MeV/c, "
          f"max p = {p_ball.max():.2f}, corr(p, r) = {np.corrcoef(p_ball, r)[0, 1]:+.3f}, "
          f"below strict floor: {(p_ball < floor).mean():.4f}, V(ball) = {V_ball.min():.3f}..{V_ball.max():.3f} MeV")

    # ---- 2. scattering on the local-frame nucleon -------------------------------------
    if local_on:
        E_loc, p_loc, vloc = nuc.local_frame(r, nucs.p_vec, nucs.p_refl)
    else:
        E_loc, p_loc, vloc = E_ball, nucs.p_vec, np.zeros(n)
    p_red = np.linalg.norm(p_loc, axis=1)
    print(f"local energy v_loc: mean {vloc.mean():.3f} MeV, max {vloc.max():.3f}; scattering nucleon <|p|> = {p_red.mean():.2f} MeV/c, "
          f"corr(|p|, r) = {np.corrcoef(p_red, r)[0, 1]:+.3f}, (E - m) mean = {(E_loc - m).mean():.3f} MeV")
    Ebeam = args.ebeam * 1e3
    k = np.zeros((n, 4)); k[:, 0] = Ebeam; k[:, 3] = np.sqrt(Ebeam**2 - m_e**2)
    P = np.column_stack([E_loc, p_loc])
    kp0, pp0 = scatter(k, P, (m_e, m), rng)
    mis0 = missing(k, kp0, pp0, m)                  # scattering-frame E_miss/p_miss (before the balance)

    # ---- 3. INCL energy balance ------------------------------------------------------
    old_total = Ebeam + E_ball - V_ball             # preInteraction: E_lep + E1 - V1
    beta = (k[:, 1:] + p_loc) / (Ebeam + E_loc)[:, None]
    alpha, kp, pp, V_out, ok, dE = incl_energy_balance(nuc, r, k, kp0, pp0, beta, old_total, local_on)
    print(f"balance: alpha mean {alpha[ok].mean():.5f}, range [{alpha[ok].min():.5f}, {alpha[ok].max():.5f}], "
          f"failures {int((~ok).sum())}, max |dE| = {np.abs(dE[ok]).max():.2e} MeV; "
          f"V(T_p') > 0 for {(V_out > 0).mean() * 100:.1f} % of events")

    # ---- 4. record: E_miss, p_miss ---------------------------------------------------
    mis = missing(k, kp, pp, m)
    Em, pm = mis["Em"], mis["pm"]
    Em_expect = nuc.V0 - T_ball - V_out
    pm_ref = p_red                                   # p_red (on) or p_ball (never)
    fast = V_out == 0
    print(f"E_miss (record): mean {Em.mean():.3f} MeV, range [{Em.min():.3f}, {Em.max():.3f}]; "
          f"fast protons (V = 0): mean {Em[fast].mean():.3f}, range [{Em[fast].min():.3f}, {Em[fast].max():.3f}] "
          f"(V0 = {nuc.V0:.3f}, S = {nuc.S})")
    print(f"  max |E_miss - (V0 - T_ball - V(T_p'))| = {np.abs(Em - Em_expect)[ok].max():.2e} MeV")
    print(f"|p_miss| (record): mean {pm.mean():.2f} MeV/c, corr(|p_miss|, r) = {np.corrcoef(pm, r)[0, 1]:+.3f}; "
          f"ratio to {'p_red' if local_on else 'p_ball'}: mean {(pm / pm_ref)[ok].mean():.4f}, "
          f"fast-proton max |diff| = {np.abs(pm - pm_ref)[ok & fast].max():.2e} MeV/c")
    dp = mis["pm_vec"] - p_loc      # INCL's CM rescaling changes the lab total momentum by gamma*beta*dE*
    print(f"  INCL rescaling shifts the final-state total momentum (the remnant absorbs it): "
          f"|p_miss_vec - {'p_red' if local_on else 'p_ball'}_vec| mean {np.linalg.norm(dp, axis=1).mean():.2f} MeV/c, "
          f"mean z component {dp[:, 2].mean():+.2f} MeV/c, fast-proton max {np.linalg.norm(dp, axis=1)[fast].max():.2f}")
    print(f"scattering frame (before balance): E_miss mean {mis0['Em'].mean():.3f} MeV (= m - E_loc), "
          f"|p_miss| mean {mis0['pm'].mean():.2f} MeV/c")

    # ---- histograms + readouts --------------------------------------------------------
    r_edges = np.linspace(0.0, nuc.r_max, 24)
    p_edges = np.linspace(0.0, 280.0, 29)
    e_edges = np.arange(-60.5, 80.5 + 1e-9, 1.0)
    pm_edges = np.arange(0.0, 400.0 + 1e-9, 5.0)
    H, _, _ = np.histogram2d(r, p_ball, bins=[r_edges, p_edges])
    cE, _ = np.histogram(Em, e_edges); cEx, _ = np.histogram(Em_expect, e_edges); cE0, _ = np.histogram(mis0["Em"], e_edges)
    cP, _ = np.histogram(pm, pm_edges); cPx, _ = np.histogram(pm_ref, pm_edges); cP0, _ = np.histogram(mis0["pm"], pm_edges)

    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = args.outdir / stem_name
    with open(stem.with_suffix(".txt"), "w") as fh:
        fh.write(f"# {stem_name}: {nuc.describe()}\n# E_beam = {args.ebeam} GeV, N = {n}, seed = {args.seed}, "
                 f"local energy = {args.local_energy}, resample = {args.resample}\n")
        fh.write(f"# E_miss overflow: {int(((Em < e_edges[0]) | (Em >= e_edges[-1])).sum())}, "
                 f"|p_miss| overflow: {int((pm >= pm_edges[-1]).sum())}\n")
        hd.describe2d(H, r_edges, p_edges, xname="r [fm]", yname="|p_ball| [MeV/c]", quiet=True, save=fh)
        hd.compare1d(cE, cEx, e_edges, labels=("E_miss record", "V0 - T_ball - V(T_p')"),
                     xname="E_miss [MeV]", table=False, quiet=True, save=fh)
        hd.compare1d(cP, cPx, pm_edges, labels=("|p_miss| record", "p_red" if local_on else "p_ball"),
                     xname="|p_miss| [MeV/c]", table=False, quiet=True, save=fh)
        hd.describe1d(cE0, e_edges, name="E_miss scattering frame (before balance) [MeV]", quiet=True, save=fh)
        hd.describe1d(cP0, pm_edges, name="|p_miss| scattering frame (before balance) [MeV/c]", quiet=True, save=fh)
    np.savez_compressed(stem.with_suffix(".npz"), r_vec=nucs.r_vec, p_ball_vec=nucs.p_vec, p_refl=nucs.p_refl,
                        vloc=vloc, E_loc=E_loc, p_loc=p_loc, k=k, kp0=kp0, pp0=pp0, kp=kp, pp=pp, alpha=alpha,
                        ok=ok, V_out=V_out, Em=Em, pm=pm, pm_vec=mis["pm_vec"], Em_expect=Em_expect,
                        Em0=mis0["Em"], pm0=mis0["pm"], V0=nuc.V0, S=nuc.S, TF=nuc.TF, pF=nuc.pF, m=m,
                        ebeam=args.ebeam, seed=args.seed, local_energy=args.local_energy, resample=args.resample)

    # ---- figure ------------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.2), constrained_layout=True)
    a = ax[0, 0]
    pc = a.pcolormesh(r_edges, p_edges, H.T, cmap="Blues", rasterized=True)
    fig.colorbar(pc, ax=a, label="nucleons")
    rr = np.linspace(0, nuc.r_max, 300)
    a.plot(rr, nuc.pF * nuc.min_p_from_r(rr), "r-", lw=1.4, label=r"strict floor $p_{\min}(r) = p_F\,F(r)^{1/3}$")
    a.axhline(nuc.pF, color="k", ls=":", lw=1, label=rf"$p_F$ = {nuc.pF:.1f} MeV/c")
    a.set_xlabel("r [fm]"); a.set_ylabel(r"$|\vec p_{\rm ball}|$ [MeV/c]")
    a.set_title(f"INCL ground state, r-p coefficient {nuc.rp_coefficient:g}"
                + (" + truncated-ball redraw" if args.resample else "") + f", corr = {np.corrcoef(p_ball, r)[0, 1]:+.2f}", fontsize=10)
    a.legend(loc="lower right", fontsize=8, frameon=True)

    a = ax[0, 1]
    a.plot(rr, nuc.local_energy(rr, np.full_like(rr, 0.5 * nuc.pF)), "C0-", lw=1.6,
           label=r"$v_{\rm loc}(r)$ for $T \leq T_F$  (= $T_F(r)$)")
    a.axhline(nuc.V0, color="C3", ls="--", lw=1.2, label=rf"$V_0 = T_F + S$ = {nuc.V0:.2f} MeV")
    a.axhline(nuc.TF, color="C0", ls=":", lw=1, label=rf"$T_F$ = {nuc.TF:.2f} MeV")
    a.set_xlabel("r [fm]"); a.set_ylabel("[MeV]"); a.set_ylim(0, 62)
    a.set_title("INCL potential and local energy (C12 protons)", fontsize=10)
    a.legend(loc="upper left", fontsize=8, frameon=False)
    ins = a.inset_axes([0.55, 0.12, 0.42, 0.42])
    TT = np.linspace(0, 260, 300)
    ins.plot(TT, nuc.potential_energy(TT), "C3-", lw=1.4)
    ins.set_xlabel("T [MeV]", fontsize=8); ins.set_ylabel("V(T) [MeV]", fontsize=8)
    ins.tick_params(labelsize=7); ins.set_ylim(0, 50); ins.grid(alpha=0.3)

    a = ax[1, 0]
    a.stairs(cE, e_edges, fill=True, color="C0", alpha=0.75, label="record (after INCL balance)")
    a.stairs(cEx, e_edges, color="k", lw=1.2, ls="--", label=r"$V_0 - T_{\rm ball} - V(T_{p'})$")
    a.stairs(cE0, e_edges, color="C2", lw=1.0, label="scattering frame (before balance)")
    a.axvline(nuc.S, color="C3", ls=":", lw=1); a.axvline(nuc.V0, color="C3", ls=":", lw=1)
    a.text(nuc.S, 0.98 * a.get_ylim()[1], " S", color="C3", va="top", fontsize=8)
    a.text(nuc.V0, 0.98 * a.get_ylim()[1], r" $V_0$", color="C3", va="top", fontsize=8)
    a.set_xlabel(r"$E_{\rm miss} = \omega - T_{p'}$  [MeV]"); a.set_ylabel("events / 1 MeV")
    a.legend(loc="upper left", fontsize=8, frameon=False)

    a = ax[1, 1]
    a.stairs(cP, pm_edges, fill=True, color="C1", alpha=0.75, label="record (after INCL balance)")
    a.stairs(cPx, pm_edges, color="k", lw=1.2, ls="--", label=r"$p_{\rm red}$" if local_on else r"$p_{\rm ball}$")
    a.stairs(cP0, pm_edges, color="C2", lw=1.0, label="scattering frame (before balance)")
    a.set_xlabel(r"$|\vec p_{\rm miss}| = |\vec p_{p'} - \vec q|$  [MeV/c]"); a.set_ylabel("events / 5 MeV/c")
    a.legend(loc="upper right", fontsize=8, frameon=False)
    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.suptitle(f"e + p(INCL C12) $\\to$ e' + p', two-body phase space, $E_e$ = {args.ebeam} GeV, N = {n:,}, "
                 f"local energy: {args.local_energy}", fontsize=11)
    fig.savefig(stem.with_suffix(".png"), dpi=140)
    print(f"wrote {stem.with_suffix('.png')}, .txt, .npz")


if __name__ == "__main__":
    main()

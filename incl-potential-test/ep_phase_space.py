#!/usr/bin/env python3
"""
ep_phase_space.py: two-body phase-space e + p -> e' + p' on a FREE proton AT REST,
with the (e,e'p) missing-energy / missing-momentum readout.

Purpose
-------
Baseline for the INCL potential / local-energy tests. With the target proton free
and at rest there is no binding energy and no Fermi motion, so by construction

    q      = k - k'                 (three-momentum transfer)
    omega  = E - E'                 (energy transfer)
    p_miss = p_p' - q               must be 0   (it equals the initial nucleon momentum)
    E_miss = omega - T_p' - T_rec   must be 0   (T_rec = 0: no residual system here)

Anything non-zero in this configuration is a bookkeeping error in the script, not
physics. The next steps swap the free target 4-vector for a bound nucleon (Fermi
momentum, potential V0, local energy) and reuse `scatter()` and `missing()`
unchanged; `missing()` already accepts an optional recoil mass for that.

Sampling
--------
Pure two-body phase space: the final state is isotropic in the e-p CM frame
(uniform in cos theta*, phi*), then boosted to the lab. No matrix element (no
Mott / Rosenbluth weight). Because t = -Q^2 is linear in cos theta*, the Q^2
distribution must come out FLAT on [0, 4 p*^2] -- that is the check that the
sampling itself is right.

Masses are read from the repo's shared/pdg.json (PDG values, same source as the
genie-agent runners); a PDG fallback is used if the file is missing.

Usage (through pixi, from the genie-dev root)
---------------------------------------------
    pixi run python incl-potential-test/ep_phase_space.py -n 200000 --ebeam 2.445

Outputs (next to the script unless --outdir):
    ep_free_proton.png   E_miss, |p_miss|, Q^2 panels
    ep_free_proton.txt   histdiag readouts of the same counts (read this, not the PNG)
    ep_free_proton.npz   event 4-vectors (GeV) + E_miss/p_miss, to rebuild the histograms
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "results" / "template"))
import histdiag as hd  # noqa: E402

# PDG fallbacks (PDG 2024) only if shared/pdg.json is unreachable.
_M_E_PDG = 0.51099895e-3
_M_P_PDG = 0.93827209


def load_masses():
    """(m_e, M_p) in GeV from shared/pdg.json, with PDG fallback."""
    p = ROOT / "shared" / "pdg.json"
    try:
        d = json.loads(p.read_text())
        return d["probes"]["eminus"]["mass_gev"], d["nucleons"]["proton"]["mass_gev"], str(p)
    except (OSError, KeyError, json.JSONDecodeError):
        return _M_E_PDG, _M_P_PDG, "PDG 2024 fallback (shared/pdg.json not readable)"


# ----------------------------------------------------------------------------
# 4-vector helpers. Arrays are (n, 4) with column 0 = energy, 1..3 = px, py, pz.
# ----------------------------------------------------------------------------
def mass2(p):
    return p[:, 0] ** 2 - np.sum(p[:, 1:] ** 2, axis=1)


def boost(p, beta):
    """Boost 4-vectors p (n,4) by velocity beta (n,3). beta = +v of the frame
    the vectors are expressed in, as seen from the target frame (i.e. to go
    CM -> lab pass beta_CM_in_lab)."""
    b2 = np.sum(beta**2, axis=1)
    gamma = 1.0 / np.sqrt(1.0 - b2)
    bp = np.sum(beta * p[:, 1:], axis=1)
    # gamma2 = (gamma-1)/b2, safe when b2 -> 0
    gamma2 = np.where(b2 > 0, (gamma - 1.0) / np.where(b2 > 0, b2, 1.0), 0.0)
    out = np.empty_like(p)
    out[:, 0] = gamma * (p[:, 0] + bp)
    out[:, 1:] = p[:, 1:] + (gamma2 * bp + gamma * p[:, 0])[:, None] * beta
    return out


def scatter(k, P, m_out, rng):
    """Two-body phase-space scattering k + P -> k' + P' with outgoing masses
    m_out = (m1, m2). Isotropic in the CM frame of (k + P), boosted back to the
    frame k and P are given in. Works for any target 4-vector P (at rest or not,
    on- or off-shell), which is what the bound-nucleon steps will feed it."""
    n = k.shape[0]
    m1, m2 = m_out
    tot = k + P
    s = mass2(tot)
    rs = np.sqrt(s)
    # CM momentum from the Kallen function
    lam = (s - (m1 + m2) ** 2) * (s - (m1 - m2) ** 2)
    if np.any(lam < 0):
        raise ValueError("below threshold for the requested outgoing masses")
    pstar = np.sqrt(lam) / (2.0 * rs)
    e1 = (s + m1**2 - m2**2) / (2.0 * rs)
    e2 = (s + m2**2 - m1**2) / (2.0 * rs)
    cost = rng.uniform(-1.0, 1.0, n)
    phi = rng.uniform(0.0, 2.0 * np.pi, n)
    sint = np.sqrt(1.0 - cost**2)
    d = np.stack([sint * np.cos(phi), sint * np.sin(phi), cost], axis=1)
    k1 = np.empty((n, 4)); k1[:, 0] = e1; k1[:, 1:] = pstar[:, None] * d
    k2 = np.empty((n, 4)); k2[:, 0] = e2; k2[:, 1:] = -pstar[:, None] * d
    beta = tot[:, 1:] / tot[:, [0]]
    return boost(k1, beta), boost(k2, beta)


def missing(k, kp, pp, m_p, m_recoil=None):
    """(e,e'p) missing quantities. p_miss = p_p' - q (initial-nucleon convention).
    E_miss = omega - T_p' - T_rec; T_rec = 0 unless a recoil mass is given, in which
    case the residual system carries -p_miss."""
    q = k[:, 1:] - kp[:, 1:]
    omega = k[:, 0] - kp[:, 0]
    pm_vec = pp[:, 1:] - q
    pm = np.linalg.norm(pm_vec, axis=1)
    T_p = pp[:, 0] - m_p
    T_rec = 0.0 if m_recoil is None else np.sqrt(m_recoil**2 + pm**2) - m_recoil
    Em = omega - T_p - T_rec
    Q2 = np.sum(q**2, axis=1) - omega**2
    return dict(Em=Em, pm=pm, pm_vec=pm_vec, omega=omega, q=q, Q2=Q2, T_p=T_p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-n", "--nevents", type=int, default=200_000)
    ap.add_argument("--ebeam", type=float, default=2.445, help="electron beam energy [GeV]")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--outdir", type=Path, default=HERE)
    ap.add_argument("--stem", default="ep_free_proton")
    args = ap.parse_args(argv)

    m_e, m_p, msrc = load_masses()
    rng = np.random.default_rng(args.seed)
    n = args.nevents

    # beam along +z on a proton at rest
    k = np.zeros((n, 4)); k[:, 0] = args.ebeam; k[:, 3] = np.sqrt(args.ebeam**2 - m_e**2)
    P = np.zeros((n, 4)); P[:, 0] = m_p

    kp, pp = scatter(k, P, (m_e, m_p), rng)
    mis = missing(k, kp, pp, m_p)  # free proton: no residual system

    # ---- bookkeeping checks (all should be at float precision) ----
    dcons = (k + P) - (kp + pp)
    print(f"masses from: {msrc}")
    print(f"m_e = {m_e:.9f} GeV, M_p = {m_p:.9f} GeV, E_beam = {args.ebeam} GeV, N = {n}, seed = {args.seed}")
    print(f"max |4-momentum non-conservation| per component [GeV]: {np.abs(dcons).max(axis=0)}")
    print(f"max |m(e')^2 - m_e^2| = {np.abs(mass2(kp) - m_e**2).max():.3e} GeV^2, "
          f"max |m(p')^2 - M_p^2| = {np.abs(mass2(pp) - m_p**2).max():.3e} GeV^2")
    s = mass2(k + P)[0]
    pstar = np.sqrt((s - (m_e + m_p) ** 2) * (s - (m_e - m_p) ** 2)) / (2 * np.sqrt(s))
    q2max = 4 * pstar**2
    print(f"sqrt(s) = {np.sqrt(s):.4f} GeV, p* = {pstar:.4f} GeV, Q^2_max = 4p*^2 = {q2max:.4f} GeV^2 "
          f"(sampled max {mis['Q2'].max():.4f})")
    Em_MeV, pm_MeV = mis["Em"] * 1e3, mis["pm"] * 1e3
    print(f"E_miss : max|.| = {np.abs(Em_MeV).max():.3e} MeV   mean = {Em_MeV.mean():.3e} MeV")
    print(f"|p_miss|: max   = {pm_MeV.max():.3e} MeV/c  mean = {pm_MeV.mean():.3e} MeV/c")

    # ---- histograms: axes chosen so the later bound-nucleon results fit on them ----
    e_edges = np.arange(-20.5, 80.5 + 1e-9, 1.0)        # MeV, 1 MeV bins, a bin centred on 0
    p_edges = np.arange(0.0, 400.0 + 1e-9, 5.0)         # MeV/c
    q_edges = np.linspace(0.0, 1.05 * q2max, 43)        # GeV^2, flat expected up to 4p*^2
    cE, _ = np.histogram(Em_MeV, e_edges)
    cP, _ = np.histogram(pm_MeV, p_edges)
    cQ, _ = np.histogram(mis["Q2"], q_edges)

    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = args.outdir / args.stem
    with open(stem.with_suffix(".txt"), "w") as fh:
        fh.write(f"# {args.stem}: e + p(at rest) -> e' + p', two-body phase space, "
                 f"E_beam = {args.ebeam} GeV, N = {n}, seed = {args.seed}\n")
        fh.write(f"# max|E_miss| = {np.abs(Em_MeV).max():.3e} MeV, max|p_miss| = {pm_MeV.max():.3e} MeV/c, "
                 f"overflow E: {int((Em_MeV < e_edges[0]).sum() + (Em_MeV >= e_edges[-1]).sum())}, "
                 f"overflow p: {int((pm_MeV >= p_edges[-1]).sum())}\n")
        hd.describe1d(cE, e_edges, name="E_miss [MeV]", table=False, quiet=True, save=fh)
        hd.describe1d(cP, p_edges, name="|p_miss| [MeV/c]", table=False, quiet=True, save=fh)
        hd.describe1d(cQ, q_edges, name="Q^2 [GeV^2]", table=False, quiet=True, save=fh)
    np.savez_compressed(stem.with_suffix(".npz"), k=k, kp=kp, P=P, pp=pp,
                        Em=mis["Em"], pm=mis["pm"], pm_vec=mis["pm_vec"], Q2=mis["Q2"],
                        ebeam=args.ebeam, seed=args.seed, m_e=m_e, m_p=m_p)

    # ---- figure ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.8), constrained_layout=True)
    ax[0].stairs(cE, e_edges, fill=True, color="C0", alpha=0.8)
    ax[0].set_xlabel(r"$E_{\rm miss} = \omega - T_{p'}$  [MeV]")
    ax[0].set_ylabel("events / 1 MeV")
    ax[0].text(0.97, 0.95, f"max$|E_{{\\rm miss}}|$ = {np.abs(Em_MeV).max():.1e} MeV",
               ha="right", va="top", transform=ax[0].transAxes, fontsize=9)
    ax[1].stairs(cP, p_edges, fill=True, color="C1", alpha=0.8)
    ax[1].set_xlabel(r"$|\vec p_{\rm miss}| = |\vec p_{p'} - \vec q|$  [MeV/c]")
    ax[1].set_ylabel("events / 5 MeV/c")
    ax[1].text(0.97, 0.95, f"max$|p_{{\\rm miss}}|$ = {pm_MeV.max():.1e} MeV/c",
               ha="right", va="top", transform=ax[1].transAxes, fontsize=9)
    ax[2].stairs(cQ, q_edges, fill=True, color="C2", alpha=0.8)
    ax[2].axvline(q2max, color="k", ls="--", lw=1, label=r"$4p^{*2}$")
    ax[2].set_xlabel(r"$Q^2$  [GeV$^2$]  (flat: isotropic CM)")
    ax[2].set_ylabel("events / bin")
    ax[2].set_ylim(0, 1.3 * cQ.max())
    ax[2].legend(loc="upper right", frameon=False)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle(f"e + p(at rest) $\\to$ e' + p', two-body phase space, "
                 f"$E_e$ = {args.ebeam} GeV, N = {n:,}", fontsize=11)
    fig.savefig(stem.with_suffix(".png"), dpi=150)
    print(f"wrote {stem.with_suffix('.png')}, .txt, .npz")


if __name__ == "__main__":
    main()

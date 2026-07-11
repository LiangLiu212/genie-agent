"""de Forest sigma_cc1 off-shell e-p cross section, Mott cross section, Bosted
form factors and the H(e,e'p) elastic cross section -- a vectorized numpy port
of simc_gfortran/physics_proton.f @ 60c2047 (the same prescription E91-013
used to extract its spectral functions: sigma_cc1, deForest_flag = 0).

Ported symbols and their sources:
    sig_mott       <- sigMott          physics_proton.f:178-193
    fofa_best_fit  <- fofa_best_fit    physics_proton.f:137-172  (Bosted PRC 51, 409 Eqs 4-5)
    sigep          <- sigep            physics_proton.f:1-21     (H elastic, microbarn/sr)
    deforest       <- deForest flag 0/-1  physics_proton.f:25-135
Constants Mp / hbarc / alpha follow SIMC constants.inc:19,41,44 (proton mass
taken from the pdg package instead: 938.27209 vs SIMC's 938.27231 MeV, a
2e-7 relative difference).

Units are SIMC's: energies/momenta in MeV, Q2 in MeV^2, angles in rad.
    sig_mott, sigep : microbarn / sr
    deforest        : microbarn * MeV^2 / sr^2   ( = K * sigma_cc1 = d6sigma / S(Em,pm),
                      K = E_p * p_p -- the Jacobian dE_p dOmega_p -> d3pm, so
                      d6sigma = sigma_cc1 * S * dE_e' dOmega_e d3pm )

Flag semantics (physics_proton.f:36-41):
    flag =  0  sigma_cc1, off-shell   (Ebar = sqrt(pm^2 + Mp^2), qbar^2 = (Ep-Ebar)^2 - q^2)
    flag = -1  sigma_cc1, ON-SHELL    (Ebar = Ep - nu,           qbar^2 = -Q2)
    flag = +1  sigma_cc2 -- not ported (E91-013 used cc1); raises NotImplementedError.

The de Forest metric caveat (report/simc-eep-normalization.md section 8) lives in
the cc2 branch only; the cc1 structure functions below are verbatim from the
Fortran.
"""
import numpy as np

from selection import M_P as _M_P_GEV   # proton mass from the pdg package [GeV]

MP = _M_P_GEV * 1000.0                  # [MeV]
MP2 = MP ** 2
HBARC = 197.327053                      # [MeV fm]   (SIMC constants.inc:41)
ALPHA = 1.0 / 137.0359895               # (SIMC constants.inc:44)


def fofa_best_fit(Q2):
    """Bosted world-data fit for G_Ep, G_Mp (PRC 51, 409 Eqs 4-5).
    Q2 > 0 in MeV^2 (SIMC passes -Q2/hbarc^2 in fm^-2 and converts back;
    the net input is just spacelike Q2). Returns (GE, GM)."""
    Q2g = np.asarray(Q2, dtype=float) * 1e-6            # [GeV^2]
    Q = np.sqrt(np.maximum(Q2g, 0.0))
    Q3, Q4, Q5 = Q ** 3, Q ** 4, Q ** 5
    GE = 1.0 / (1.0 + 0.62 * Q + 0.68 * Q2g + 2.8 * Q3 + 0.83 * Q4)
    GM = 2.793 / (1.0 + 0.35 * Q + 2.44 * Q2g + 0.5 * Q3 + 1.04 * Q4 + 0.34 * Q5)
    return GE, GM


def sig_mott(e0, theta, Q2):
    """Mott cross section for a point nucleus [microbarn/sr]
    (physics_proton.f:178-193). e0 [MeV], theta [rad], Q2 [MeV^2].
    N.B. in this Q2-form both SIMC callers (sigep, deForest) pass the
    SCATTERED electron energy as e0 — with Q2 = 4*Ein*Ee*sin^2(theta/2)
    that reproduces the standard Mott built from the beam energy."""
    sig = (2.0 * ALPHA * HBARC * e0 * np.cos(theta / 2.0) / Q2) ** 2   # [fm^2/sr]
    return sig * 1.0e4                                                  # -> microbarn/sr


def sigep(Ein, Ee, theta_e, Q2):
    """H(e,e'p) elastic cross section [microbarn/sr] (physics_proton.f:1-21).
    Ein/Ee = incident/scattered electron energy [MeV], theta_e [rad], Q2 [MeV^2]."""
    GE, GM = fofa_best_fit(Q2)
    tau = Q2 / (4.0 * MP2)
    W1p = GM ** 2 * tau
    W2p = (GE ** 2 + GM ** 2 * tau) / (1.0 + tau)
    Wp = W2p + 2.0 * W1p * np.tan(theta_e / 2.0) ** 2
    return sig_mott(Ee, theta_e, Q2) * (Ee / Ein) * Wp    # sigMott(vertex%e%E,...) = E'


def angles_pq(uq, up):
    """sin(gamma) and cos(phi) of the proton about q (physics_proton.f:74-89).
    uq, up: unit-vector arrays of shape (N, 3), lab frame with the beam along z.
    gamma = angle(q, p); phi = azimuth of p about q from the scattering plane."""
    uq = np.asarray(uq, dtype=float)
    up = np.asarray(up, dtype=float)
    cdot = np.einsum("ij,ij->i", uq, up)
    sin_gamma = np.sqrt(np.maximum(1.0 - cdot ** 2, 0.0))
    num = (uq[:, 1] * (uq[:, 1] * up[:, 2] - uq[:, 2] * up[:, 1])
           - uq[:, 0] * (uq[:, 2] * up[:, 0] - uq[:, 0] * up[:, 2]))
    den = sin_gamma * np.sqrt(np.maximum(1.0 - uq[:, 2] ** 2, 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        cos_phi = np.where(den > 0, num / den, 0.0)
    return sin_gamma, np.clip(cos_phi, -1.0, 1.0)


def deforest(Ee, theta_e, Q2, nu, qmag, Ep, pp, pm, sin_gamma, cos_phi, flag=0):
    """K * sigma_cc1 = d6sigma / S(Em,pm)  [microbarn * MeV^2 / sr^2]
    (physics_proton.f:25-135, deForest_flag = 0 or -1).

    Ee, theta_e : scattered electron energy [MeV], angle [rad]
    Q2, nu, qmag: 4-momentum transfer^2 [MeV^2], energy transfer [MeV], |q| [MeV]
    Ep, pp      : outgoing-proton energy, momentum [MeV]
    pm          : missing momentum |p_m| [MeV]
    sin_gamma, cos_phi : proton orientation about q (angles_pq)
    """
    if flag not in (0, -1):
        raise NotImplementedError("only sigma_cc1 (flag 0 / -1) is ported; "
                                  "E91-013 used cc1")
    q4sq = -np.asarray(Q2, dtype=float)          # spacelike, regular metric
    q2 = np.asarray(qmag, dtype=float) ** 2      # |q|^2

    if flag == 0:                                # off-shell Ebar, qbar (f:66-69)
        ebar = np.sqrt(pm ** 2 + MP2)
        qbsq = (Ep - ebar) ** 2 - q2
    else:                                        # on-shell replacement (f:70-72)
        ebar = Ep - nu
        qbsq = q4sq

    GE, GM = fofa_best_fit(Q2)
    tau_s = q4sq / (4.0 * MP2)                   # signed (negative) tau (f:91-92)
    f1 = (GE - GM * tau_s) / (1.0 - tau_s)
    kf2 = (GM - GE) / (1.0 - tau_s)

    t2 = np.tan(theta_e / 2.0) ** 2
    termC = (q4sq / q2) ** 2                     # (f:98-101)
    termT = t2 - q4sq / (2.0 * q2)
    termS = t2 - (q4sq / q2) * cos_phi ** 2
    termI = (-q4sq / q2) * np.sqrt(t2 - q4sq / q2) * cos_phi

    sumFF1 = (f1 + kf2) ** 2                     # cc1 structure funcs (f:103-110)
    sumFF2 = f1 ** 2 - qbsq * kf2 ** 2 / (4.0 * MP2)
    WC = (ebar + Ep) ** 2 * sumFF2 - q2 * sumFF1
    WT = -2.0 * qbsq * sumFF1
    WS = 4.0 * pp ** 2 * sin_gamma ** 2 * sumFF2
    WI = -4.0 * (ebar + Ep) * pp * sin_gamma * sumFF2

    allsum = (termC * WC + termT * WT + termS * WS + termI * WI) / 4.0   # (f:127-128)
    return sig_mott(Ee, theta_e, Q2) * pp * allsum / ebar                # (f:129)


def _elastic_kinematics(Ein, theta_e):
    """Free e-p elastic point: returns (Ee, Q2, nu, qmag, Ep, pp) at pm = 0."""
    s2 = np.sin(theta_e / 2.0) ** 2
    Ee = Ein / (1.0 + 2.0 * Ein * s2 / MP)
    Q2 = 4.0 * Ein * Ee * s2
    nu = Ein - Ee
    qmag = np.sqrt(Q2 + nu ** 2)
    Ep = MP + nu
    pp = qmag
    return Ee, Q2, nu, qmag, Ep, pp


def _selftest():
    """Validation (plan step 1): flag 0 == flag -1 at pm = 0, and the elastic
    closure sigep = deforest * Ee / (pp * Mp * Ein).

    The closure identity: PWIA d6sigma = K*sigma_cc1*S with S = delta(Em)delta3(pm)
    for a free proton; integrating with dE_p dOmega_p = d3pm/K gives
    dsigma/dOmega_e = sigma_cc1 / |dEm/dEe'| and |dEm/dEe'| = Mp*Ein/(Ee*Ep)
    at the elastic point, so sigep = deforest/(Ep*pp) * Ee*Ep/(Mp*Ein)."""
    Eins = np.array([845.0, 2445.0, 2445.0, 3245.0, 3245.0])
    thetas = np.radians(np.array([78.5, 20.5, 32.0, 28.6, 50.0]))   # Dutta Table I settings
    Ee, Q2, nu, qmag, Ep, pp = _elastic_kinematics(Eins, thetas)
    zeros = np.zeros_like(Ee)

    d0 = deforest(Ee, thetas, Q2, nu, qmag, Ep, pp, zeros, zeros, zeros, flag=0)
    dm1 = deforest(Ee, thetas, Q2, nu, qmag, Ep, pp, zeros, zeros, zeros, flag=-1)
    ok1 = np.allclose(d0, dm1, rtol=1e-12)
    print(f"flag 0 == flag -1 at pm=0:  max rel diff {np.max(np.abs(d0/dm1 - 1)):.2e}"
          f"  {'PASS' if ok1 else 'FAIL'}")

    ratio = deforest(Ee, thetas, Q2, nu, qmag, Ep, pp, zeros, zeros, zeros) \
        * Ee / (pp * MP * Eins) / sigep(Eins, Ee, thetas, Q2)
    ok2 = np.allclose(ratio, 1.0, rtol=1e-10)
    print("elastic closure  deforest*Ee/(pp*Mp*Ein) / sigep:")
    for E, th, r, s in zip(Eins, np.degrees(thetas), ratio,
                           sigep(Eins, Ee, thetas, Q2)):
        print(f"   Ein={E:7.1f} MeV  theta={th:5.1f} deg   ratio={r:.12f}"
              f"   sigep={s:.4e} ub/sr")
    print(f"  {'PASS' if ok2 else 'FAIL'}")

    # Mott sanity: rearranged elastic form alpha^2 cos^2 / (4 Ein^2 sin^4) * (hbarc)^2
    th, E = np.radians(32.0), 2445.0
    q2el = 4 * E * _elastic_kinematics(np.array([E]), np.array([th]))[0][0] \
        * np.sin(th / 2) ** 2
    direct = (ALPHA * HBARC * np.cos(th / 2)) ** 2 \
        / (4 * E ** 2 * np.sin(th / 2) ** 4) * 1e4 * (4 * E ** 2 * np.sin(th / 2) ** 2 / q2el) ** 2
    ok3 = np.isclose(direct, sig_mott(E, th, q2el), rtol=1e-12)
    print(f"Mott rearrangement at 2445 MeV, 32 deg: {sig_mott(E, th, q2el):.6e} ub/sr"
          f"  {'PASS' if ok3 else 'FAIL'}")
    return ok1 and ok2 and ok3


if __name__ == "__main__":
    import sys
    sys.exit(0 if _selftest() else 1)

"""Flat companion MC for the S^D extraction: the phase-space volume H(Em, pm)
(plan: .claude/plans/genie-experimental-spectral-function.md, step 3).

H(bin) = integral of dE_e' dOmega_e dE_p dOmega_p over the analysis fiducial,
restricted to throws whose reconstructed (Em, pm) land in the bin -- the GENIE
analogue of SIMC/Dutta's per-bin experimental phase space H(Em,pm)
(longpaper2.tex:843-875; cf. genvol in report/simc-eep-normalization.md).
Units: MeV^2 sr^2. With events weighted by 1/(K sigma_cc1) [1/(ub MeV^2/sr^2)]
and sigma_tot/N_gen [ub], S^D = weighted-sum / H comes out in MeV^-4.

Sampling is exact importance sampling with per-throw volume weights (each
variable uniform over a -- possibly throw-dependent -- local range, weight =
product of local ranges; H(bin) = sum of weights landing in the bin / N_flat):

variant (a) `q2win`  (matches cache/sd/<model>_q2win.npz + El window):
    El  ~ U[EL_LO, EL_HI]                (event coverage: in-grid events span
                                          [0.256, 2.166] GeV -- zero loss)
    Q2  ~ U[1.216, 1.344] GeV^2          (thrown directly; dcos(theta_e) =
                                          dQ2 / (2 E_beam El) -- exact Jacobian,
                                          100 % fiducial efficiency)
    T_p ~ U[max(nu-130, 0), nu+25] MeV   (tracks nu so Em lands in the grid)
    cos(gamma_pq) ~ U[cg_min, 1]         (cone about q with pm <= PM_MAX_H)
    phi_e, phi_pq: integrated (x 2pi each; Em, pm and the fiducial do not
                   depend on them)

variant (b) `accept` (matches cache/sd/<model>_accept.npz):
    El  ~ U over the HMS momentum bite, cos(theta_e) ~ U over the in-plane
    band (the exact delta_e/yptar_e box after the e'-plane rotation),
    E_p ~ U over the SOS bite, proton direction thrown as slopes (yptar,
    xptar) uniform over the SOS box about the arm axis with the solid-angle
    Jacobian dOmega = dyp dxp / (1 + yp^2 + xp^2)^(3/2); phi_e integrated
    (x 2pi). The electron out-of-plane window is fully accepting, exactly as
    in acceptance.py. The t05 generation cut Q2 >= 1.18 GeV^2 is imposed on
    BOTH variants -- the event samples carry it, so H must too.

Outputs cache/sd/H_q2win.npz / H_accept.npz: H [MeV^2 sr^2], sumw2 (MC
variance), nflat (raw counts -- mask bins with nflat below ~50 at use time),
em_edges/pm_edges, N_flat, and the fiducial bounds (single source of truth
for the step-4 event masks).

    pixi run python results/prd-analyzer/phase_space_h.py            # both variants
"""
import sys
import os

sys.path.insert(0, "results/prd-analyzer")
import numpy as np

import samples as S
import acceptance as acc
from selection import M_P as _M_P_GEV

MP = _M_P_GEV * 1000.0                    # [MeV]
MREC = acc.M_REC * 1000.0                 # 11B recoil [MeV]
EB = 2445.0                               # beam [MeV]

EM_EDGES = np.arange(-20.0, 125.0, 5.0)   # 28 bins, matches the data's 5-MeV grid
PM_EDGES = np.arange(0.0, 425.0, 25.0)    # 16 bins
PM_MAX_H = 420.0                          # cone bound: > pm grid edge (400)

# variant (a) fiducial bounds (also the step-4 event mask; zero observed loss)
EL_LO, EL_HI = 250.0, 2200.0              # [MeV]
Q2_LO, Q2_HI = 1.28e6 * 0.95, 1.28e6 * 1.05   # [MeV^2]
Q2_GEN = 1.18e6                           # t05 generation cut [MeV^2]

# variant (b) bounds from acceptance.py (MeV)
B_EL_LO, B_EL_HI = acc.P0_E * 1e3 * (1 - acc.DELTA_E_HW / 100), \
                   acc.P0_E * 1e3 * (1 + acc.DELTA_E_HW / 100)
B_CT_LO, B_CT_HI = np.cos(acc.TH0_E + np.arctan(acc.YPTAR_E_HW)), \
                   np.cos(acc.TH0_E - np.arctan(acc.YPTAR_E_HW))
_pp_lo, _pp_hi = acc.P0_P * 1e3 * (1 - acc.DELTA_P_HW / 100), \
                 acc.P0_P * 1e3 * (1 + acc.DELTA_P_HW / 100)
B_EP_LO, B_EP_HI = np.hypot(_pp_lo, MP), np.hypot(_pp_hi, MP)
TWO_PI = 2.0 * np.pi


def _throw_q2win(n, rng):
    """Variant (a): returns (Em, pm, weight) -- weight [MeV^2 sr^2] per throw."""
    El = rng.uniform(EL_LO, EL_HI, n)
    Q2 = rng.uniform(Q2_LO, Q2_HI, n)
    ct = 1.0 - Q2 / (2.0 * EB * El)               # cos(theta_e), |ct| <= 1 for El >= 275
    nu = EB - El
    qmag = np.sqrt(Q2 + nu ** 2)

    tp_lo = np.maximum(nu - 130.0, 0.0)
    tp_hi = nu + 25.0
    wTp = tp_hi - tp_lo
    Tp = tp_lo + rng.uniform(0.0, 1.0, n) * wTp
    Ep = Tp + MP
    pp = np.sqrt(np.maximum(Ep ** 2 - MP ** 2, 0.0))

    with np.errstate(divide="ignore", invalid="ignore"):
        cg_min = np.clip((qmag ** 2 + pp ** 2 - PM_MAX_H ** 2)
                         / (2.0 * qmag * pp), -1.0, 1.0)
    wcg = np.where(pp > 0, 1.0 - cg_min, 0.0)
    cg = 1.0 - rng.uniform(0.0, 1.0, n) * wcg

    pm = np.sqrt(np.maximum(qmag ** 2 + pp ** 2 - 2.0 * qmag * pp * cg, 0.0))
    Em = nu - Tp - pm ** 2 / (2.0 * MREC)

    w = ((EL_HI - EL_LO) * ((Q2_HI - Q2_LO) / (2.0 * EB * El)) * TWO_PI
         * wTp * wcg * TWO_PI)
    w = np.where(np.abs(ct) <= 1.0, w, 0.0)       # guard (inactive for EL_LO=250)
    return Em, pm, w


def _throw_accept(n, rng):
    """Variant (b): returns (Em, pm, weight) over the HMS x SOS boxes."""
    El = rng.uniform(B_EL_LO, B_EL_HI, n)         # electron: momentum bite x theta band
    ct = rng.uniform(B_CT_LO, B_CT_HI, n)
    st = np.sqrt(1.0 - ct ** 2)
    nu = EB - El
    qx, qz = -El * st, EB - El * ct               # phi_e = 0 frame

    Ep = rng.uniform(B_EP_LO, B_EP_HI, n)         # proton: SOS bite x slope box
    pp = np.sqrt(Ep ** 2 - MP ** 2)
    yp = rng.uniform(-acc.YPTAR_P_HW, acc.YPTAR_P_HW, n)
    xp = rng.uniform(-acc.XPTAR_P_HW, acc.XPTAR_P_HW, n)
    norm2 = 1.0 + yp ** 2 + xp ** 2
    sp, cp = np.sin(acc.TH0_P), np.cos(acc.TH0_P)
    # p = pp * (z_arm + yp*y_arm + xp*x_arm)/sqrt(norm2); arm axes as acceptance.py
    px = pp * (-sp - yp * cp) / np.sqrt(norm2)
    py = pp * xp / np.sqrt(norm2)
    pz = pp * (cp - yp * sp) / np.sqrt(norm2)

    pm = np.sqrt((px - qx) ** 2 + py ** 2 + (pz - qz) ** 2)
    Em = nu - (Ep - MP) - pm ** 2 / (2.0 * MREC)

    Q2 = 2.0 * EB * El * (1.0 - ct)
    w = ((B_EL_HI - B_EL_LO) * (B_CT_HI - B_CT_LO) * TWO_PI
         * (B_EP_HI - B_EP_LO)
         * (2 * acc.YPTAR_P_HW) * (2 * acc.XPTAR_P_HW) / norm2 ** 1.5)
    w = np.where(Q2 >= Q2_GEN, w, 0.0)            # t05 generation cut, as in the samples
    return Em, pm, w


def build_h(variant, n_flat, seed=20260702, chunk=2_000_000):
    throw = {"q2win": _throw_q2win, "accept": _throw_accept}[variant]
    rng = np.random.default_rng(seed)
    nb_e, nb_p = len(EM_EDGES) - 1, len(PM_EDGES) - 1
    Hsum = np.zeros((nb_e, nb_p))
    Wsq = np.zeros((nb_e, nb_p))
    cnt = np.zeros((nb_e, nb_p), dtype=np.int64)
    done = 0
    while done < n_flat:
        n = min(chunk, n_flat - done)
        Em, pm, w = throw(n, rng)
        ok = w > 0
        Hsum += np.histogram2d(Em[ok], pm[ok], bins=(EM_EDGES, PM_EDGES),
                               weights=w[ok])[0]
        Wsq += np.histogram2d(Em[ok], pm[ok], bins=(EM_EDGES, PM_EDGES),
                              weights=w[ok] ** 2)[0]
        cnt += np.histogram2d(Em[ok], pm[ok],
                              bins=(EM_EDGES, PM_EDGES))[0].astype(np.int64)
        done += n
    H = Hsum / n_flat                              # [MeV^2 sr^2] per bin
    Herr = np.sqrt(Wsq) / n_flat                   # ~MC error (weights ~uniform per bin)
    return dict(H=H, Herr=Herr, nflat=cnt, N_flat=np.array([n_flat]),
                em_edges=EM_EDGES, pm_edges=PM_EDGES,
                el_bounds=np.array([EL_LO, EL_HI]),
                q2_bounds=np.array([Q2_LO, Q2_HI, Q2_GEN]))


if __name__ == "__main__":
    n_flat = int(float(os.environ.get("N_FLAT", "2e8")))
    out_dir = f"{S.CACHE_DIR}/sd"
    os.makedirs(out_dir, exist_ok=True)
    for variant in ("q2win", "accept"):
        full = build_h(variant, n_flat)
        half = build_h(variant, n_flat // 2, seed=987654321)
        used = full["nflat"] >= 50
        rel = np.abs(half["H"][used] / full["H"][used] - 1.0)
        path = f"{out_dir}/H_{variant}.npz"
        np.savez_compressed(path, **full)
        print(f"[{variant}] N_flat={n_flat:.1e}  bins used (n>=50): {used.sum()}/{used.size}  "
              f"H range [{full['H'][used].min():.3e}, {full['H'][used].max():.3e}] MeV^2 sr^2")
        print(f"[{variant}] split-sample check: median |dH/H| = {np.median(rel):.4f}, "
              f"p99 = {np.percentile(rel, 99):.4f}  ->  {path}")

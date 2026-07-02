"""HMS/SOS spectrometer-acceptance selection for the Dutta Fig. 9 overlay.

Implements the fiducial recipe of report/simc-eep-normalization.md (Sections
4.5/4.7): per-arm boxes in SPECTROMETER coordinates (delta, yptar, xptar)
about the E91-013 Q^2 = 1.28 GeV^2 central settings, applied to GENIE gst
events -- replacing the simple (El, theta_e, Tp, theta_p) windows of
selection.py with the physical detector acceptance.

Central settings (Dutta Table I row 5; SOS P0 = central |q| of the electron
kinematics, see the report):
    HMS (e'):  P0 = 1.725 GeV/c at 32.0 deg
    SOS (p):   P0 = 1.341 GeV/c at 43.5 deg, opposite side of the beam
Half-widths (collimator-derived, report Section 4.5):
    HMS: |delta| < 8 %   (clean region; full bite ~ +-10 %), |yptar| < 27.5 mrad
    SOS: |delta| < 20 %  (40 % bite), |yptar| < 57.0 mrad, |xptar| < 37.2 mrad
The octagonal collimator corners are not modeled (rectangular box, ~10 %
larger solid angle than the true octagon).

Azimuth handling: gevgen events are azimuthally symmetric about the beam, so
each event is rotated about z to put e' in the spectrometer (horizontal)
plane. The electron out-of-plane slope is then 0 by construction -- the HMS
xptar window (+-70 mrad, the most generous of all windows) is treated as
fully accepting for the electron. The proton receives the same rotation, so
its out-of-plane slope RELATIVE to the e' plane is preserved and the SOS box
carves the physical coincidence acceptance.

Missing kinematics follow the paper's definitions (selection.py instead uses
the heavy-recoil approximation T_rec = 0):
    E_m = omega - T_p - T_rec,   T_rec = p_m^2 / (2 M_{A-1})
"""
import numpy as np
import uproot
import awkward as ak

from selection import M_P, _PDG, BRANCHES   # masses from the pdg package

# --- central settings + half-widths (report/simc-eep-normalization.md 4.5) ---
P0_E, TH0_E = 1.725, np.radians(32.0)   # HMS  [GeV/c], [rad]
P0_P, TH0_P = 1.341, np.radians(43.5)   # SOS  [GeV/c], [rad]
DELTA_E_HW = 8.0       # [%]   HMS clean momentum region
YPTAR_E_HW = 27.5e-3   # [rad] HMS in-plane (collimator h/z)
DELTA_P_HW = 20.0      # [%]   SOS full 40 % bite
YPTAR_P_HW = 57.0e-3   # [rad] SOS in-plane
XPTAR_P_HW = 37.2e-3   # [rad] SOS out-of-plane (collimator v/z)

# 11B recoil mass [GeV]: AME2020 atomic mass 11.0093054 u minus 5 electron
# masses (CODATA u = 931.49410242 MeV; m_e from the pdg package).
_U_MEV = 931.49410242
_M_E = _PDG.get_particle_by_mcid(11).mass          # electron mass [GeV]
M_REC = 11.0093054 * _U_MEV / 1000.0 - 5 * _M_E    # = 10.2526 GeV

KEYS = ["E_miss", "p_miss", "Q2", "delta_e", "yptar_e",
        "delta_p", "yptar_p", "xptar_p", "El", "theta_e", "Tp", "theta_p"]


def load_events(path):
    """Read one gst (local path or root:// URL) and build the per-event
    spectrometer-frame quantities. Angles in rad (slopes), energies GeV,
    E_miss/p_miss in MeV (MeV/c)."""
    a = uproot.open(path)["gst"].arrays(BRANCHES, library="ak")

    isp = (a.pdgf == 2212)
    has_p = ak.to_numpy(ak.any(isp, axis=1))
    lead = ak.argmax(ak.where(isp, a.pf, -1.0), axis=1, keepdims=True)
    g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
    Ep, pxp, pyp, pzp, pp = g(a.Ef), g(a.pxf), g(a.pyf), g(a.pzf), g(a.pf)

    nz = lambda b: ak.to_numpy(a[b])
    Ev, El = nz("Ev"), nz("El")
    pxv, pyv, pzv = nz("pxv"), nz("pyv"), nz("pzv")
    pxl, pyl, pzl = nz("pxl"), nz("pyl"), nz("pzl")
    cthl = nz("cthl")

    # --- electron arm (HMS): rotate e' into the spectrometer plane (phi_e -> 0)
    pTl = np.hypot(pxl, pyl)
    pl = np.hypot(pTl, pzl)
    delta_e = (pl / P0_E - 1.0) * 100.0
    se, ce = np.sin(TH0_E), np.cos(TH0_E)
    # in-plane slope about the HMS axis = tan(theta_e - theta0_e)
    yptar_e = (pTl * ce - pzl * se) / (pTl * se + pzl * ce)

    # --- proton arm (SOS, opposite side): same rotation about the beam
    phi_e = np.arctan2(pyl, pxl)
    cph, sph = np.cos(phi_e), np.sin(phi_e)
    pxp_r = pxp * cph + pyp * sph            # proton rotated by -phi_e
    pyp_r = -pxp * sph + pyp * cph
    sp, cp = np.sin(TH0_P), np.cos(TH0_P)
    pz_arm = -pxp_r * sp + pzp * cp          # along the SOS axis (phi = pi side)
    py_arm = -pxp_r * cp - pzp * sp          # in-plane transverse
    px_arm = pyp_r                           # out-of-plane
    with np.errstate(divide="ignore", invalid="ignore"):
        yptar_p = np.where(pz_arm > 0, py_arm / pz_arm, np.nan)
        xptar_p = np.where(pz_arm > 0, px_arm / pz_arm, np.nan)
    delta_p = (pp / P0_P - 1.0) * 100.0

    # --- missing kinematics (paper definitions; T_rec included)
    omega = Ev - El
    Tp = Ep - M_P
    qx, qy, qz = pxv - pxl, pyv - pyl, pzv - pzl
    p_miss = np.sqrt((pxp - qx) ** 2 + (pyp - qy) ** 2 + (pzp - qz) ** 2)  # GeV
    T_rec = p_miss ** 2 / (2.0 * M_REC)
    E_miss = (omega - Tp - T_rec) * 1000.0

    theta_e = np.degrees(np.arccos(np.clip(cthl, -1.0, 1.0)))
    theta_p = np.degrees(np.arccos(np.clip(np.where(pp > 0, pzp / pp, 1.0), -1.0, 1.0)))

    return dict(E_miss=E_miss, p_miss=p_miss * 1000.0, Q2=nz("Q2"),
                delta_e=delta_e, yptar_e=yptar_e,
                delta_p=delta_p, yptar_p=yptar_p, xptar_p=xptar_p,
                El=El, theta_e=theta_e, Tp=Tp, theta_p=theta_p,
                has_p=has_p, qel=ak.to_numpy(a.qel).astype(bool))


def _in(x, hw):
    return np.abs(np.nan_to_num(x, nan=1e9)) <= hw


def select_acceptance(ev):
    """Full HMS x SOS coincidence acceptance (arm-frame boxes)."""
    return (ev["has_p"].astype(bool)
            & _in(ev["delta_e"], DELTA_E_HW) & _in(ev["yptar_e"], YPTAR_E_HW)
            & _in(ev["delta_p"], DELTA_P_HW) & _in(ev["yptar_p"], YPTAR_P_HW)
            & _in(ev["xptar_p"], XPTAR_P_HW))


def cut_summary(ev, label=""):
    """N-1 cut flow for the acceptance selection."""
    masks = {
        "has_p":   ev["has_p"].astype(bool),
        "delta_e": _in(ev["delta_e"], DELTA_E_HW),
        "yptar_e": _in(ev["yptar_e"], YPTAR_E_HW),
        "delta_p": _in(ev["delta_p"], DELTA_P_HW),
        "yptar_p": _in(ev["yptar_p"], YPTAR_P_HW),
        "xptar_p": _in(ev["xptar_p"], XPTAR_P_HW),
    }
    n = len(ev["El"])
    allm = np.ones(n, bool)
    for m in masks.values():
        allm &= m
    print(f"[{label}] total events: {n}")
    for name, m in masks.items():
        nm1 = np.ones(n, bool)
        for k, mm in masks.items():
            if k != name:
                nm1 &= mm
        print(f"   {name:8s} alone {int(m.sum()):8d}   N-1 (all but {name:8s}) {int(nm1.sum()):8d}")
    print(f"   ALL CUTS {int(allm.sum()):8d}")
    return allm

"""Selection + missing-kinematics utilities for the (e,e'p) PRD analysis.

Replicates the Q² = 1.28 GeV² spectrometer setting of Dutta et al. (JLab Hall C E91-013,
nucl-ex/0303011, Table I row 5): narrow HMS/SOS acceptance windows on the scattered electron
(El, θ_e) and the leading proton (T_p, θ_p), plus the missing-energy / missing-momentum
reconstruction
    ω      = E_v − E_l
    E_miss = ω − T_p                 (heavy-recoil approx, T_{A-1} ≈ 0)
    p_miss = | q⃗ − p⃗_p |,   q⃗ = p⃗_beam − p⃗_e'
Reconstructed (post-FSI) leading proton = highest-momentum final-state proton.

This is the shared selection util imported by the plotting scripts. Reads GENIE gst trees
(uproot + awkward). Branch meanings: El/pxl.. = scattered e'; pf/Ef/pdgf = post-FSI hadrons;
Q2 = experimental-like; qel/res/dis = mode flags.
"""
import numpy as np
import uproot
import awkward as ak

M_P = 0.938272  # proton mass [GeV]

# Spectrometer acceptance windows: name -> (center, half-width). Q² = 1.28 setting (Table I row 5).
CUTS = {
    "El":      (1.725, 0.005),   # scattered e' energy [GeV]   (paper E_e' = 1.725)
    "theta_e": (32.0,  0.5),     # e' angle [deg]              (paper θ_e' = 32°)
    "Tp":      (0.700, 0.025),   # leading-proton KE [GeV]     (paper T_p = 700 MeV)
    "theta_p": (43.0,  1.0),     # proton angle [deg]          (paper θ_p = 43.5° conjugate)
}

BRANCHES = ["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl", "cthl",
            "Q2", "qel", "res", "dis",
            "pdgf", "Ef", "pxf", "pyf", "pzf", "pf"]


def load_events(path):
    """Read one gst, build per-event scalars (leading proton, missing E/p). Returns a dict
    of numpy arrays (E_miss, p_miss in MeV / MeV/c; angles in deg; energies in GeV)."""
    a = uproot.open(path)["gst"].arrays(BRANCHES, library="ak")

    isp = (a.pdgf == 2212)
    has_p = ak.to_numpy(ak.any(isp, axis=1))
    lead = ak.argmax(ak.where(isp, a.pf, -1.0), axis=1, keepdims=True)   # leading-proton index
    g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
    Ep, pxp, pyp, pzp, pp = g(a.Ef), g(a.pxf), g(a.pyf), g(a.pzf), g(a.pf)

    nz = lambda b: ak.to_numpy(a[b])
    Ev, El = nz("Ev"), nz("El")
    pxv, pyv, pzv = nz("pxv"), nz("pyv"), nz("pzv")
    pxl, pyl, pzl = nz("pxl"), nz("pyl"), nz("pzl")
    cthl = nz("cthl")

    omega = Ev - El
    Tp = Ep - M_P
    theta_e = np.degrees(np.arccos(np.clip(cthl, -1.0, 1.0)))
    theta_p = np.degrees(np.arccos(np.clip(np.where(pp > 0, pzp / pp, 1.0), -1.0, 1.0)))
    qx, qy, qz = pxv - pxl, pyv - pyl, pzv - pzl                 # 3-momentum transfer q
    p_miss = np.sqrt((pxp - qx)**2 + (pyp - qy)**2 + (pzp - qz)**2)
    E_miss = omega - Tp

    return dict(Ev=Ev, El=El, theta_e=theta_e, has_p=has_p, Tp=Tp, theta_p=theta_p,
                Q2=nz("Q2"), E_miss=E_miss * 1000.0, p_miss=p_miss * 1000.0,
                qel=ak.to_numpy(a.qel).astype(bool))


def _win(x, c, hw):
    return np.abs(np.nan_to_num(x, nan=1e9) - c) <= hw


def select_electron(ev):
    """Stage 1: scattered-electron arm only (El ∧ θ_e) — fixes Q²."""
    return _win(ev["El"], *CUTS["El"]) & _win(ev["theta_e"], *CUTS["theta_e"])


def select(ev):
    """Stage 2: full (e,e'p) coincidence — has_p ∧ El ∧ θ_e ∧ T_p ∧ θ_p."""
    return (ev["has_p"] & select_electron(ev)
            & _win(ev["Tp"], *CUTS["Tp"]) & _win(ev["theta_p"], *CUTS["theta_p"]))


def cut_summary(ev, label=""):
    """Print the N-1 cut flow and return the all-cuts mask."""
    masks = {
        "has_p":   ev["has_p"].astype(bool),
        "El":      _win(ev["El"], *CUTS["El"]),
        "theta_e": _win(ev["theta_e"], *CUTS["theta_e"]),
        "Tp":      _win(ev["Tp"], *CUTS["Tp"]),
        "theta_p": _win(ev["theta_p"], *CUTS["theta_p"]),
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

#!/usr/bin/env python3
"""
ep_incl_scan.py: how the E_miss and |p_miss| distributions of ep_incl_scatter.py move when
T_F and S_p are changed (local energy on + the fork's resampling, as ep_incl_C12_lfon_resample.png).

Top row:    T_F scan through p_F (T_F = sqrt(p_F^2 + m^2) - m). INCL's S = 6.83 stays, so the
            well depth V0 = T_F + S, the Fermi ball, the floor p_min(r) = p_F F(r)^(1/3) and the
            local energy all move with it. S_p fixed at the mass-table value 15.957.
Bottom row: S_p scan (the real separation energy paid at the surface exit, dQ = -S_p + S).
            Only the exit changes: E_miss(free) shifts rigidly, |p_free| by |dQ|/beta.
            T_F fixed at INCL's 38.17 (p_F = 270.34).

Each panel: free-proton curves solid, record (proton still inside the well) dashed and
thin, nominal INCL values in black. Same seed for every variant (common random numbers),
so the differences are the parameters, not statistics. The closed forms
    E_miss(free) = T_F + S_p - T_ball  in [S_p, T_F + S_p]
    E_miss(rec)  = V0 - T_ball - V(T_p')  with V0 = T_F + S
say what to expect. Outputs ep_incl_C12_lfon_resample_scan.png / .txt.
"""
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "results" / "template"))
import histdiag as hd
from ep_phase_space import load_masses
from ep_incl_scatter import run_chain
from incl_nucleus import INCLNucleus

N, EBEAM, SEED = 200_000, 2.445, 1
m_e = load_masses()[0] * 1e3
nom = INCLNucleus()
TF_NOM, SP_NOM = nom.TF, nom.S - nom.emission_qvalue_correction()
TF_VALUES = [30.0, TF_NOM, 46.0]           # MeV
SP_VALUES = [10.0, SP_NOM, 22.0]           # MeV
m = nom.m

def pF_of_TF(TF):
    return np.sqrt(TF * (TF + 2 * m))

e_edges = np.arange(-60.5, 80.5 + 1e-9, 1.0)
pm_edges = np.arange(0.0, 400.0 + 1e-9, 5.0)

def run(nuc):
    R = run_chain(nuc, N, EBEAM, SEED, local_on=True, resample=True, m_e=m_e, verbose=False)
    ex = R["exits"]
    return dict(Em=R["Em"], pm=R["pm"], Emf=R["Em_free"][ex], pmf=R["pm_free"][ex], exits=ex.mean(),
                TF=nuc.TF, pF=nuc.pF, V0=nuc.V0, Sp=R["S_real"], Tball=R["T_ball"].mean(),
                pred=R["p_red"].mean())

rows = []
scan_TF = [(f"$T_F$ = {TF:.2f} MeV ($p_F$ = {pF_of_TF(TF):.1f})", run(INCLNucleus(pF=pF_of_TF(TF))), TF == TF_NOM)
           for TF in TF_VALUES]
scan_SP = [(f"$S_p$ = {SP:.2f} MeV", run(INCLNucleus(S_p_real=SP)), SP == SP_NOM) for SP in SP_VALUES]

with open(HERE / "ep_incl_C12_lfon_resample_scan.txt", "w") as fh:
    fh.write(f"# scan of T_F (through p_F) and S_p; local energy on + resample; N = {N}, E_beam = {EBEAM} GeV, seed = {SEED}\n")
    for tag, scan in (("T_F", scan_TF), ("S_p", scan_SP)):
        nomR = [x for x in scan if x[2]][0][1]
        for lab, Rv, is_nom in scan:
            line = (f"{tag} scan | {lab.replace('$', '')}: p_F = {Rv['pF']:.2f}, T_F = {Rv['TF']:.2f}, V0 = {Rv['V0']:.2f}, "
                    f"S_p = {Rv['Sp']:.3f} | <T_ball> = {Rv['Tball']:.2f}, <p_red> = {Rv['pred']:.2f} | exits {Rv['exits'] * 100:.2f} % | "
                    f"E_miss free: mean {Rv['Emf'].mean():.2f}, range [{Rv['Emf'].min():.2f}, {Rv['Emf'].max():.2f}] | "
                    f"E_miss record: mean {Rv['Em'].mean():.2f} | <|p_miss|> free {Rv['pmf'].mean():.2f}, record {Rv['pm'].mean():.2f}")
            print(line); fh.write("# " + line + "\n")
            if not is_nom:
                c1, _ = np.histogram(Rv["Emf"], e_edges); c2, _ = np.histogram(nomR["Emf"], e_edges)
                hd.compare1d(c1, c2, e_edges, labels=(lab.replace('$', ''), "nominal"), xname="E_miss free [MeV]",
                             table=False, quiet=True, save=fh)
                c1, _ = np.histogram(Rv["pmf"], pm_edges); c2, _ = np.histogram(nomR["pmf"], pm_edges)
                hd.compare1d(c1, c2, pm_edges, labels=(lab.replace('$', ''), "nominal"), xname="|p_miss| free [MeV/c]",
                             table=False, quiet=True, save=fh)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(2, 2, figsize=(12, 8.4), constrained_layout=True)
colors = ["C0", "k", "C3"]
for row, (scan, title) in enumerate(((scan_TF, rf"$T_F$ scan (through $p_F$; $V_0 = T_F + S$, $S$ = {nom.S}), $S_p$ = {SP_NOM:.2f} MeV"),
                                     (scan_SP, rf"$S_p$ scan (surface exit only), $T_F$ = {TF_NOM:.2f} MeV"))):
    for (lab, Rv, is_nom), c in zip(scan, colors):
        cEf, _ = np.histogram(Rv["Emf"], e_edges); cE, _ = np.histogram(Rv["Em"], e_edges)
        cPf, _ = np.histogram(Rv["pmf"], pm_edges); cP, _ = np.histogram(Rv["pm"], pm_edges)
        ax[row, 0].stairs(cEf, e_edges, color=c, lw=1.8 if is_nom else 1.4, label=lab + " (free proton)")
        ax[row, 0].stairs(cE, e_edges, color=c, lw=0.9, ls="--", alpha=0.8, label=lab + " (record, inside)" if is_nom else None)
        ax[row, 1].stairs(cPf, pm_edges, color=c, lw=1.8 if is_nom else 1.4, label=lab + " (free proton)")
        ax[row, 1].stairs(cP, pm_edges, color=c, lw=0.9, ls="--", alpha=0.8, label=lab + " (record, inside)" if is_nom else None)
        for xv in (Rv["Sp"], Rv["TF"] + Rv["Sp"]):
            ax[row, 0].axvline(xv, color=c, ls=":", lw=0.7, alpha=0.7)
    ax[row, 0].set_title(title, fontsize=10)
    ax[row, 0].set_xlabel(r"$E_{\rm miss} = \omega - T_{p'}$  [MeV]"); ax[row, 0].set_ylabel("events / 1 MeV")
    ax[row, 0].set_xlim(-45, 80); ax[row, 0].legend(fontsize=7.5, frameon=False, loc="upper left")
    ax[row, 1].set_title("dotted lines on the left: $S_p$ and $T_F + S_p$ of each variant", fontsize=9)
    ax[row, 1].set_xlabel(r"$|\vec p_{\rm miss}| = |\vec p_{p'} - \vec q|$  [MeV/c]"); ax[row, 1].set_ylabel("events / 5 MeV/c")
    ax[row, 1].legend(fontsize=7.5, frameon=False, loc="upper right")
for a in ax.flat:
    a.grid(alpha=0.3)
fig.suptitle(f"e + p(INCL C12) $\\to$ e' + p', two-body phase space, $E_e$ = {EBEAM} GeV, N = {N:,} per curve, "
             "local energy on + truncated-ball redraw", fontsize=11)
fig.savefig(HERE / "ep_incl_C12_lfon_resample_scan.png", dpi=140)
print("wrote", HERE / "ep_incl_C12_lfon_resample_scan.png", "+ .txt")

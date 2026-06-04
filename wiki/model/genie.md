---
title: GENIE (and the MINERvA tune)
type: model
tags: [model, generator, genie, neutrino, minerva-tune]
updated: 2026-06-02
sources: [2503.15047, 2301.02272]
channels: [ccqe]
---

# GENIE

The neutrino event generator used as the central model in the MINERvA
A-dependence analysis ([[ccqe]]), in the form of **GENIE v2.12.6 modified to the
"MINERvA tune v1.0.1"** (2503.15047).

## MINERvA tune ingredients (2503.15047)

- **Nuclear model:** relativistic Fermi gas + Bodek–Ritchie high-momentum (SRC)
  tail; Fermi momentum k_F = 0.221 GeV/c. Density: Gaussian below Ca,
  2-parameter Woods–Saxon for heavier nuclei (2503.15047).
- **QE:** Llewellyn-Smith; vector form factors BBBA05; axial dipole with
  **M_A = 0.99 GeV/c²** (2503.15047).
- **2p2h** ([[mec-2p2h]]): IFIC Valencia model, q₃ < 1.2 GeV/c, empirically
  enhanced in (energy, q₃) regions by fits to MINERvA LE data (2503.15047).
- **RPA:** Valencia-model RPA; carbon screening reused for heavier nuclei as an
  approximation (2503.15047).
- **Resonance:** Rein–Sehgal, M_A^RES = 1.12 GeV/c²; non-resonant pion production
  reduced (bubble-chamber reanalysis + MINERvA) (2503.15047).
- **DIS:** leading order with Bodek–Yang low-Q² modification; AGKY hadronization
  (2503.15047).
- **FSI** ([[fsi]]): INTRANUKE-**hA**; an elastic-hA FSI bug was fixed by
  reweighting those events to no-FSI for C, O, Fe, Pb (2503.15047).

## MnvGENIEv1 (the muon-kinematics analysis, 2301.02272)

The companion muon-kinematics measurement (2301.02272) uses GENIE **2.12.6**
with the **MnvGENIEv1** tune — default GENIE adjusted to previous MINERvA data,
with three modifications (2301.02272):

1. **RPA:** Valencia random-phase-approximation ("weak nuclear screening")
   correction vs neutrino energy and three-momentum transfer (2301.02272).
2. **2p2h** ([[mec-2p2h]]): Valencia multinucleon model, empirically fit to
   previous MINERvA CH data — the modification **increases the integrated 2p2h
   rate by 49%**, applied as the same fractional increase per proton–neutron
   pair for all nuclei (2301.02272).
3. **Non-resonant pion production reduced by 57%** to match a fit to deuterium
   measurements (2301.02272).

QE is Llewellyn-Smith with a Bodek-Ritchie high-momentum Fermi-gas tail (BRRFG);
M_A is (not stated) in this paper's text (2301.02272). This is the same MnvGENIE
lineage as the "MINERvA tune v1.0.1" used in 2503.15047, but the two papers quote
their tunes with different levels of detail.

## In the generator comparisons

- **TKI analysis (2503.15047):** comparison versions run untuned (`_00_000`, via
  NUISANCE): GENIE v3 **G18_01a, G18_01b, G18_10a, G18_10b** (2503.15047). The
  **hN** variants approach [[neut]] in high-[[fsi]] regions, while the **hA**
  variants tend to **under-predict** the data there (as does [[nuwro]]);
  [[gibuu]] is most consistent (2503.15047).
- **Muon-kinematics analysis (2301.02272):** the data **prefer GENIE's hA FSI
  model over hN** (2301.02272). Both papers thus favor hA over hN, though the
  framing and observables differ (see [[fsi]]).

The hN/hA contrast directly reflects the cascade choice above.
Source: [[source/2503.15047]], [[source/2301.02272]].

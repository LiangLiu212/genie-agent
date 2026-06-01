---
title: GENIE (and the MINERvA tune)
type: model
tags: [model, generator, genie, neutrino, minerva-tune]
updated: 2026-06-01
sources: [2503.15047]
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

## In the generator comparison (2503.15047)

Comparison versions (run untuned, `_00_000`, via NUISANCE): GENIE v3
**G18_01a, G18_01b, G18_10a, G18_10b** (2503.15047). The **hN** GENIE variants
approach [[neut]] in the high-[[fsi]] regions, while the **hA** variants tend to
**under-predict** the data there (as does [[nuwro]]); [[gibuu]] is most
consistent (2503.15047). The hN/hA contrast directly reflects the cascade choice
above. Source: [[source/2503.15047]].

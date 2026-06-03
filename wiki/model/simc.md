---
title: SIMC (Hall C (e,e'p) Monte Carlo)
type: model
tags: [model, monte-carlo, electron-scattering, jlab, pwia]
updated: 2026-06-01
sources: [nucl-ex/0303011]
---

# SIMC

The JLab Hall C adaptation of the (e,e'p) simulation code originally written for
SLAC experiment NE18 (nucl-ex/0303011). Used to model spectrometer acceptance,
phase space, and radiative corrections in the [[em-qe]] analysis.

## Ingredients (nucl-ex/0303011)

- COSY-generated transport matrices model the HMS and SOS at [[jlab-hall-c]];
  includes energy loss and multiple scattering in intervening material
  (nucl-ex/0303011).
- Surviving events weighted by PWIA cross section, radiative corrections, and
  Coulomb corrections (nucl-ex/0303011).
- Off-shell e-p cross section: deForest σ_cc1 prescription (nucl-ex/0303011).
- [[spectral-function]] input: Independent Particle Shell Model (IPSM), with
  per-shell momentum distributions from a Woods-Saxon potential (code DWEEPY);
  Perey factor β = 0.85 for Fe and Au (nucl-ex/0303011).
- Radiative corrections: Mo and Tsai formulation adapted for coincidence (e,e'p)
  per Ent et al. (Phys. Rev. C 64, 054610) (nucl-ex/0303011).
- Form factors: G_E dipole G_E = (1 + Q²/0.71)⁻²; G_M from Gari-Krümpelmann
  (≈ μ_p G_E), with μ_p G_E/G_M = 1 in the "traditional" PWIA (nucl-ex/0303011).

## Role in the analysis (nucl-ex/0303011)

SIMC supplies the per-bin phase space H(E_m,p_m) and the radiative-correction
ratio C^rad used to deradiate the experimental [[spectral-function]], and its
acceptance model is validated against elastic e-p data (nucl-ex/0303011). One
limitation noted: the SIMC zero-missing-energy peak is consistently narrower than
observed (energy resolution not fully modeled), flagged by the authors as not of
primary importance (nucl-ex/0303011). Source: [[source/nucl-ex_0303011]].

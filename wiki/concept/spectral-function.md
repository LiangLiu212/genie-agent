---
title: Spectral function
type: concept
tags: [concept, nuclear-structure, spectral-function, electron-scattering]
updated: 2026-06-01
sources: [nucl-ex/0303011]
targets: [c12, fe56, au197]
channels: [em-qe]
---

# Spectral function

The joint probability distribution S(E_m, p_m) of finding a nucleon in the
nucleus with missing energy E_m and missing momentum p_m
([[missing-energy-momentum]]). It is the nuclear-structure input to the PWIA
(e,e'p) ([[em-qe]]) cross section and, more broadly, an input to neutrino-nucleus
event generators.

## Extraction in (e,e'p) (nucl-ex/0303011)

The "experimental" (radiation-corrected, "deradiated") spectral function is
(nucl-ex/0303011):

```
S^derad(E_m, p_m) = (1 / [L · H(E_m,p_m)]) · Σ_counts [1 / (σ_ep E_e′ p_p′)] · C^rad(E_m,p_m)
```

with L the luminosity, H the per-bin phase space, σ_ep the off-shell e-p cross
section, and C^rad the radiative-correction factor (nucl-ex/0303011). The
correction is iterative and model-based (not D'Agostini/SVD): SIMC populates
(p_m, E_m) bins with radiative corrections on/off, the ratio C^rad deradiates the
data, and the deradiated experimental spectral function replaces the model and
iterates to convergence (nucl-ex/0303011). The corrected spectral functions still
include final-state-interaction distortions, including absorption (nucl-ex/0303011).

The model input is the Independent Particle Shell Model (IPSM), with per-shell
momentum distributions from solving the Schrödinger equation in a Woods-Saxon
potential (code DWEEPY); a Perey factor β = 0.85 is applied for Fe and Au
(nucl-ex/0303011). Separated spectral functions combine longitudinal and
transverse pieces (nucl-ex/0303011):

```
S(E_m, p_m) = [σ_L S_L + σ_T S_T] / (σ_L + σ_T)
```

See [[simc]] for the simulation and [[longitudinal-transverse-separation]] for
the L/T decomposition.

## Measurements (nucl-ex/0303011)

JLab Hall C E91-013 on [[c12]], [[fe56]], [[au197]] over Q² = 0.64–3.25 (GeV/c)²
([[source/nucl-ex_0303011]]). Spectral functions measured for |p_m| < 300 MeV/c
and E_m up to 80 MeV (nucl-ex/0303011). Headline: "The measured spectral
functions differ in detail but not in overall shape from most of the theoretical
models" (nucl-ex/0303011). Carbon shell windows: p-shell 10 < E_m < 25 MeV,
s-shell 30 < E_m < 50 MeV; Fe and Au integrated over 0 < E_m < 80 MeV
(nucl-ex/0303011).

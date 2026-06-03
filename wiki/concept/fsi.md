---
title: Final-state interactions (FSI)
type: concept
tags: [concept, fsi, nuclear-effects, intranuke]
updated: 2026-06-01
sources: [2503.15047, nucl-ex/0303011]
channels: [ccqe, em-qe]
targets: [c12, ch, o16, fe56, pb, au197]
---

# Final-state interactions (FSI)

Re-interactions of the struck nucleon (and other hadrons) with the residual
nucleus on its way out. FSI redistribute and absorb hadronic strength, distort
kinematics, and grow with nuclear mass A — a leading source of model uncertainty
in both neutrino ([[ccqe]]) and electron ([[em-qe]]) scattering.

## Probes of FSI in this wiki

- **Nuclear transparency** ([[nuclear-transparency]]) in (e,e'p): the ratio of
  measured to PWIA-predicted knockout yield directly measures the escape
  probability. Falls with A (C > Fe > Au) (nucl-ex/0303011).
- **Transverse kinematic imbalance** ([[transverse-kinematic-imbalance]]) in
  ν_μ CCQE-like: FSI broaden the δP_T distribution and shift it to higher values
  as A increases; the effect is strongest on [[pb]] (2503.15047).

## A-dependence (2503.15047)

MINERvA's simultaneous five-target measurement shows nuclear effects increase
with A: cross-section ratios to [[ch]] per neutron are consistent with unity for
[[c12]] and [[o16]] (water) but deviate clearly for [[fe56]] and [[pb]]; simple
neutron-number scaling works for small nuclei while FSI produce more complex
behavior for large nuclei (2503.15047). Generators differ most in high-FSI
regions: [[neut]] over-predicts, hN [[genie]] approaches NEUT, hA GENIE and
[[nuwro]] under-predict, and [[gibuu]] is most consistent (2503.15047).

## Modeling (2503.15047)

MINERvA's central model uses GENIE's **INTRANUKE-hA** intranuclear cascade; an
elastic-hA FSI bug was fixed by reweighting those events to no-FSI for C, O, Fe,
Pb (2503.15047). See [[genie]]. Comparison generators implement FSI differently
(hA vs hN cascades, GiBUU transport), which is the origin of the spread above.

Source: [[source/2503.15047]], [[source/nucl-ex_0303011]].

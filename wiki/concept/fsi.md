---
title: Final-state interactions (FSI)
type: concept
tags: [concept, fsi, nuclear-effects, intranuke]
updated: 2026-06-02
sources: [2503.15047, 2301.02272, nucl-ex/0303011]
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
- **A-dependence of muon-kinematics cross-section ratios** in ν_μ CCQE-like: the
  per-nucleon ratio of a heavy target to [[ch]] vs transverse muon momentum P_T
  carries a characteristic FSI shape that grows with A; for [[pb]] the ratio is
  always above unity and the shape evolves slowly with longitudinal momentum P_∥
  (2301.02272).

## A-dependence (2503.15047, 2301.02272)

Both MINERvA simultaneous five-target measurements show nuclear effects increase
with A: cross-section ratios to [[ch]] per nucleon are consistent with unity for
[[c12]] and [[o16]] (water) but deviate clearly for [[fe56]] and [[pb]]; simple
nucleon-number scaling works for small nuclei while FSI produce more complex
behavior for large nuclei (2503.15047, 2301.02272). The muon-kinematics analysis
finds Fe/CH ≈ 1.4–1.5 (vs ≈ 1.2 predicted) and a Pb/CH ratio always above unity
whose **P_T shape no generator reproduces**, and reports evidence that the
A-scaling is **not constant over the momentum transferred to the nucleus**
(2301.02272).

### Generator FSI preferences — two framings

- In the **TKI** analysis (2503.15047): generators differ most in high-FSI
  regions: [[neut]] over-predicts, hN [[genie]] approaches NEUT, hA GENIE and
  [[nuwro]] under-predict, [[gibuu]] is most consistent (2503.15047).
- In the **muon-kinematics** analysis (2301.02272): the data **prefer GENIE's hA
  FSI model over hN**, prefer the [[spectral-function]] over LFG within
  [[nuwro]], and the [[gibuu]] comparison may indicate cascade-type models better
  characterize pion intranuclear absorption in heavy nuclei (2301.02272).

> [!note] Consistent, different observables
> The two MINERvA papers agree that hN sits worse than hA (in 2503.15047 hN
> over-predicts toward NEUT; in 2301.02272 the data explicitly prefer hA over
> hN) and both favor GiBUU-style transport for heavy nuclei. They are **not in
> contradiction**, but the comparisons use different observables (TKI δP_T vs
> muon P_∥/P_T), different signal definitions (leading-proton vs muon-only,
> [[ccqe]]), and a different central tune ([[genie]] G18 untuned vs MnvGENIEv1),
> so the agreement is qualitative rather than bin-for-bin.

## Modeling (2503.15047, 2301.02272)

MINERvA's central model uses GENIE's **INTRANUKE-hA** intranuclear cascade; in
the TKI analysis an elastic-hA FSI bug was fixed by reweighting those events to
no-FSI for C, O, Fe, Pb (2503.15047). See [[genie]]. Comparison generators
implement FSI differently (hA vs hN cascades, GiBUU transport), which is the
origin of the spread above. The muon-kinematics analysis (2301.02272) uses the
GENIE 2.12.6 MnvGENIEv1 tune (also hA) as its central model.

Source: [[source/2503.15047]], [[source/2301.02272]],
[[source/nucl-ex_0303011]].

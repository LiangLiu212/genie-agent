---
title: Transverse kinematic imbalance (TKI)
type: concept
tags: [concept, kinematics, tki, fsi, neutrino-scattering]
updated: 2026-06-01
sources: [2503.15047]
channels: [ccqe]
targets: [c12, ch, o16, fe56, pb]
---

# Transverse kinematic imbalance (TKI)

A set of variables built from the muon and proton momenta projected onto the
plane transverse to the incoming neutrino. Because the neutrino energy is
unknown event-by-event, transverse imbalance isolates nuclear effects — Fermi
motion, [[fsi]], and [[mec-2p2h]] — that would vanish for a free, stationary
nucleon ([[ccqe]]) (2503.15047).

## Variables (2503.15047)

Measured by [[minerva]] (each as an absolute cross section per target and a ratio
to [[ch]]) (2503.15047):

- **δP_T** — magnitude of the transverse momentum imbalance of the μ–p system;
  the primary FSI-sensitive observable.
- **δP_{Tx}, δP_{Ty}** — its two transverse components.
- **δα_T** — boost angle; sensitive to whether FSI decelerates or accelerates
  the proton.
- **φ_T** — acoplanarity angle.
- **δP_L** — longitudinal-momentum imbalance,
  δP_L = ½R − (m_{A'}² + δP_T²)/(2R) with R ≡ m_A + p^μ_L + p^p_L − E^μ − E^p
  (2503.15047).
- **P_n** — inferred initial-nucleon momentum, P_n = √(δP_T² + δP_L²)
  (2503.15047).

m_A and m_{A'} are the initial and residual nucleus masses; p_L, E the
longitudinal momenta and energies of the muon and proton (2503.15047).

## Key finding (2503.15047)

The δP_T distribution **shifts toward higher values for higher-A targets**
(Fe, Pb), consistent with stronger [[fsi]]; the [[genie]] MINERvA tune captures
this except for [[pb]], where the observed shift exceeds the prediction
(2503.15047). The high-δP_T tail is where generator disagreement is largest
([[neut]], [[nuwro]], [[gibuu]]). Source: [[source/2503.15047]].

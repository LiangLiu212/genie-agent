---
title: GiBUU
type: model
tags: [model, generator, gibuu, transport, neutrino]
updated: 2026-06-02
sources: [2503.15047, 2301.02272]
channels: [ccqe]
---

# GiBUU

Transport-theory-based neutrino event generator. Compared against the MINERvA
A-dependence data ([[ccqe]]) as **GiBUU release 2019 patch 8** (configurations
T0 and T1), run via NUISANCE (2503.15047).

## In the comparisons

- **TKI analysis (2503.15047):** GiBUU is the **most consistent** generator
  across targets and [[transverse-kinematic-imbalance]] variables, including the
  high-[[fsi]] regions where [[neut]] over-predicts and hA [[genie]] / [[nuwro]]
  under-predict (2503.15047).
- **Muon-kinematics analysis (2301.02272):** the GiBUU comparison **may indicate
  that cascade-type models better characterize pion intranuclear absorption in
  heavy nuclei** (2301.02272) — relevant because the CCQE-like signal includes
  pion-production events where the pion is absorbed.

Its coupled transport treatment of [[fsi]] is the likely reason it tracks the
A-dependence better than the cascade-based generators (2503.15047).
Source: [[source/2503.15047]], [[source/2301.02272]].

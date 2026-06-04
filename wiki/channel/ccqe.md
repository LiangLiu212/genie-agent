---
title: Charged-current quasi-elastic (CCQE / CCQE-like)
type: channel
tags: [channel, neutrino-scattering, ccqe, quasi-elastic]
updated: 2026-06-02
sources: [2503.15047, 2301.02272]
targets: [c12, ch, o16, fe56, pb]
---

# Charged-current quasi-elastic (CCQE / CCQE-like)

Charged-current neutrino single-nucleon knockout: ν_μ + n → μ⁻ + p. The
neutrino analogue of electromagnetic [[em-qe]] (e,e'p) knockout; the dominant
signal channel for accelerator oscillation experiments and a probe of nuclear
structure and final-state interactions ([[fsi]]).

## CCQE-like signal definition (2503.15047)

Experiments cannot tag the underlying reaction, so they define a **CCQE-like**
(or "0π") final state by what is observed. At [[minerva]] the truth-level signal
is a ν_μ CC interaction on [[c12]]/[[ch]]/[[o16]]/[[fe56]]/[[pb]] with
(2503.15047):

- a muon with angle < 17° and 2 GeV/c < p_μ < 20 GeV/c;
- a (leading) proton with angle < 70° and 500 MeV/c < p_p < 1100 MeV/c;
- no mesons, no baryons heavier than neutrons, and no photons above 10 MeV
  (sub-10 MeV photons from nuclear de-excitation are allowed).

Crucially, **[[mec-2p2h]] and Δ-resonance-then-pion-absorption** processes that
yield a proton and no pion are part of the CCQE-like signal — so CCQE-like is
broader than true QE (2503.15047).

### Muon-only variant (2301.02272)

The companion muon-kinematics analysis (2301.02272) uses a **looser, muon-only**
CCQE-like definition on the same five targets: a final state with a muon at
angle ≤ 17° and **2–20 GeV/c**, **any number of nucleons (no proton
requirement)**, **no mesons**, and no photons above 10 MeV (nuclear-excitation
photons allowed) (2301.02272). Same QE + 2p2h + pion-absorption physics content,
but dropping the leading-proton requirement of 2503.15047 (proton 0.5–1.1 GeV/c,
< 70°) opens the acceptance — the two MINERvA measurements are therefore
**complementary, not directly comparable bin-for-bin**.

## Reconstruction (2503.15047)

A negative muon matched into MINOS; ≥1 range-based proton with a Bragg-peak hit
pattern (and a pion-Bragg veto); no Michel electrons near the vertex/track ends
(rejects π⁺); and ≤1 isolated energy cluster (reduces π⁰) (2503.15047).
Purities ≈ 47–60%; efficiency 5–8% (passive nuclei), 28% (tracker) (2503.15047).

## Measurements in this wiki

- MINERvA A-dependence on five targets vs [[transverse-kinematic-imbalance]] and
  muon/proton kinematics, ⟨E_ν⟩ ∼ 6 GeV (2503.15047); see [[source/2503.15047]].
  Nuclear effects grow with A: ratios to CH per neutron ≈ 1 for C and water but
  deviate for Fe and Pb ([[fsi]]).
- MINERvA A-dependence on the same five targets vs **longitudinal/transverse
  muon momentum** (P_∥, P_T), peak E_ν ≈ 6.5 GeV (2301.02272); see
  [[source/2301.02272]]. Pb/CH per-nucleon ratio always > 1 with a
  characteristic P_T shape; Fe/CH ≈ 1.4–1.5 vs ≈ 1.2 predicted; C and water
  ratios near unity. Overall level and P_T shape for Fe/Pb not reproduced by
  current generators ([[fsi]]).

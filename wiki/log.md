# Wiki log

Append-only timeline of wiki operations. Each entry begins with
`## [YYYY-MM-DD] <op> | <title>` so it stays greppable:
`grep "^## \[" log.md | tail`.

## [2026-06-01] init | wiki scaffolded
- Created schema (`CLAUDE.md`), `index.md`, `log.md`, and category dirs
  (source, experiment, target, channel, concept, model, comparison).
- Ingest pipeline: `paper-extractor` subagent fills `papers/<id>/`, then the
  wiki ingest step synthesizes across papers. No sources ingested yet.

## [2026-06-01] ingest | A Study of the Quasi-elastic (e,e'p) Reaction on ¹²C, ⁵⁶Fe and ¹⁹⁷Au (nucl-ex/0303011)
- First source ingested: Dutta et al., JLab Hall C E91-013; (e,e'p) on C/Fe/Au,
  Q² = 0.64–3.25 (GeV/c)². Created thin node `source/nucl-ex_0303011`.
- New pages: `experiment/jlab-hall-c`; `target/c12`, `target/fe56`,
  `target/au197`; `channel/em-qe`; `concept/nuclear-transparency`,
  `concept/spectral-function`, `concept/missing-energy-momentum`,
  `concept/longitudinal-transverse-separation`; `model/simc` (11 pages).
- Headline facts captured: nuclear-transparency table (T falls C>Fe>Au, ~flat in
  Q²; Table III verbatim), deradiated spectral-function extraction (IPSM/DWEEPY,
  Perey β=0.85 for Fe/Au), and L–T separations showing excess transverse strength
  at Q²=0.64 reduced at 1.8 (GeV/c)² (first L–T data on medium/heavy nuclei).
- Forward-link markers left for not-yet-written pages: [[ccqe]], [[fsi]],
  [[mec-2p2h]], [[minerva]]. No contradictions (single source).

## [2026-06-01] ingest | A dependence of the ν_μ CCQE-like cross section with TKI (2503.15047)
- Second source: MINERvA (Kleykamp et al.), NuMI ME beam ⟨E_ν⟩∼6 GeV, 10.61×10²⁰
  POT; ν_μ CCQE-like on C/CH/H₂O/Fe/Pb measured simultaneously vs transverse
  kinematic imbalance + muon/proton kinematics. Created `source/2503.15047`.
- Resolved four forward-link markers from the first ingest by creating the pages
  they pointed at: `experiment/minerva`, `channel/ccqe`, `concept/fsi`,
  `concept/mec-2p2h`.
- New targets: `target/ch` (scintillator reference), `target/o16` (water),
  `target/pb` (lead). New concept `concept/transverse-kinematic-imbalance` and
  `concept/unfolding-dagostini`. New models `model/genie` (MINERvA tune),
  `model/neut`, `model/nuwro`, `model/gibuu`.
- Updated `target/c12` and `target/fe56` with a neutrino-side CCQE-like section
  (both now carry electron (e,e'p) + ν_μ data); `concept/fsi` synthesizes the
  two FSI probes across both sources (transparency vs TKI).
- Headline facts captured: δP_T shifts to higher values with increasing A
  (FSI); ratios to CH per neutron ≈1 for C and water, deviate for Fe and Pb
  (largest for Pb, exceeding the MINERvA-tune prediction); generator ordering
  NEUT over-predicts > hN-GENIE ≈ NEUT > data > hA-GENIE/NuWro, GiBUU most
  consistent.
- 14 new pages + 2 updated; no contradictions with nucl-ex/0303011 (complementary
  electron vs neutrino probes; FSI grows with A in both).

## [2026-06-02] ingest | Simultaneous measurement of ν_μ quasielastic-like cross sections on CH, C, H₂O, Fe, and Pb as a function of muon kinematics at MINERvA (2301.02272)
- Created `source/2301.02272` — MINERvA (Kleykamp et al.), NuMI ME beam, peak
  E_ν ≈ 6.5 GeV, 10.61×10²⁰ POT; ν_μ CCQE-like on CH/C/H₂O/Fe/Pb measured
  simultaneously, double-differential in longitudinal/transverse muon momentum
  (P_∥, P_T). The muon-kinematics companion to the TKI paper 2503.15047 (same
  author/beam/exposure/targets), but with a looser **muon-only** signal
  definition (no proton requirement) vs the leading-proton requirement of
  2503.15047 — documented on `channel/ccqe`.
- Updated 5 targets (`pb`, `fe56`, `c12`, `o16`, `ch`), `experiment/minerva`,
  `channel/ccqe`, `concept/fsi`, `concept/mec-2p2h`, `concept/unfolding-dagostini`,
  `concept/spectral-function`, and models `genie` (added MnvGENIEv1: +49% 2p2h,
  −57% non-resonant π), `nuwro` (data prefer SF over LFG), `gibuu`. 13 pages
  updated, 1 created; no NEUT-specific claim in this paper so `model/neut` left
  unchanged.
- Headline facts: Pb/CH per-nucleon ratio always > 1 with a characteristic P_T
  shape that evolves slowly in P_∥ (constant above P_∥=4.5 GeV/c); Fe/CH ≈ 1.4–1.5
  vs model ≈ 1.2; C/water ratios near unity; level and P_T shape for Fe/Pb not
  reproduced by current generators; A-scaling not constant over momentum transfer.
- No hard contradiction, but a physics-judgment NOTE added to `concept/fsi`: the
  two MINERvA papers' generator-FSI framings (TKI: hN over-predicts, hA under;
  muon-kin: data prefer hA over hN, SF over LFG) are qualitatively consistent
  (both favor hA over hN and GiBUU) but use different observables, signal
  definitions, and central tunes — flagged for the human.

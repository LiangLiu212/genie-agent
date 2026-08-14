# Electron–C12 scattering — full generated phase space, exactly-one-proton selection (v1.0)

v1.0 opens the [v0.3](../prd-analyzer-v0.3/electron_c12_scattering.md) analysis
back up to the **full generated phase space**: the Dutta Q² = 1.28 ± 5 % slice
is dropped, keeping only

    qel                            (electron panels)
    qel && N_p(final state) = 1    (proton panels)

with the same samples (C12 full-EM t05 grid campaign 2026-07-26, 2M
events/tune) and the v0.3 exactly-one-proton convention. "Uncut" means the
full *generated* phase space: the t05 campaigns carry the generation cut
**EM-MinQ2Limit = 1.18 GeV²**, which remains the hard lower edge of every Q²
distribution — nothing below 1.18 exists in the samples.

## 1. QEL kinematics — E_e′, θ_e′, T_p, θ_p, Q², no Q² cut

![C12 QEL kinematics, no Q² cut, N_p=1, events/bin](kin_qel_c12_counts.png)

Raw events/bin (equal ntot = 2M/tune; area-normalized shape companion
`kin_qel_c12.png`), script
[`make_kin_qel_v1.py`](../template/make_kin_qel_v1.py) — the uncut
counterpart of v0.3 section 3, reading the v0.1 caches with no Q² mask. The
grey dashed lines on the Q² panel are the Dutta window as **reference only**
(nothing applied).

Selection counts (the legend N = qel events):

| tune | qel N (of 2M) | has_p | 0p | 1p | ≥2p |
|---|---|---|---|---|---|
| GEM26_11a_05_000 | 385,486 | 78.1 % | 21.9 % | 63.1 % | 15.0 % |
| GEM26_22a_05_000 | 385,229 | 76.9 % | 23.1 % | 62.2 % | 14.8 % |
| GEM26_22b_05_000 | 277,035 | 79.5 % | 20.5 % | 64.1 % | 15.4 % |
| GEM21_11a_05_000 | 345,033 | 79.0 % | 21.0 % | 63.6 % | 15.4 % |

(multiplicity split of the full qel sample, both hit-nucleon species;
panel ranges pooled p0.2–p99.8: E_e′ [0.3, 2.1] GeV, θ_e′ [28, 125]°,
T_p [0, 2] GeV, θ_p [0, 155]°, Q² [1.18, 3.62] GeV².)

- **The multiplicity split is nearly identical to v0.3's in-window one**
  (there: 0p 20.1–22.6 %, 1p 62.1–63.9 %, ≥2p 15.3–16.0 %): within the
  generated Q² ≥ 1.18 range the FS-proton multiplicity is essentially
  Q²-independent, so the Dutta slice never biased it.
- **22b's overall qel deficit is the dominant inter-tune difference**
  (277k vs 345–385k qel events of the same 2M): an overall scale visible in
  every panel, not a shape effect — the `QELEventGenerator`+SF combination
  yields fewer accepted QEL events across the whole phase space.
- Q² falls steeply from the 1.18 edge (~2 decades to 3.6 GeV²); the Dutta
  window sits directly on the most-populated edge region, which is what made
  the v0.2/v0.3 slice statistics comfortable.
- T_p keeps its two-component structure in the full phase space: the QE bump
  (peak ≈ 0.7 GeV, the Q²-broadened image of the v0.3 slice's peak) over the
  low-T_p FSI-rescatter hump, with the N_p = 1 selection keeping the QE bump
  dominant for every tune. GEM21 (dashed) cuts off earliest in both E_e′
  (shoulder deficit below ≈ 0.9 GeV) and T_p (≈ 1.6 GeV endpoint).

Regenerate:
`pixi run python results/template/make_kin_qel_v1.py --target C12`.

# Simultaneous measurement of ν_μ quasielastic-like cross sections on CH, C, H₂O, Fe, and Pb as a function of muon kinematics at MINERvA

**Collaboration:** The MINERvA Collaboration (J. Kleykamp *et al.*)
**arXiv:** [2301.02272](https://arxiv.org/abs/2301.02272) [hep-ex]
**Journal reference / DOI:** (not stated in paper source)

---

## Beam / probe / exposure

- **Probe:** ν_μ (charged-current). Neutrino-dominated broad-band NuMI beam, horns set to focus positively-charged pions.
- **Beam production:** 120-GeV proton beam on a two-interaction-length graphite target, two parabolic focusing horns, 675-m decay pipe, 200 m of earth shielding.
- **Peak neutrino energy:** 6.5 GeV (the ⟨E_ν⟩ ~ 6 GeV "medium-energy" NuMI configuration; text states the earlier 3 GeV measurement and that this run's mean energy is "higher by a factor of two").
- **Exposure:** 10.61 × 10²⁰ protons on target (POT). First half of the exposure taken with the water target empty, second half with it full (to measure and subtract non-water backgrounds directly).
- **Flux constraint:** corrected with hadron-production data; further constrained using ν–e elastic scattering and low-recoil interactions from the same exposure. Flux uncertainty constrained to **3.9%**.
- **Target nuclei:** C, H₂O (water), Fe, Pb, and scintillator (CH / hydrocarbon). Each nuclear target covers only part of the hexagonal scintillator-plane area, so a different integrated flux is used per target material.
- **N_nucleons / fiducial mass:** (not stated in paper as explicit numbers). The water target is a flattened circular neoprene balloon 17–24 cm thick in the beam direction; solid targets configured so the passive material traversed (in g/cm²) is approximately equal.

## Detector / spectrometer setup

- **MINERvA detector** ([Aliaga:2013uqz]): nuclear-target region of thin passive targets (C, Fe, Pb, water) interspersed with 1.7-cm-thick active scintillator planes, followed by a scintillator-only (tracker) region, then electromagnetic and hadronic calorimetry.
- **MINOS near detector** ([Michael:2008bc]): located 2 m downstream of MINERvA; measures charge and momentum of final-state muons.
- **Muon reconstruction:** momentum = range inside MINERvA + (range or curvature) inside MINOS; muon angle measured in MINERvA.
- **Acceptance (reco):** muons within 17° of the neutrino beam, momentum 1.5–40 GeV/c (MINOS acceptance).
- **Simulation:** hit-level Geant4-based detector simulation overlaid with random beam data for beam-related accidental activity; includes time dependence of proton-beam intensity and water-target configuration. Beam line modeled with g4numi version 6 (Geant v9.4.p2).
- Angular / momentum resolution values: (not quoted explicitly in paper text).

## Simulation (interaction generator)

- **Generator:** GENIE 2.12.6 ([Andreopoulos:2009rq]).
- **QE model:** Llewellyn-Smith formalism. Nuclear effects via a Bodek-Ritchie high-momentum tail in the Fermi-momentum distribution of initial-state nucleons (BRRFG).
- **Tune:** MnvGENIEv1 (default GENIE adjusted to previous MINERvA data), with three modifications:
  1. **RPA:** Valencia Random Phase Approximation correction ("weak nuclear screening") added as a function of neutrino energy and three-momentum transfer.
  2. **2p2h / MEC:** Valencia multi-nucleon model added and modified by an empirical fit to previous MINERvA CH data; the modification **increases the integrated 2p2h interaction rate by 49%**, applied as the same fractional increase per proton-neutron pair for all nuclei.
  3. **Non-resonant pion production reduced by 57%** to agree with a fit to deuterium measurements.
- M_A: (not stated explicitly in paper text).

## Signal definition (truth-level)

Cross sections are defined as **any interaction with a muon in the final state**, where:
- muon angle ≤ 17° (relative to neutrino beam),
- muon momentum between **2 and 20 GeV/c**,
- **any number of nucleons allowed**,
- **no photons above 10 MeV** (to accommodate nuclear excitations),
- **no mesons**.

(Quasielastic-like: includes true QE, 2p2h/multi-nucleon, and pion-production events where the pion is absorbed in the nucleus.)

## Event selection (reco-level)

Cuts, in order described:
1. Muon candidate originating in MINERvA and reconstructed in MINOS near detector.
2. No minimum requirement on number of proton tracks.
3. No electron candidates (Michel electrons from π→μ→e decay chain) near the interaction vertex or any track endpoint.
4. Any non-muon reconstructed track required to satisfy proton-identification cuts based on energy-deposition pattern (rejects charged pions).
5. No more than one isolated cluster of energy in the detector (rejects neutral pions).
6. MINOS acceptance: muon within 17°, momentum 1.5–40 GeV/c.

Backgrounds and efficiencies determined separately for samples with and without identified proton tracks.

- **Background levels (non-quasielastic-like):** 36% in scintillator; 33–45% in nuclear targets (lowest in Pb).
- **Selected interactions after background subtraction:** ~1,000,000 in scintillator tracker; 25,000 in C (control region); 20,000 in water; 92,000 in Fe; 124,000 in Pb.
- **Backgrounds:** two categories — (a) interactions originating in scintillator but mis-reconstructed into a target; (b) non-QE-like interactions correctly reconstructed in a target. Constrained via sidebands (Michel-electron sideband enriched in charged pions; ≥2 extra energy clusters sideband enriched in neutral pions). Single-π⁰ background constrained by MINERvA's earlier π⁰ measurement.
- Selection efficiency: corrected per target region (value not quoted as a single number in text).

## Binning

The measurement is double-differential in longitudinal muon momentum (P_∥) and transverse muon momentum (P_T). Explicit bin edges are **not tabulated in the paper source**; the text states:

- The "peak" / highest-statistics P_∥ bin is **4.5 < P_∥ / (GeV/c) < 5.5**.
- The broad neutrino-energy beam populates P_∥ bins between **3.75 and 6.5 GeV/c**.

(Full P_T and P_∥ bin-edge tables: not stated in paper source — see open_questions.md.)

## Unfolding / acceptance correction

- **Method:** D'Agostini iterative Bayesian unfolding ([DAgostini:1994fjx], [DAgostini:2010hil]) to correct for detector resolution.
- Number of iterations / regularization choice: (not stated in paper text).
- After unfolding, each target region is corrected for efficiency.

## Efficiency correction

After background subtraction and unfolding, each of the different target regions is corrected for efficiency separately. (No dedicated efficiency figure in the main text.)

## Cross-section formula

The paper does not present an explicit LaTeX cross-section formula. The procedure stated verbatim:

> "the cross section is found by dividing by the number of target nucleons and by the total integrated flux appropriate for each target."

Schematically:

```
dσ/d(P_T,P_∥) = N_unfolded,eff-corrected(P_T,P_∥) / (N_nucleons × Φ_integrated)
```

where N_unfolded,eff-corrected is the background-subtracted, unfolded, efficiency-corrected event count in each (P_T, P_∥) bin; N_nucleons is the number of target nucleons for that material; Φ_integrated is the integrated neutrino flux appropriate for that target's illumination.

For cross-section **ratios** to scintillator, the scintillator cross section is built from a linear combination of 12 transverse detector "wedges" matched to each target's illumination, so the incident flux is the same to better than 1% in numerator and denominator.

## Systematic uncertainties

Three sources, evaluated with a multi-universe technique (correlations between bins and targets retained):
- **Flux:** from hadron production and focusing; constrained to **3.9%** via ν–e scattering. Dominant for absolute cross sections in most bins.
- **Neutrino interaction model:** dominated by background-process modeling, in particular final-state-interaction (FSI) uncertainties.
- **MINERvA detector:** dominated by muon reconstruction (muon energy scale), small but growing at high P_T where the cross section falls steeply.

In **ratios** to scintillator, flux and muon-energy-scale uncertainties cancel to first order; the largest remaining systematics are reconstruction uncertainties that do not cancel (e.g. FSI in the target nuclei). In the most populated P_∥ bin, systematic and statistical uncertainties are comparable; in other bins statistics dominate. In most kinematic regions the cross-section-ratio uncertainty is well below 10%.

## Main results

Headline statements (verbatim from abstract / conclusions):

- "first simultaneous measurement of the quasielastic-like neutrino-nucleus cross sections on C, water, Fe, Pb and scintillator (hydrocarbon or CH) as a function of longitudinal and transverse muon momentum."
- "The ratio of cross sections per nucleon between Pb and CH is always above unity and has a characteristic shape as a function of transverse muon momentum that evolves slowly as a function of longitudinal muon momentum. The ratio is constant versus longitudinal momentum within uncertainties above a longitudinal momentum of 4.5 GeV/c."
- "The cross section ratios to CH for C, water, and Fe remain roughly constant with increasing longitudinal momentum, and the ratios between water or C to CH do not have any significant deviation from unity."
- "Both the overall cross section level and the shape for Pb and Fe as a function of transverse muon momentum are not reproduced by current neutrino event generators."
- Fe/CH ratio ≈ 1.4–1.5 per nucleon; MINERvA's underlying model (not tuned to Fe/Pb) predicts ≈ 1.2.
- "MINERvA ... sees evidence of scaling as a function of A that is not constant over the momentum transferred to the nucleus, and not predicted by any generators considered."
- Data prefer GENIE's hA FSI model over hN; in NuWro the data prefer the Spectral Function over LFG; GIBUU comparison may indicate cascade-type models better characterize pion intranuclear absorption in heavy nuclei.

**Figures (main text):**

- **Fig. 1** (`fig:zvertex`, `fig1.png`): Reconstructed vertex location in the upstream MINERvA region (data vs simulation, full-water configuration), two-track interactions; nuclear targets appear as peaks. Used to constrain scintillator background.
- **Fig. 2** (`fig:phys_sidebands`, `fig2a–d.png`): Top — single-Michel-electron sideband (left) and extra-energy-cluster sideband (right) for Pb. Bottom — signal region in Pb (left) and CH (right) after backgrounds and signal tuned, for the peak P_∥ bin.
- **Fig. 3** (`fig:xsec`, `fig3.png`): Cross section vs P_T in the highest-statistics P_∥ bin, data vs simulation, all five target materials. Inner/outer error bars = statistical/total.
- **Fig. 4** (`fig:xsec_2d2`, `fig4.png`): Quasielastic-like cross-section ratios to scintillator vs muon momenta on Pb, Fe, water, C. Points = data, solid lines = model. **(Primary headline result.)**
- **Fig. 5** (`fig:models`, `fig5.png`): Pb/CH cross-section ratio compared to several GENIE/NuWro/GIBUU model choices, with χ² between each model and data. (Model-comparison/discussion.)

**Supplemental Material figures:**

- **Fig. 6** (`fig:syst_err`, `fig6.png`): Uncertainties on the Pb/scintillator cross-section ratio as a function of muon kinematics.
- **Fig. 7** (`fig:sup_xsec_uncertainties`, `fig7a–c.png`): Cross-section uncertainties on scintillator tracker (top) and Pb (bottom) vs P_∥ and P_T.
- **Fig. 8** (`fig:sup_xsec_ch_2d`, `fig8a–c.png`): Absolute cross sections on scintillator tracker (top), iron (middle), lead (bottom) vs P_∥ and P_T.

## Released numerical data

(no ancillary data released — no `anc/` directory in the arXiv source tarball)

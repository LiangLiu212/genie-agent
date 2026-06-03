# Measurement of the *A* dependence of the ν_μ charged-current quasielastic-like cross section as a function of muon and proton kinematics at ⟨E_ν⟩ ∼ 6 GeV

**Collaboration:** The MINERvA Collaboration (J. Kleykamp *et al.*)
**arXiv:** [2503.15047](https://arxiv.org/abs/2503.15047) [hep-ex]
**Journal reference / DOI:** (not stated in source — submitted as a PRD manuscript; tex uses `revtex4-2` with `prd` option; DOI not present in the tex or `00README.json`)

---

## 1. Beam / probe / exposure

- **Probe / flavor:** ν_μ (NuMI medium-energy, neutrino-enhanced horn polarity, ∼3.8% ν̄ contamination).
- **Beam:** NuMI wide-band beam at Fermilab; 120 GeV protons on a graphite target, two-horn focusing, 675 m decay region.
- **Mean neutrino energy:** ⟨E_ν⟩ ∼ 6 GeV (ME configuration).
- **Exposure (this analysis):** 10.61 × 10²⁰ POT in the neutrino-enhanced ME configuration. (MINERvA total ME accumulation quoted as 24.5 × 10²⁰ POT; LE was 5.4 × 10²⁰ POT at ⟨E_ν⟩∼3 GeV.)
- **Data-taking period:** 2012–2019.
- **Target nuclei:** C, CH (scintillator), H₂O, Fe, Pb — measured simultaneously in the same detector and flux.
- **Z, N, and event statistics per target** (Table I in the paper, "Event statistics after all cuts"):

  | Target | Z | N | Events | Purity |
  |--------|---|---|--------|--------|
  | Tracker (CH) | 7 | 6 | 218,000 | 60% |
  | Carbon | 6 | 6 | 2,255 | 54% |
  | Water | 10 | 8 | 1,563 | 47% |
  | Iron | 26 | 30 | 8,577 | 47% |
  | Lead | 82 | 124 | 8,660 | 55% |

  (Z=7, N=6 listed for the CH/tracker reflects the effective scintillator composition as given in the source.)
- **Number of targets (T):** Determined from target mass and known composition; fiducial C, Fe, Pb mass uncertainties < 1%; water mass uncertainty ≈ 1%.

## 2. Detector / spectrometer setup

- **MINERvA detector:** 208 hexagonal planes, each 127 triangular polystyrene scintillator strips (height ∼1.7 cm, width ∼3.3 cm), three angular (UVX) orientations enabling 3D tracking. Overall length ∼5 m.
- **Nuclear target region:** ∼1.25 m upstream region with passive C, Fe, Pb, and water targets interleaved with scintillator planes.
- **Tracker region:** 124 contiguous scintillator planes downstream of the nuclear targets.
- **Calorimetry:** downstream EM calorimeter (20 scintillator planes with 2 mm Pb), then hadronic calorimeter (20 planes with 2.54 cm steel).
- **Muon spectrometer:** magnetized MINOS near detector, 2 m downstream, used as a muon range stack and spectrometer (sets the muon momentum/charge requirements).
- **Proton energy:** measured by range; Bragg-peak end-of-track hit pattern used to flag/reject inelastically scattering or exiting protons and to veto pions.
- Angular/momentum resolution: (not quoted numerically in the main tex).

## 3. Simulation

- **Primary generator (analysis central value):** GENIE v2.12.6, modified to "MINERvA tune v1.0.1" ("MINERvA tune").
- **Nuclear model:** relativistic Fermi gas + Bodek–Ritchie high-momentum tail (SRC); Fermi momentum k_F = 0.221 GeV/c. Density: Gaussian for nuclei below Ca, 2-parameter Woods–Saxon for heavier nuclei.
- **QE:** Llewellyn-Smith formalism; vector form factors BBBA05; axial dipole form with **M_A = 0.99 GeV/c²**.
- **2p2h:** IFIC Valencia model, simulated only for three-momentum transfer < 1.2 GeV/c; enhanced in specific (E, q₃) regions by empirical fits to MINERvA LE data.
- **RPA:** Valencia-model RPA applied (Fermi-gas appropriate); carbon screening used for heavier nuclei as an approximation.
- **Resonance:** Rein–Sehgal, **M_A^RES = 1.12 GeV/c²**; non-resonant pion production reduced significantly (bubble-chamber reanalysis + MINERvA data).
- **DIS:** leading-order with Bodek–Yang low-Q² modification; AGKY hadronization.
- **FSI:** INTRANUKE-hA; elastic hA FSI bug fixed by reweighting those events to no-FSI for C, O, Fe, Pb.
- **Flux:** GEANT4 NuMI beamline simulation, hadron-production reweighted to external data (MIPP, NA49), constrained in situ by ν–e elastic scattering.
- **Detector response:** GEANT4 v4.9.3.p6, QGSP_BERT physics list.
- **Comparison generators** (via NUISANCE): GENIE v3 G18_01a, G18_01b, G18_10a, G18_10b (untuned `_00_000`); NuWro 19.02 (LFG and SF); GiBUU release 2019 patch 8 (T0 and T1); NEUT 5.4.1 (LFG).

## 4. Signal definition (truth-level)

CCQE-like ν_μ interaction on CH, C, H₂O, Fe, or Pb. Truth-level phase space:

- Muon: angle w.r.t. beam < 17°, momentum 2 GeV/c < p_μ < 20 GeV/c.
- Proton: angle < 70°, momentum 500 MeV/c < p_p < 1100 MeV/c (leading proton used if more than one).
- No mesons, no baryons heavier than neutrons, no photons above 10 MeV (photons < 10 MeV allowed, from nuclear de-excitation).

2p2h and Δ-resonance-then-pion-absorption processes producing a proton and no pion are part of the CCQE-like signal.

## 5. Event selection (reconstruction-level)

Cuts applied (in the order described):
1. Negatively charged muon candidate reconstructed in MINOS (sets the 2–20 GeV/c, <17° muon window).
2. At least one proton candidate (range-based energy; Bragg-peak hit pattern required for a well-reconstructed proton; pion Bragg-peak veto).
3. No Michel-electron candidates (from π → μ → e) near the vertex or any track endpoint — rejects charged pions.
4. No more than one isolated energy cluster — reduces neutral-pion background.
5. Highest-momentum proton matching the constraints used in the TKI calculation.

Note: a commented-out author note in the source records that the *reconstruction* fiducial is wider than the *signal* cut (reco proton < 90°, 400 < p_p/MeV < 1300) to avoid cutting on the efficiency edge — flagged in open_questions.

- **Selected events:** see Table in §1 (e.g. 218,000 in CH tracker; 8,660 in Pb).
- **Purity (background fraction):** purities ≈ 47–60% (so background fraction ≈ 40–53%); backgrounds dominated by undetected charged/neutral pions plus a "plastic" (surrounding scintillator) background for passive targets.
- **Selection efficiency:** 5–8% for the passive nuclear targets, 28% in the tracker (per simulation).

## 6. Binning

The full bin edges are not tabulated in the source tex; they are encoded in the released ancillary `.txt` data files. The released `δP_T` (lead) absolute cross-section file gives bin centers 0.1, 0.3, 0.5, 0.8, 1.38, 2.38 GeV (six bins). Binning and number of unfolding iterations were optimized per variable. (Explicit edge tables not provided in paper — see ancillary files in §13.)

Measured variables (one absolute cross section + one CH-ratio per variable):
- TKI: δP_T, δP_{Tx}, δP_{Ty}, δα_T, φ_T (acoplanarity), δP_L, P_n.
- Muon: p_μ, p_{μT}, θ_μ.
- Proton: p_p, p_{pT}, θ_p.

## 7. Unfolding / acceptance correction

- **Method:** D'Agostini iterative unfolding, validated with reweighted ("warped") model studies.
- **Regularization:** number of iterations optimized per variable (binning and iteration count optimized together).
- Unfolding matrix U_ij in the cross-section formula removes reconstruction smearing.

## 8. Efficiency correction

After unfolding, distributions divided by the signal reconstruction efficiency (true signal passing reco cuts / true signal in selection phase space), evaluated from simulation as a function of target position/type and muon/proton angles and momenta. Example efficiency vs δP_T for CH and Pb shown in the Supplement (Fig. Supp.5).

## 9. Cross-section formula

$$\left(\frac{d\sigma}{dX}\right)_i = \frac{\sum_j U_{ij}\,(N^{measured}_j - N^{background}_j)}{\epsilon_i\, T\, \Phi_i\, \Delta X_i}$$

where:
- d σ/dX = differential cross section in variable X,
- N^measured_j = measured events in reco bin j,
- N^background_j = estimated background in reco bin j,
- U_ij = unfolding matrix (reco bin j → truth bin i),
- ε_i = reconstruction efficiency in bin i,
- Φ_i = integrated total neutrino flux,
- T = number of target nucleons/targets for that target type,
- ΔX_i = bin width.

Auxiliary derived TKI variables:
$$\delta P_L = \tfrac{1}{2}R - \frac{m_{A'}^2 + \delta P_T^2}{2R}, \quad R \equiv m_A + p^\mu_L + p^p_L - E^\mu - E^p$$
$$P_n = \sqrt{\delta P_T^2 + \delta P_L^2}$$
with m_A, m_{A'} the initial/residual nucleus masses, p_L and E the longitudinal momenta and energies of the muon and proton.

Cross sections are reported per nucleon; ratios to CH are scaled by the number of neutrons in the target.

## 10. Systematic uncertainties

- **Method:** multi-universe; cross section re-extracted under each varied source, with inter-bin and inter-target correlations retained.
- **Categories:** flux, neutrino-interaction model, detector effects.
- **Dominant term:** proton reconstruction (detector) uncertainty dominates the absolute cross-section uncertainty — driven by the scintillator-light-to-energy conversion for proton Bragg-peak hits.
- Flux uncertainty dominated by hadron production and focusing (constrained by external hadron-production data and in-situ ν–e scattering).
- Interaction-model uncertainty dominated by background modeling and FSI.
- **Ratios to CH:** flux and hadron/muon reconstruction uncertainties largely cancel, reducing the total uncertainty.
- Per-bin sizes are shown as figures (per-variable uncertainty-breakdown plots), not quoted as single numbers in the tex.

## 11. Main results

Headline statements (verbatim/near-verbatim from abstract and conclusions):

- "The first simultaneous measurements of the ν_μ quasielastic-like cross section on C, CH, H₂0, Fe, and Pb targets as a function of kinematic imbalance variables in the plane transverse to the incoming neutrino direction are presented."
- "The range of predictions of the different models tends to cover the data but the degree and consistency of the agreement suffers in regions, and on higher A targets, where the final state interactions are expected to be more pronounced."
- δP_T distribution shifts toward higher values for higher-A targets (Fe, Pb), consistent with increased FSI; the MINERvA tune describes this except for Pb, where the data shift is even larger than predicted.
- Cross-section ratios to CH per neutron are consistent with unity for water and carbon, with clear deviations from unity for Fe and Pb.
- "These data show clearly that nuclear effects are important and their influence increases with atomic mass A." Simple neutron-number scaling works for smaller nuclei; FSI produces more complex behavior for larger nuclei.
- Among generators: NEUT tends to over-predict (especially large targets); GENIE hN versions approach NEUT; hA versions of GENIE and NuWro tend to under-predict the data in high-FSI regions; GiBUU most consistently describes the data across targets and variables.

Key figures (rendered to `figures/`):
- `Figures/TKI_var.eps` — schematic of TKI variables (`fig:TKI`).
- `Figures/xsec_five_square/*.eps` — the primary differential cross sections per target for each of the 13 variables (δP_T, φ_T, δα_T, δP_{Tx}, δP_{Ty}, δP_L, P_n, p_μ, p_{μT}, θ_μ, p_p, p_{pT}, θ_p). These are the headline results.
- `Figures/fluxes.eps` — per-target flux ratio to scintillator (`fig:fluxes`).

## 12. Released numerical data

`anc/` **is present.** No `README` file is included in `anc/` (flagged in open_questions). Contents:

- **`anc/tki_release.root`** (1.5 MB) and **`anc/tki_release_mnv.root`** (36.7 MB) — ROOT releases (the latter is the MnvH/MINERvA-format release with full covariance objects).
- **`anc/absolute/`** — 420 ASCII `.txt` files organized by variable subdirectory: `alpha/`, `combined/`, `dpt/`, `dptx/`, `dpty/`, `muon/`, `phi/`, `pl/`, `pn/`, `proton/`.
  - For each variable and target there is an absolute cross-section file plus `_covariance.txt` and `_correlation.txt`, and `_flux` variants giving the appropriately-fluxed CH for each target ratio (e.g. `absolute_xsec_dpt_ch_iron_flux.txt`).
  - `combined/` (42 files) holds combined cross sections and full correlation matrices per variable.
  - **Column format** (per file header), e.g. `absolute/dpt/absolute_xsec_dpt_lead.txt`:
    - `# X-axis: #delta P_{T} (GeV)`
    - `# Y-axis: d#sigma/d#delta P_{T} (cm^{2}/GeV/nucleon)`
    - columns: `X` (bin center), `Content` (cross section), `Error`.
- **Contact author:** (not stated in `anc/`; corresponding author is J. Kleykamp, now at University of Mississippi — per author list).

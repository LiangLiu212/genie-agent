# Open questions — nucl-ex/0303011

- **No `anc/` directory** in the arXiv source tarball: no machine-readable numerical data released. All result numbers (transparencies, yield ratios) are only in the in-text tables (Tables II and III). Recorded as "(no ancillary data released)" in the summary.

- **No journal DOI / reference in the source.** The tex has no `\journal`, volume, or DOI field. This is a long-form paper; some results were previously published (Phys. Rev. Lett. 80, 5072 (1998) and Phys. Rev. C 61, 061602(R) (2000)), but the journal reference for this specific manuscript is not stated. Needs lookup if a citation is required.

- **Integrated luminosity / collected charge not stated** as a single number. Beam current (10–60 μA) and target thickness (≈200 mg/cm²) are given, but no integrated charge or N_targets. Absolute normalization is handled internally by SIMC (luminosity × phase space / generated events).

- **Possible units typo in SOS angular resolution.** The tex states "an inplane (out-of-plane) angular resolution of 4.5(0.5) msr" for the SOS (line ~429). Angular resolution should be in mrad, not msr (msr is a solid-angle unit). The HMS value just above is correctly given in mrad (0.8/1.0 mrad). Reproduced verbatim in the summary but flagged here as a likely source typo.

- **Selected event count and background fraction not stated.** The paper gives efficiencies and deadtimes but no total selected (e,e'p) event count or explicit background fraction (spectra described as "clean").

- **Explicit (E_m, p_m) bin edges not tabulated.** Only integration windows / shell-region cuts are given; the per-bin grid used for the deradiation/phase-space correction is not stated in the paper.

- **Figures #9 (fig9, carbon S(E_m)) and #13 (fig13, gold S(E_m))** are flagged in keep_proposal.md: they show measured spectral functions (an (e,e'p) headline-type observable) but each is purely a single-IPSM-model comparison. Human should decide keep vs drop given the raw spectra (#3, #5) and momentum distributions (#6, #8) are already kept.

- **Fig 9 error bars are undocumented, and the author data file carries statistical errors only.** Column 4 of `data/Dipingkar-dutta-data-prc_figs/fig9_q1p2.dat` is 0.84% (p-shell peak) to 3.3% (E_m = 77.5 MeV) per bin, scaling like 1/sqrt(N) — statistical. The published Fig. 9 bars, pixel-measured against the zero-value markers, are ±0.046 MeV^-1 = 8.1% at E_m = 17.5 MeV and ±0.013 = 4.7% at 22.5 MeV (5–10× column 4; hidden under the markers everywhere else, bound < 0.006 absolute). The tex never says what the plotted bars contain. Magnitudes are consistent with stat ⊕ ~2% point-to-point systematic ⊕ ~5% model dependence for C (radiative corrections, off-shell σ_cc1, correlation corrections; tex ~1178–1187), with the sharp p-shell peak further inflated (iterative de-radiation is most model-sensitive where the spectrum is steepest). **Open:** confirm (thesis or author) what the published bars include. Until resolved, fit with σ_i = col4 ⊕ 2% ⊕ 5% (the 5% largely bin-correlated), override the 17.5/22.5 bins with the measured published bars (8.1%/4.7%), and float the overall normalization.

- **The two fig 6 Q² = 0.64 data files disagree with the published figure.** In print all
  four Q² coincide within marker size (caption: each rescaled so its |p_m|<300 integral
  equals the Q² = 1.8 one), but `data/Dipingkar-dutta-data-prc_figs/fig6_{top,bot}_q0p6.dat`
  sit 1.07–1.44× above the q1p8 files with a p_m-dependent ratio (medians ×1.27 / ×1.33;
  dip at |p_m| = 20, max at 140), while the q1p2/q3p2 files match print within ~10 %.
  Either the q0p6 files predate the caption's rescale, or they are the *other* Q² = 0.64
  setting (ε = 0.38 backward angle — more transverse-weighted, qualitatively consistent
  with sitting high). **Open:** confirm with the author; until then treat the two q0p6
  fig6 files as shape-only, not comparable to the published normalized panels.
  (Found while replotting: `report/dutta-e91013-figures.md` §3.)

- **All 12 fig6/fig7 momentum-distribution files are exactly left–right symmetrized**
  (y(−p_m) ≡ y(+p_m) to full file precision — 8 independent values per 16-row file), so
  the ± asymmetry the paper discusses (tex ~922, ~1141–1161) is absent from the files by
  construction. Fit in |p_m| or account for the doubled bins.

- **Fig 9 / Fig 11 spectral-function normalization is undocumented (full-occupancy scale, not raw distorted yield).** The fig9 data integrate to Σ·(5 MeV) = 6.080 ± 0.029 ≈ Z = 6 for carbon (p-shell window 10–25 MeV alone: 4.20 ≈ 4), and fig11 to 18.2 ≈ iron's in-window IPSM strength — yet the text states S^derad still contains FSI absorption, and the same kinematics give T(C, 1.28) = 0.60(2) with a 1.11 ± 0.03 correlation factor applied to the PWIA, so the raw distorted integral should be ≈ T/1.11 × 6 ≈ 3.2. The plotted data were evidently renormalized to the IPSM/full-occupancy scale for the shape comparison; the captions of Figs. 6–8 state their normalization but Fig. 9's does not. **Open:** the exact scale convention (divide by T×corr, or integrals matched to IPSM?). Until resolved, treat fig9_q1p2.dat as shape + relative shell occupancy only; converting to absolute distorted yield (×≈0.54) drags in T's ±3.3% stat and the correlation factor's ±2.7%.

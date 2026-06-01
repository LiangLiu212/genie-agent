# Open questions — nucl-ex/0303011

- **No `anc/` directory** in the arXiv source tarball: no machine-readable numerical data released. All result numbers (transparencies, yield ratios) are only in the in-text tables (Tables II and III). Recorded as "(no ancillary data released)" in the summary.

- **No journal DOI / reference in the source.** The tex has no `\journal`, volume, or DOI field. This is a long-form paper; some results were previously published (Phys. Rev. Lett. 80, 5072 (1998) and Phys. Rev. C 61, 061602(R) (2000)), but the journal reference for this specific manuscript is not stated. Needs lookup if a citation is required.

- **Integrated luminosity / collected charge not stated** as a single number. Beam current (10–60 μA) and target thickness (≈200 mg/cm²) are given, but no integrated charge or N_targets. Absolute normalization is handled internally by SIMC (luminosity × phase space / generated events).

- **Possible units typo in SOS angular resolution.** The tex states "an inplane (out-of-plane) angular resolution of 4.5(0.5) msr" for the SOS (line ~429). Angular resolution should be in mrad, not msr (msr is a solid-angle unit). The HMS value just above is correctly given in mrad (0.8/1.0 mrad). Reproduced verbatim in the summary but flagged here as a likely source typo.

- **Selected event count and background fraction not stated.** The paper gives efficiencies and deadtimes but no total selected (e,e'p) event count or explicit background fraction (spectra described as "clean").

- **Explicit (E_m, p_m) bin edges not tabulated.** Only integration windows / shell-region cuts are given; the per-bin grid used for the deradiation/phase-space correction is not stated in the paper.

- **Figures #9 (fig9, carbon S(E_m)) and #13 (fig13, gold S(E_m))** are flagged in keep_proposal.md: they show measured spectral functions (an (e,e'p) headline-type observable) but each is purely a single-IPSM-model comparison. Human should decide keep vs drop given the raw spectra (#3, #5) and momentum distributions (#6, #8) are already kept.

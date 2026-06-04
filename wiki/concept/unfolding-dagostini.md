---
title: D'Agostini iterative unfolding
type: concept
tags: [concept, unfolding, analysis-method, neutrino-scattering]
updated: 2026-06-02
sources: [2503.15047, 2301.02272]
---

# D'Agostini iterative unfolding

An iterative Bayesian deconvolution that removes detector smearing, mapping
reconstructed bins back to truth bins. Standard in neutrino cross-section
analyses; the regularization is set by the number of iterations.

## Use at MINERvA (2503.15047)

- Applied to every measured [[transverse-kinematic-imbalance]] / kinematic
  distribution; the unfolding matrix U_ij (reco bin j → truth bin i) appears in
  the cross-section formula (2503.15047):

  ```
  (dσ/dX)_i = [ Σ_j U_ij (N^meas_j − N^bkg_j) ] / (ε_i · T · Φ_i · ΔX_i)
  ```

  with ε the efficiency, T the number of targets, Φ the integrated flux, ΔX the
  bin width (2503.15047).
- **Number of iterations optimized per variable**, jointly with the binning;
  validated with reweighted ("warped") model studies (2503.15047).

The companion MINERvA muon-kinematics analysis (2301.02272) applies the same
D'Agostini iterative Bayesian unfolding to correct detector resolution in the
(P_∥, P_T) cross sections; the number of iterations is (not stated) in that
paper's text (2301.02272).

This is a distinct, model-iterative method — contrast the radiative-correction
iteration used to "deradiate" the (e,e'p) [[spectral-function]] in
nucl-ex/0303011, which the authors there explicitly note is *not*
D'Agostini/SVD. Source: [[source/2503.15047]], [[source/2301.02272]].

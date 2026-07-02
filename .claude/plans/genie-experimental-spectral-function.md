# Extract the experimental (distorted) spectral function S^D from GENIE

## Context

The fig9 overlay (`results/prd-analyzer/em_dutta_fig9_q1p28.png`) is a shape comparison:
each model is area-matched to the data's occupancy-scale integral (6.08 ~ Z) because the
data's absolute normalization is convention-defined (see
`papers/nucl-ex_0303011/open_questions.md`) and GENIE's absolute rate was unused.

This plan upgrades that to the real thing: apply Dutta's own PWIA estimator
(`longpaper2.tex:843-875`) to reconstructed GENIE events and extract
**S^D_GENIE(Em, pm)** on an absolute per-nucleus scale. Then
`int d3pm (|pm| < 300)` gives the fig9 observable with no area-matching, and the window
integral `int S^D dEm d3pm` (Em < 80) is GENIE's transparency analogue, directly
comparable to the paper's T(C, 1.28) = 0.60(2) x (1/1.11 correlation) ~ 0.54 x Z ~ 3.2.

## The estimator (data -> GENIE dictionary)

Dutta: `S^D = 1/(L*H) * sum_counts 1/(sigma_cc1 * K) * C^rad`, per (Em, pm) bin.

| experiment | GENIE analogue |
|---|---|
| counts in (Em, pm) bin | reconstructed events: Em = omega - Tp - Trec, pm = \|q - pp\| (post-FSI leading proton -- S^D is *defined* FSI-distorted) |
| luminosity L | sigma_tot / N_generated (monoenergetic fixed target: absolute bin yield = sigma_tot * n/N) |
| C^rad (radiative unfolding) | = 1 (GENIE has no radiation; matches the deradiated data) |
| sigma_cc1 * K per count | per-event 1/(E_p * p_p * sigma_cc1), sigma_cc1 at the event's reco kinematics, off-shell flag 0 (Ebar = sqrt(pm^2 + m^2)) |
| H(Em, pm) phase space | flat companion MC over the same generation region + cuts |

Key identity (from `simc_gfortran/physics_proton.f:51-62`): K = E_p * p_p is exactly the
Jacobian dE_p dOmega_p -> d3pm, so d6sigma = sigma_cc1 * S(Em,pm) * dE_e' dOmega_e d3pm.
Weighting events by 1/(K*sigma_cc1) and dividing by H (same measure) gives the bin-averaged
S^D directly:

```
S^D(bin) = [sigma_tot / N_gen] * sum_{i in bin} 1/(E_p,i * p_p,i * sigma_cc1,i) / H(bin)
```

Use the SAME sigma_cc1 for all five models regardless of what generated them -- the
sigma-model mismatch is part of what the estimator measures, identically on the data side
(the paper's ~5 % model dependence).

## Steps

1. **sigma_cc1 module** -- `results/prd-analyzer/deforest.py`: numpy port of `sigMott`,
   `fofa_best_fit` (Bosted PRC 51, 409) and `deForest` (flag 0) from
   `simc_gfortran/physics_proton.f` @ `60c2047`. Units: microbarn * MeV^2 / sr^2.
   Per-event inputs: Ein, E_e', theta_e, Q^2, omega, q, p_p vector (theta_pq, phi), Em, pm.
   *Validation*: also port `sigep`; at pm -> 0, Em -> 0 the deForest on-shell limit must
   reproduce the elastic sigep at the same kinematics; check flag 0 vs -1 agree at pm = 0.

2. **Streaming builder** -- `build_cache_sd.py`: same skeleton as `build_cache_q2.py` /
   `build_cache_acceptance.py`, but additionally cache per-event `E_p`, `p_p`, `theta_pq`
   (or the computed `w_cc1` weight directly -- decide when writing; caching the raw scalars
   is more flexible). Two fiducial variants, both cached:
   (a) Q^2 = 1.28 +- 5 % only (full 4pi arms) -- the clean-H version;
   (b) the HMS x SOS acceptance boxes (reuse `acceptance.py`).
   Record `sigma_tot` per model: read the gst `xsec` branch (verify availability + units,
   1e-38 cm^2; constant for a monoenergetic single-process sample) -- fallback: spline
   lookup from the tune's gmkspl xml at 2.445 GeV.

   DONE 2026-07-02: one pass -> cache/sd/<model>_{q2win,accept}.npz with raw scalars
   (El, theta_e, Q2, nu, qmag, Ep, pp, sin_gamma, cos_phi, E_miss incl Trec, p_miss);
   MAX_FILES=8 -> q2win ~835-940k, accept ~58-105k events/model.
   The gst files carry NO xsec branch -> sigma from the production's own gmkspl spline
   (path auto-extracted from the 20260611 gridlogs, xrdcp-cached, both QES channels
   linearly interpolated at 2.445; GENIE natural units 1/GeV^2 x 389.3793721 ub GeV^2;
   MUST filter tgt:1000060120 -- the GEM21 spline file is multi-target C12/Fe56/Au197
   and an unfiltered parse silently returns Au197). sigma(2.445, Q2>=1.18) [nb/nucleus]:
   LFG = SF = 23.610 (Rosenbluth ground-state-independent, as expected), SuSAv2 20.636,
   UnifiedQEL2024 15.804, UnifiedQEL 15.564. Selections verified: accept variant
   reproduces the acceptance-cache count exactly (7544/500k); 1/(K sigma_cc1) weights
   100 % finite-positive, p99/p1 spread 2.4-2.9 in the fig9 window. q2win requires
   has_p (the estimator counts (e,e'p) coincidences).

3. **Phase space H** -- `phase_space_h.py`: vectorized flat MC. Throw uniform
   (E_e', cos theta_e, phi_e, E_p, cos theta_p, phi_p) over a bounding region that covers
   the reconstruction window (Em in [-20, 120], pm in [0, 400] comfortably), apply the
   Q^2 >= 1.18 mask (and, for variant (b), the arm boxes incl. the e'-plane rotation
   convention from `acceptance.py`), reconstruct the same (Em, pm) from the thrown
   kinematics, and set H(bin) = V6 * n_flat(bin)/N_flat with V6 the product of the thrown
   ranges. N_flat ~ 1e8 (numpy, minutes). Mask bins with n_flat below a threshold (~50)
   -- acceptance-edge bins where H -> 0 blow up, as in the experiment.

   DONE 2026-07-02: exact importance sampling with per-throw volume weights instead of
   a plain bounding box -- variant (a) throws Q2 uniform IN the window (Jacobian
   dcos(theta_e) = dQ2/(2 E_b El), 100 % fiducial efficiency), T_p in a nu-tracking
   window ([nu-130, nu+25], weight = local range), proton direction as a cone about q
   (cos gamma in [cg_min(pm<=420), 1]); variant (b) throws the exact HMS/SOS boxes with
   the slope->solid-angle Jacobian 1/(1+yp^2+xp^2)^(3/2), phi_e integrated (x2pi).
   Q2 >= 1.18 imposed on BOTH variants (the t05 samples carry it). Variant (a) adds an
   El in [250, 2200] MeV fiducial bound (covers all in-grid events, zero loss; stored in
   the npz as the step-4 event-mask source of truth). N_flat = 2e8 each ->
   cache/sd/H_{q2win,accept}.npz (H, Herr, nflat, edges, bounds). q2win: 448/448 bins
   populated, H in [2.3e-2, 2.8e+1] MeV^2 sr^2; accept: 350/448 (the rest outside the
   acceptance -- masked at use). Split-sample (1e8, independent seed) check: median
   |dH/H| = 0.35 %, p99 = 11-17 % (low-count edge bins; propagate Herr in step 4).

4. **Extraction + figures** -- `plot_sd_extraction.py`:
   - 2D S^D(Em, pm) map per model (sanity: the P(k,E) ridge for the SF models);
   - `y(Em) = sum_l S^D(k,l) * Vol3pm(l)` over pm < 300 (Vol3pm = 4pi int pm^2 dpm per
     bin; full-sphere coverage holds for variant (a), for (b) it leans on the isotropy of
     S in the pm direction -- state it);
   - ABSOLUTE overlay on fig9 + a ratio panel;
   - report per-model `int S^D dEm d3pm` (Em < 80, pm < 300) vs 0.54 x Z ~ 3.2 (the
     paper's absorbed scale) and vs the data file's 6.08 (occupancy convention).

   DONE 2026-07-02: sd_2d_maps.png (SF ridge / LFG stripe visible in both fiducials) +
   sd_extraction_fig9.png (absolute overlay + GENIE/data ratio panel with the
   T/1.11 = 0.54 guide). Window integrals: LFG 3.505(8), SF 2.978(5), SuSAv2 3.221(6),
   UQEL2024 2.175(4), UQEL 2.137(4) -- the Rosenbluth/SuSAv2 models within +-9 % of the
   paper's absorbed scale 3.24 (I/6.08 = 0.49-0.58 vs measured T/1.11 = 0.54); the
   UnifiedQEL pair at 0.66x, tracking its smaller sigma_tot (15.6/23.6 nb). NEW
   cross-fiducial validation: UnifiedQEL S^D extracted through both fiducials agrees
   bin-by-bin over 232 common bins (median a/b = 0.946, median |pull| = 0.64) -- the H
   machinery is validated across three-orders-of-magnitude different volumes. Note: the
   acceptance fiducial never reaches 95 % pm-sphere Vol3 coverage in any Em row (its
   patch tops out at pm ~ 275), so its y(Em) is drawn as open circles / lower bound.

5. **Closure test** (validates the whole chain): a small LOCAL FSI-off run with
   `run_gevgen` (tune `GEM26_22b_05_000` with FSI disabled -- mechanism via the genie-tune
   overlay or the generator-list/hA knob, to be checked; ~500k events, local background
   job). With FSI off, the estimator must return the input SF: f(E) of `pke12_tot`
   (17.5 MeV peak) up to the calculable sigma_gen/sigma_cc1 reweight, and the integral
   -> Z within a few %. Bonus closure on SF+Rosenbluth: the reweight ratio
   sigma_Rosenbluth/sigma_cc1 is directly computable per event.

   NOTE 2026-07-02 (from the pre-FSI study, README section 9): the closure target
   "recover the input f(E)" applies to the UnifiedQEL variants ONLY. The Rosenbluth
   pair's pre-FSI E_m is a fixed 16.0-MeV delta (sampled removal energy not propagated
   into the outgoing kinematics), so its FSI-off closure would return that delta, not
   f(E); its E_m information content lives entirely in FSI transport. Also measured:
   INTRANUKE hA2018 shifts surviving protons down ~20 MeV in E_m (pre 16.0 -> post ~36),
   INCL does not (pre median 19.2 -> post peak 15-20).

6. **Docs**: README section 7 (method, dictionary table, integrals table, caveats);
   cross-link `report/simc-eep-normalization.md` (the H/genvol machinery is the SIMC
   analogue) and the open_questions entries (this extraction is the GENIE side of the
   normalization question).

## Open decisions

- Binning: Em 5 MeV (match the data grid) x pm 25 MeV/c over 0-400 as the default.
- H statistics/error propagation: include the MC stat of H(bin) in the S^D error bars.
- ~~sigma_tot source~~ RESOLVED: the gst has no xsec branch; sigma comes from the
  production's own gmkspl spline (auto-located via the campaign gridlog).
- FSI-off mechanism for the closure run (genie-tune overlay vs switching the FSI model in
  the tune family) -- needs a quick check before step 5.
- Whether variant (b) needs the collimator octagon or the rectangle suffices (start with
  the rectangle, consistent with the existing acceptance analysis).

## Cost

- Streaming: same scale as the existing builders (MAX_FILES = 4-20, 2-10M events/model,
  ~1-5 GB transferred each) -- the new columns are computed inline, no extra passes.
- Flat MC for H: pure numpy, minutes, local.
- Closure run: one local gevgen ~500k events (100k ~ 25-30 min -> ~2.5 h, background).

## Verification checklist

- [x] `deforest.py`: pm -> 0 limit reproduces `sigep`; units microbarn MeV^2/sr^2.
      DONE 2026-07-02: flag 0 == flag -1 at pm=0 to 2e-16; elastic closure
      `deforest*Ee/(pp*Mp*Ein) = sigep` exact (1.000000000000) at all five Dutta
      beam/angle settings; sigma_cc1*K positive/finite/smooth over Em in [0,100],
      pm in [0,400] at the Q2=1.28 setting (0/138 bad grid points). Port note:
      SIMC's sigMott takes the SCATTERED electron energy as e0 in its Q2-form
      (both sigep and deForest call it that way).
- [x] H(bin) stable against N_flat doubling (MC-converged). DONE 2026-07-02: 1e8
      (independent seed) vs 2e8: median |dH/H| 0.35 %; tails are low-n edge bins,
      handled by the n>=50 mask + Herr propagation.
- [ ] FSI-off closure: recovers `pke12_tot` f(E) peak position/width; integral ~ Z.
- [x] FSI-on integrals: reported with statistical errors; compared to 0.54 x Z and to
      the data's 6.08 with the normalization caveat spelled out. DONE 2026-07-02
      (README section 7 table).
- [x] Fig9 absolute overlay + ratio panel rendered in house style. DONE 2026-07-02
      (sd_extraction_fig9.png).

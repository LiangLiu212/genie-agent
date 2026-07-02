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

3. **Phase space H** -- `phase_space_h.py`: vectorized flat MC. Throw uniform
   (E_e', cos theta_e, phi_e, E_p, cos theta_p, phi_p) over a bounding region that covers
   the reconstruction window (Em in [-20, 120], pm in [0, 400] comfortably), apply the
   Q^2 >= 1.18 mask (and, for variant (b), the arm boxes incl. the e'-plane rotation
   convention from `acceptance.py`), reconstruct the same (Em, pm) from the thrown
   kinematics, and set H(bin) = V6 * n_flat(bin)/N_flat with V6 the product of the thrown
   ranges. N_flat ~ 1e8 (numpy, minutes). Mask bins with n_flat below a threshold (~50)
   -- acceptance-edge bins where H -> 0 blow up, as in the experiment.

4. **Extraction + figures** -- `plot_sd_extraction.py`:
   - 2D S^D(Em, pm) map per model (sanity: the P(k,E) ridge for the SF models);
   - `y(Em) = sum_l S^D(k,l) * Vol3pm(l)` over pm < 300 (Vol3pm = 4pi int pm^2 dpm per
     bin; full-sphere coverage holds for variant (a), for (b) it leans on the isotropy of
     S in the pm direction -- state it);
   - ABSOLUTE overlay on fig9 + a ratio panel;
   - report per-model `int S^D dEm d3pm` (Em < 80, pm < 300) vs 0.54 x Z ~ 3.2 (the
     paper's absorbed scale) and vs the data file's 6.08 (occupancy convention).

5. **Closure test** (validates the whole chain): a small LOCAL FSI-off run with
   `run_gevgen` (tune `GEM26_22b_05_000` with FSI disabled -- mechanism via the genie-tune
   overlay or the generator-list/hA knob, to be checked; ~500k events, local background
   job). With FSI off, the estimator must return the input SF: f(E) of `pke12_tot`
   (17.5 MeV peak) up to the calculable sigma_gen/sigma_cc1 reweight, and the integral
   -> Z within a few %. Bonus closure on SF+Rosenbluth: the reweight ratio
   sigma_Rosenbluth/sigma_cc1 is directly computable per event.

6. **Docs**: README section 7 (method, dictionary table, integrals table, caveats);
   cross-link `report/simc-eep-normalization.md` (the H/genvol machinery is the SIMC
   analogue) and the open_questions entries (this extraction is the GENIE side of the
   normalization question).

## Open decisions

- Binning: Em 5 MeV (match the data grid) x pm 25 MeV/c over 0-400 as the default.
- H statistics/error propagation: include the MC stat of H(bin) in the S^D error bars.
- sigma_tot source: gst `xsec` branch vs spline lookup (verify the branch first).
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

- [ ] `deforest.py`: pm -> 0 limit reproduces `sigep`; units microbarn MeV^2/sr^2.
- [ ] H(bin) stable against N_flat doubling (MC-converged).
- [ ] FSI-off closure: recovers `pke12_tot` f(E) peak position/width; integral ~ Z.
- [ ] FSI-on integrals: reported with statistical errors; compared to 0.54 x Z and to
      the data's 6.08 with the normalization caveat spelled out.
- [ ] Fig9 absolute overlay + ratio panel rendered in house style.

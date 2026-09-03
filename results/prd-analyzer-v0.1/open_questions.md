# Open questions — prd-analyzer v0.1

- **SuSAv2 on Fe56 is a scaled-C12 surrogate, not a genuine Fe56 calculation.**
  (Corrected 2026-07-15 — an earlier version of this note said "scaled Ar40": the
  Ar40 tables in `data/evgen/hadron_tensors/crpa_susav2/` are CC/CRPA only.) The
  **EM** QE hadron tensor exists **only for C12** (`SuSAv2_1000060120_QE_EM*.dat`;
  the config also references an H1 EM file that is absent on disk), so for electron
  scattering GENIE serves Fe56 via `XSecScaling` of the **C12** EM tensor. The June
  GEM21_11a_05 Fe56 spline passes the smell tests (σ(2.445) = 2.25×10⁻⁴,
  Fe56/C12 = 4.24 vs Z-ratio 26/6 = 4.33 — itself corroborating the C12 base;
  verified over XRootD 2026-07-12), but its physics content is rescaled C12.
  Tensor files and SuSAv2 code verified identical between genie_dev and
  genie_inclxx (2026-07-15), so the caveat applies unchanged to the genie_inclxx
  full-EM iron campaign. **Open:** decide whether SuSAv2 stays in the iron model
  set as a labeled surrogate ("SuSAv2(C12→Fe56)") or is dropped for the Fe56
  comparison; if kept, the caveat must appear on every iron figure that includes
  it.

- **Benhar-table E-axis convention vs GENIE `BindHitNucleon` vs Dutta's estimator.**
  Three recoil conventions collide in the fig 9 comparison:

  1. **Dutta's measurement subtracts the recoil**: E_m ≡ ω − T_p′ − T_{A−1}
     (`papers/nucl-ex_0303011/longpaper2.tex:222`), T_{A−1} computed event-wise from
     the measured p_m (≤ 4.4 MeV for |p_m| < 300 MeV/c on ¹¹B). The published spectra
     are on the **mass-based axis**: E_m = S_p + E_x, ground state at
     S_p = 15.957 MeV, nothing below S_p in PWIA.
  2. **GENIE assumes the opposite of the tables**: the `BindHitNucleon` SpectralFunc
     special case (`QELUtils.cxx:271`, [v0 §10b1](../prd-analyzer-v0/README.md))
     asserts the table's E *includes* the recoil KE and removes it at the vertex.
     The assumption is defensible in principle — a translationally-invariant
     removal-energy definition E = E_{A−1}(−k) − E_A + m_N does contain T_rec — but
     the empirical tests say it mis-reads *these* tables: the 2024 ABS table's
     ground-state quasiparticle line reconstructs at 15.94 ≈ S_p on the ω − T_p axis
     ([v0 §10b2](../prd-analyzer-v0/README.md)), confirmed from the E_m-budget angle
     in [v0.1 study 3](sf2024_unifiedqel_em_prefsi.md) (line at 15.93–15.98 MeV) —
     a mass-based table *must* put its ground state at S_p, and it does.
  3. **Consequence on Dutta's axis**: applying the measurement's estimator to GENIE
     events lands the spectrum T_rec(k) low — **23.1 % (22b) / 39.9 % (33b) of the
     strength below S_p, and 0.08 % negative for 33b (min −15.3 MeV)**
     ([study 2](sf_unifiedqel_em_prefsi.md), [study 3](sf2024_unifiedqel_em_prefsi.md)).
     This distortion is part of GENIE's prediction on the data's axis — a model
     artifact, not an analysis bug.

  **Open:**
  (a) the old `pke12_tot` E-axis convention is strictly unproven — its 5-MeV blocks
  cannot resolve the ~1 MeV difference (block edge restores at 15.0 vs
  S_p = 15.957); needs Benhar-side documentation or author contact;
  (b) the candidate upstream GENIE issue (the `QELUtils.cxx:271` special case,
  flagged in v0 §10b2) is not yet filed/tracked;
  (c) v0.1 comparison rule until resolved: compare to **fig 9 with Dutta's estimator
  applied to GENIE events** (recoil subtracted, distortion included) and to the
  **input tables on the ω − T_p axis only** — never mix the two axes in one overlay
  without saying so.

- **INCL++ ground state (GEM26_44b) energy convention — local-energy binding, no
  removal energy, resampled momenta.** Phase-0 investigation for the INCL GS+FSI
  tune (plan: `.claude/plans/gem26_44b-incl-gs-fsi.md`); all claims verified by
  direct source read 2026-07-12 in the genie_inclxx install.

  1. **Off-shell convention**: INCL target nucleons are sampled on-shell
     internally (E = √(p²+m²), `G4INCLParticle.cc:112-114`), but the GHEP hit
     nucleon is written with **E = √(p²+m²) − v_loc(r,p)**
     (`INCLNucleus::getHitNucleonEnergy`, `NucleusGenINCL::BindHitNucleon`),
     where v_loc = √(p_l²+m²) − m is INCL's local-energy prescription
     (`G4INCLKinematicsUtils.cc:44`; p_l from the r–p-correlated density via the
     reflection-radius machinery). The binding lives entirely in this off-shell
     E; GENIE's per-nucleon `RemovalEnergy` plays no role
     (`NucleusGenINCL.cxx:263` sets 0; `BindHitNucleon` ignores `Eb` and
     `HitNucleonBindingMode`, `(void)Eb`, line 357).
  2. **The event momentum distribution is NOT the INCL correlated ground
     state.** Each accept/reject iteration discards the ground-state momentum
     and resamples **uniformly in a ball of the global Fermi momentum** at the
     fixed ground-state radius, accepting only KE > locE of the original
     nucleon (`INCLNucleus::ResamplingHitNucleon`;
     `QELEventGeneratorINCL.cxx:170` calls it per throw;
     `Random::sphereVector` = uniform ball, r_max·u^{1/3}). Only the vertex
     radius comes from the correlated ground state. The in-code
     `TODO: understand the effect of the re-sampling`
     (`QELEventGeneratorINCL.cxx:97-104`) acknowledges exactly this.
  3. **Vertex-level E_m prediction**: with exact 4-momentum conservation,
     T_p′ = ω + E_i − m_N, so E_m ≡ ω − T_p′ = v_loc(p_new) − T_i(p_new)
     (before recoil subtraction). There is **no S_p floor anywhere in this
     convention** — expect QE strength concentrated near and below zero on
     Dutta's axis, qualitatively unlike SF (shell peaks ≥ S_p). Sign/shape of
     the distribution depends on v_loc vs T_i for the resampled momenta and is
     to be measured in the pilot diagnostic (the Phase-0 empirical closure).
  4. **Remnant bookkeeping**: at the vertex the A−1 remnant takes
     p = −p_i and E = M_A − E_i exactly (`NucleusGenINCL.cxx:336-350`) —
     energy conserved, remnant off-shell; the generator *updates* this remnant
     rather than adding a second one. Post-FSI, `INCLCascadeIntranuke` cascades
     on the same `INCLNucleus` singleton and ABLA07 de-excites the remnant
     (excitation energy → ejectiles/γ).
  5. **Bug found**: `QELEventGeneratorINCL::fEb` (`.h:49`) is **never
     assigned** — the INCL `BindHitNucleon` intentionally doesn't fill it —
     yet the accept branch stores it into GHEP
     (`SetRemovalEnergy(fEb)`, `.cxx:286`), overwriting the 0 from
     `NucleusGenINCL`. The stored removal energy is an indeterminate
     (uninitialized) value. Analyses must not consume GHEP `RemovalEnergy`
     for INCL events (the gst-level ladder does not); candidate upstream fix:
     initialize `fEb = 0.` in the constructors.
  6. **Relation to the recoil-convention question above**: the INCL path
     bypasses `genie::utils::BindHitNucleon` entirely, so the `QELUtils.cxx:271`
     SpectralFunc special case never fires — it sidesteps the Benhar-table
     recoil issue and replaces it with the local-energy convention of items
     1–3. On Dutta's axis the role of E_removal is played by (v_loc − T_i).

  **Open:** (a) measure the pilot's vertex E_m distribution against item 3's
  prediction before scaling up (gate); (b) the fEb uninitialized-memory bug is
  not yet filed upstream; (c) whether the uniform-ball momentum resampling
  (item 2) is intended physics or an implementation shortcut needs an INCL
  author's input before the tune is used in publication figures.

  **Correction (2026-09-02):** see `docs/incl-ground-state-review.md`. Item 1
  is the interaction's `HitNucP4`, not the record: the GHEP hit nucleon is
  rewritten on-shell from INCL after the cascade (`E_m = −T`). Item 3 is
  superseded — measured `E_m(pre-FSI) = V₀ − T_ball`, `V₀ = 45.0 MeV`,
  floor `S = 6.83`, from INCL's energy balance at cascade insertion; the
  pre-FSI `|p_m|` is the local-energy-reduced momentum.

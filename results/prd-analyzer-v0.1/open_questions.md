# Open questions — prd-analyzer v0.1

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

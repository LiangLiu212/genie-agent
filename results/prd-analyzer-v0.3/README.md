# prd-analyzer v0.3 — Q² slice, exactly-one-proton selection

The [`../prd-analyzer-v0.2/`](../prd-analyzer-v0.2/) analysis with the
post-FSI proton selection changed from *leading proton* to **exactly one
final-state proton**:

    qel  &&  |Q²/1.28 − 1| ≤ 5 %  &&  N_p(final state) = 1

("the" proton is then unambiguous; neutrons and all other final-state
particles unconstrained). N_p = 1 applies where a post-FSI proton is
reconstructed (sections 3/3.1, 4, 5, 7); the record-based sections (1, 2, 6)
are independent of the proton choice and link to v0.1/v0.2. Samples: the
same full-EM t05 campaigns (Fe56 2026-07-16, C12 2026-07-26, 2M streamed
events/tune).

The notes:

- [`electron_fe56_scattering.md`](electron_fe56_scattering.md)
- [`electron_c12_scattering.md`](electron_c12_scattering.md)

Headline: **within the Dutta window the exactly-one-proton and
leading-proton selections nearly coincide.** The window sample has a large
≥2p population (≈ 26 % Fe / ≈ 16 % C12 of qel ∧ hit-p ∧ window events; 1p =
69–72 % / 79–81 %; 0p = the known 2–5 % proton loss), but ≥2p events almost
never pass the E_m/p_m window: in-window counts drop only ~0.3–1.8 % vs
v0.2, survivals shift by ≤ 0.008, and the signed-p_m asymmetries and ΔT_p
chain pattern are statistically unchanged. The selections differ visibly
only in the inclusive views (section 3: the low-T_p multi-proton hump
shrinks; 3.1: in-window fractions rise to 42–49 % Fe / 56–66 % C12).

Machinery: the v0.2 scripts with `--proton-sel 1p`
(`make_kin_qel_q2cut.py`, `make_emiss_ladder_q2cut.py`,
`make_pmiss_signed_q2cut.py`, `make_fsi_proton_choice.py`; outputs and
caches route here), an `n_p` column in the v0.1 `kin_qel` caches, and an
`np` column in the `dump_fsiproton.cxx` dumps.

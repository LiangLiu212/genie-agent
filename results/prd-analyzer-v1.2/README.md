[← Results home](../README.md)

# prd-analyzer v1.2 — Q² slice, N_p = 1, Dutta data on the count scale (22b only)

The [`../prd-analyzer-v0.3/`](../prd-analyzer-v0.3/README.md) C12 and Fe56
analyses repeated for the single tune **`GEM26_22b_05_000`** with the Dutta data
convention corrected (author, 2026-09-06): every data point is drawn at
**half its published value** — the E_m figures' `S(E_m)` (fig 9 C12,
fig 11 Fe56) count each |p_m| twice (signed −300…+300 integral;
Σ S dE / 2 = 3.04 / 9.10 protons, raw distorted strength ≈ T·Z/f_corr),
and the |p_m| files (fig 6, fig 7) carry the full density on each side, so
the positive half is drawn as tabulated (no L+R fold). Same samples (full-EM
t05 grid campaigns, C12 2026-07-26, Fe56 2026-07-16, 2M events each), same
selection

    qel  &&  hitnuc == p  &&  |Q²/1.28 − 1| ≤ 5 %  &&  N_p(final state) = 1

same occupancy normalization `Z·dN/dx/N_sel`, N_sel = qel ∧ hit p ∧ Q² slice
(53,517 C12, 50,727 Fe56 — the v0.3 counts; the scripts also offer
`--norm total-qe`, all generated QE events, not used here).

The notes:

- [`electron_c12_scattering.md`](electron_c12_scattering.md)
- [`electron_fe56_scattering.md`](electron_fe56_scattering.md)

Headline: with the data at the count scale the post-FSI stage, not the
pre-FSI one, sits at the data's absolute strength — C12: E_m stage 4 / data
= 1.068 ± 0.008 (stage 3: 1.82), |p_m| shells 1.140 ± 0.012 (1.96); Fe56:
1.077 ± 0.009 (2.63) and 1.090 ± 0.010 (2.65). Shapes are v0.3's: on carbon
|p_m| matches the data within the binning and E_m is broader than the data
above 39 MeV; on iron both variables disagree (MC E_m narrower and 4.9 MeV
lower in the mean, MC |p_m| 21 % low below 120 MeV/c).

Machinery: the v0.3 scripts with new switches — `--data-conv raw` and
`--norm {windowed,total-qe}` on `make_emiss_ladder_q2cut.py` /
`make_pmiss_ladder_q2cut.py` (`--norm`, `--out-dir` on
`make_pmiss_signed_q2cut.py`; `--out-dir` / `--tunes` on the others),
`qe_norm.py` for the total-QE count, and `make_eep_readouts.py`, which
writes a histdiag text readout `<stem>.txt` next to every histogram PNG.
Caches are the v0.1 / v0.2 / v0.3 ones (gitignored); nothing was streamed.

[← Results home](../README.md)

# prd-analyzer v1.2 — Q² slice, N_p = 1, Dutta data on the count scale (22b only)

The [`../prd-analyzer-v0.3/`](../prd-analyzer-v0.3/README.md) C12 analysis
repeated for the single tune **`GEM26_22b_05_000`** with the Dutta data
convention corrected (author, 2026-09-06): every data point is drawn at
**half its published value** — fig 9's `S(E_m)` counts each |p_m| twice
(signed −300…+300 integral; Σ S dE / 2 = 3.04 protons, raw distorted
strength ≈ T·Z/f_corr), and the fig 6 |p_m| files carry the full density on
each side, so the positive half is drawn as tabulated (no L+R fold). Same
sample (C12 full-EM t05 grid campaign 2026-07-26, 2M events), same selection

    qel  &&  hitnuc == p  &&  |Q²/1.28 − 1| ≤ 5 %  &&  N_p(final state) = 1

same occupancy normalization `Z·dN/dx/N_sel`, N_sel = qel ∧ hit p ∧ Q² slice
= 53,517 (the v0.3 count; the scripts also offer `--norm total-qe`, all
277,035 generated QE events, not used here).

The note:

- [`electron_c12_scattering.md`](electron_c12_scattering.md)

Headline: with the data at the count scale the post-FSI stage, not the
pre-FSI one, sits at the data's absolute strength — E_m stage 4 / data =
1.068 ± 0.008 (stage 3: 1.82), |p_m| shells 1.140 ± 0.012 (1.96). Shapes are
v0.3's: |p_m| matches the data within the binning, E_m peaks on the
p-shell bin but is broader with +17 % above 39 MeV.

Machinery: the v0.3 scripts with new switches — `--data-conv raw` and
`--norm {windowed,total-qe}` on `make_emiss_ladder_q2cut.py` /
`make_pmiss_ladder_q2cut.py` (`--norm`, `--out-dir` on
`make_pmiss_signed_q2cut.py`; `--out-dir` / `--tunes` on the others),
`qe_norm.py` for the total-QE count, and `make_eep_readouts.py`, which
writes a histdiag text readout `<stem>.txt` next to every histogram PNG.
Caches are the v0.1 / v0.2 / v0.3 ones (gitignored); nothing was streamed.

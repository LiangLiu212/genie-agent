# p_F / S_p scan of the real GENIE-INCL chain (e- C12 2.445 GeV, EMQE)

The scan of the two INCL ground-state knobs that the numpy toy `incl-potential-test/`
identified (T_F through the constant Fermi momentum p_F, and the proton separation energy
S_p), now run with real GENIE-INCL events: five sub-tunes of the GEM26_44b family
(`genie-agent/tunes/GEM26_44b/README.md`, section "p_F / S_p scan sub-tunes"), 200k events
each (4 x 50k chunks, 2026-09-12), INCL's `real` separation-energy scheme (S = S_p
everywhere, V0 = T_F + S_p, S_n = 18.72 MeV), local energy on, own spline per p_F.
Baseline: the 2026-09-04 `locframe-on` sample (S = 6.83 INCL, V0 = 45.0).

| tune | variant | p_F [MeV/c] | T_F | S_p | V0_p [MeV] |
|---|---|---|---|---|---|
| GEM26_44b_05_000_lfon | baseline S = 6.83 (INCL) | 270.34 | 38.17 | 6.83 | 45.00 |
| GEM26_44b_11_000 | pF239 realS | 239.16 | 30.00 | 15.957 | 45.96 |
| GEM26_44b_12_000 | pF270 realS (centre) | 270.34 | 38.17 | 15.957 | 54.13 |
| GEM26_44b_13_000 | pF297 realS | 297.38 | 46.00 | 15.957 | 61.96 |
| GEM26_44b_14_000 | Sp10 | 270.34 | 38.17 | 10.00 | 48.17 |
| GEM26_44b_15_000 | Sp22 | 270.34 | 38.17 | 22.00 | 60.17 |

## Files

| file | what |
|---|---|
| `incl_scan_TF_c12.png` | E_m and \|p_m\| (pre-FSI primary proton, post-FSI single proton) for the T_F scan against the baseline and the Dutta data (`make_incl_onoff_overlay.py`) |
| `incl_scan_Sp_c12.png` | the same for the S_p scan |
| `scan_readout.txt` | `results/template/make_incl_scan_readout.py`: per tune and stage the mean and quantiles of E_m and \|p_m\| next to INCL's expected windows, and histdiag comparisons of every variant against the centre tune |

Caches: `results/prd-analyzer-v1.0/cache/ladder_c12/GEM26_44b_1N_000.npz` (gitignored; rebuild with
`make_emiss_ladder_q2cut.py --target C12 --tune <id> --no-q2cut --proton-sel 1p --build-only`).
Runs: `genie-agent/genie-runs/GEM26_44b_1N_000-2026-09-12/` (splines labelled `pF239-realS` ...,
chunks `<variant>-200k`, seeds 2026PP0c; ~4 GB per tune, mostly stdout).

## Results (1p selection, no Q^2 window; E_m = omega - T_p' with the recoil term restored)

Record hit nucleon (stage 2) and pre-FSI proton (stage 3) are identical in E_m, as the fork's
convention says (record = global nucleon, E_ball - V0). Quantiles from `scan_readout.txt`:

| tune | E_m stage 2/3: q1 (floor) / median / q99 | mean | toy E_miss mean | \|p_ball\| mean / max | post-FSI E_m q1 / median |
|---|---|---|---|---|---|
| baseline S=6.83 | 6.93 / 15.46 / 39.67 | 17.44 | 17.46 (V0 - T_ball) | 225.7 / 270.3 | 16.01 / 26.14 |
| pF239 realS | 16.04 / 22.80 / 41.63 | 24.31 | 24.33 | 199.7 / 239.2 | 16.01 / 24.13 |
| pF270 realS (centre) | 16.06 / 24.57 / 48.68 | 26.53 | 26.58 | 225.9 / 270.3 | 16.01 / 26.21 |
| pF297 realS | 16.08 / 26.32 / 55.30 | 28.68 | 28.73 | 248.4 / 297.4 | 16.01 / 28.16 |
| Sp10 | 10.10 / 18.58 / 42.77 | 20.55 | 20.62 | 226.0 / 270.3 | 10.06 / 20.18 |
| Sp22 | 22.10 / 30.61 / 54.74 | 32.59 | 32.62 | 225.8 / 270.3 | 22.05 / 32.47 |

- **Floors and edges are where INCL puts them**: the record's E_m starts at S_p (floor q1 within
  0.1 MeV of S_p for every tune) and ends at V0_p (q99 within 7 MeV of V0, the ball being
  truncated at p_min(r)); `|p_ball|` max = p_F to 0.1 MeV/c. The means agree with the toy's
  E_miss(free) = T_F + S_p - T_ball to better than 0.1 MeV.
- **The post-FSI floor is the real S_p in every setting**, including the baseline with INCL's
  S = 6.83: the surface exit pays the mass-table separation energy (`formulas.md` section 5 of
  the toy). Post-FSI medians: 26.1 (baseline) vs 26.2 (centre) - the well depth barely moves
  the observable proton.
- **S_p acts as a rigid shift** (histdiag on the centre tune as reference): Sp10 -5.99 MeV
  (stage 3) / -5.90 (stage 4), Sp22 +6.05 / +5.91, widths unchanged (std ratios 1.00, 1.04,
  1.00, 0.98). Toy: -5.96 / +6.05.
- **T_F stretches E_m and scales |p_m|**: pF239 mean -2.22 MeV, std ratio 0.79 (toy -2.25,
  0.788); pF297 +2.15, 1.20 (toy +2.14, 1.203). Pre-FSI |p_m| quantiles scale by 0.882 (pF239)
  and 1.098 (pF297) (toy 0.889 / 1.096); post-FSI 0.889 / 1.092.
- **Baseline vs centre** (S = 6.83 INCL vs real 15.96 at the same p_F): stage-3 E_m shifts
  rigidly by -9.1 MeV (= 15.957 - 6.83), the post-FSI E_m by only -1.3 to -2.1 MeV at the
  quantiles - the difference the well depth makes to the cascade.
- Selection fractions: qel && hit p 69.7-70.7 %; post-FSI single-proton survival 67.8 (pF239),
  65.8 (centre), 64.1 (pF297), 68.1 (Sp10), 62.8 % (Sp22) - deeper wells lose more protons.

## Verification done

- NOTICE line `INCL ground state: p_F = ..., T_F = ..., separation energies = ..., data dir = ...`
  in every run's stdout matches the sub-tune (20-event smoke runs for all six tunes first).
- Splines with the 09-04 seed 648585686: `_12`, `_14`, `_15` reproduce the 09-04 `locframe-on`
  spline knot by knot (`genie-agent/scripts/spline_knot_diff.py`, max relative difference 0):
  the QE cross section does not depend on S; `_11` / `_13` differ (up to 17 % / threshold knot).
- All 20 chunks returncode 0, 1690-1770 s each (20 concurrent); every chunk loaded its own
  tune's spline (two spline messages, no fallback).
- dump_hitnuc on the smoke runs: RemovalEnergy = V0 - T_ball inside [S_p, V0_p], |p| <= p_F.

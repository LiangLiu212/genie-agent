# Scan of the INCL Fermi energy and proton separation energy in GENIE-INCL (e- C12, 2.445 GeV)

2026-09-12/13. Companion to the numpy toy `incl-potential-test/` (its `formulas.md` gives the
closed forms) and to the results directory `results/incl-pf-sp-scan/` (figures, readout).
Code: GENIE fork branch `feature/pF_Sp_scan` (LiangLiu212/Generator @ 71b1675fa) and INCL
branch `feature/pF_Sp_scan` (LiangLiu212/inclxx @ 2d13c0a); tunes and tooling in this repo
(commit fd78a44).

## Summary

- Two INCL ground-state parameters were scanned in the real GENIE-INCL chain: the Fermi
  kinetic energy T_F (through the constant Fermi momentum p_F, which sets the well depth
  V0 = T_F + S, the Fermi ball, the r-p floor and the local energy) and the proton
  separation energy S_p (INCL's real-mass-table scheme, so S = S_p everywhere).
- Every observable landed where INCL's bookkeeping says: the record and pre-FSI missing
  energy E_m = omega - T_p' starts at S_p and ends at V0_p, the struck momentum tops out at
  p_F, and the mean E_m agrees with the toy's T_F + S_p - T_ball to 0.1 MeV in all five variants.
- S_p is a rigid shift of E_m (-5.99 / +6.05 MeV pre-FSI, -5.90 / +5.91 MeV post-FSI for
  10 / 22 MeV against 15.96) with unchanged width. T_F stretches E_m (std ratio 0.79 / 1.20 for
  T_F = 30 / 46 MeV) and scales |p_m| by 0.88 / 1.10.
- The post-FSI floor is the real S_p = 15.96 MeV in every setting, including the current
  tune with INCL's constant S = 6.83: the surface exit always pays the mass-table separation
  energy. The well depth alone moves the post-FSI median by 0.1 MeV (23.4 vs 23.4).
- The QE cross section does not depend on S: the three splines at p_F = 270.34 MeV/c are
  identical knot by knot to the 2026-09-04 nominal spline; only p_F changes the spline.

## 1. What was scanned

| tune | variant | p_F [MeV/c] | T_F [MeV] | S_p / S_n [MeV] | V0_p / V0_n [MeV] | spline |
|---|---|---|---|---|---|---|
| GEM26_44b_05_000 (`locframe-on` sample of 2026-09-04) | baseline, INCL S = 6.83 | 270.34 | 38.17 | 6.83 / 6.83 | 45.00 / 45.00 | 9f4 (09-04) |
| GEM26_44b_11_000 | pF239 | 239.16 | 30.00 | 15.957 / 18.72 | 45.96 / 48.72 | own |
| GEM26_44b_12_000 | pF270, centre | 270.34 | 38.17 | 15.957 / 18.72 | 54.13 / 56.89 | own (= 9f4) |
| GEM26_44b_13_000 | pF297 | 297.38 | 46.00 | 15.957 / 18.72 | 61.96 / 64.72 | own |
| GEM26_44b_14_000 | Sp10 | 270.34 | 38.17 | 10.00 / 18.72 | 48.17 / 56.89 | own (= 9f4) |
| GEM26_44b_15_000 | Sp22 | 270.34 | 38.17 | 22.00 / 18.72 | 60.17 / 56.89 | own (= 9f4) |

The five variants form a cross through the centre point (p_F = 270.34, real S_p = 15.957).
S_n stays at its real value (18.72 MeV), so with the real scheme the neutron well is deeper
than in the baseline; all analyses select proton knock-out (`qel && hitnuc == 2212`).
Local energy on (`first-collision`), EMQE only, 200k events per variant.

## 2. How the knobs reach INCL

- **p_F**: new `NucleusGenINCL` parameter `inclxx-fermi-momentum` [MeV/c] ->
  `G4INCL::Config::setFermiMomentum` (an existing INCL setter); a value <= 0 keeps INCL's
  constant 1.37 hbar c = 270.34 MeV/c.
- **S_p**: new parameter `inclxx-separation-energies` = `INCL | real | real-light` ->
  `G4INCL::Config::setSeparationEnergyType`, a one-line inline setter added to INCL's
  `G4INCLConfig.hh` (upstream has only the getter). With `real`, INCL takes
  S_p = m_p + M(B11) - M(C12) from `walletlifetime.dat` in the INCL data directory, uses it in
  V0 = T_F + S_p and in the emission Q-value (which is then zero). The value is therefore set
  by the B11 mass-excess row of a per-variant copy of the data directory
  (`genie-agent/scripts/make_incl_data_variant.py`): S_p = 7.288968 + excess(B11), i.e.
  `11 5 8.6679` (15.957, untouched), `11 5 2.7110` (10.0, `data-Sp10`), `11 5 14.7110`
  (22.0, `data-Sp22`).
- Both are forwarded in `INCLNucleus::configure()` after `Config::init()` and before
  `ParticleTable::initialize`; a NOTICE line prints p_F, T_F, the scheme and the data directory.
- Each variant is a two-file sub-tune under `genie-agent/tunes/GEM26_44b/GEM26_44b_1N_000/`
  (`CommonParam.xml` with the Dutta Q2 cut, and a complete tune-local `NucleusGenINCL.xml`
  whose `Default` set carries the three parameters), selected by `--tune GEM26_44b_1N_000
  --gxmlpath genie-agent/tunes`.
- Splines: `gmkspl -n 30 -e 3.0`, seed 648585686 (the 09-04 seed), 7600-8300 s each when
  the five run concurrently. Events: 4 x 50k chunks per variant, 1690-1770 s each, 20 in
  parallel; gst via `gntpc`.

## 3. What the toy predicted

The toy (`incl-potential-test/ep_incl_scatter.py`, two-body phase space on INCL's local-frame
nucleon, INCL energy balance, INCL surface exit) gives closed forms:

```
record / pre-FSI:  E_m = V0 - T_ball - V(T_p')  = T_F + S_p - T_ball   (V(T_p') = 0 above ~195 MeV)
free proton:       E_m = omega - T_out          = T_F + S_p(real) - T_ball   in [S_p, T_F + S_p]
|p_m|              ~ p_red = the local-frame momentum, scaling with p_F
```

`incl-potential-test/ep_incl_scan.py` (figure `figures/ep_incl_C12_lfon_resample_scan.png`)
turned these into expected distributions with the same scan values: means 24.3 / 26.6 / 28.7 MeV
for T_F = 30 / 38.2 / 46 and 20.6 / 26.6 / 32.6 MeV for S_p = 10 / 16 / 22; S_p a rigid
+-6 MeV shift, T_F a stretch (std ratio 0.79 / 1.20) and a |p_m| scale (0.89 / 1.10).

## 4. Results

Selection as in the v1.0 ladders: `qel && hitnuc == p`, single final-state proton for the
post-FSI stage, no Q2 window; E_m = omega - T_p' with the recoil term restored.
Stage 2 (record hit nucleon) and stage 3 (pre-FSI proton) are identical in E_m, as the fork's
convention requires (record = global nucleon with E_ball - V0).

### 4.1 Record and pre-FSI proton

| variant | E_m q1 (floor) | median | q99 (edge) | mean | toy mean | \|p_ball\| mean / max [MeV/c] | \|p_p' - q\| mean, toy |
|---|---|---|---|---|---|---|---|
| baseline S=6.83 | 6.93 | 15.46 | 39.67 | 17.44 | 17.46 | 225.7 / 270.3 | 149.1, 149.3 |
| pF239 | 16.04 | 22.80 | 41.63 | 24.31 | 24.33 | 199.7 / 239.2 | 133.1, 132.5 |
| pF270 (centre) | 16.06 | 24.57 | 48.68 | 26.53 | 26.58 | 225.9 / 270.3 | 150.9, 149.3 |
| pF297 | 16.08 | 26.32 | 55.30 | 28.68 | 28.73 | 248.4 / 297.4 | 165.4, 163.8 |
| Sp10 | 10.10 | 18.58 | 42.77 | 20.55 | 20.62 | 226.0 / 270.3 | 149.7, 148.3 |
| Sp22 | 22.10 | 30.61 | 54.74 | 32.59 | 32.62 | 225.8 / 270.3 | 150.9, 150.6 |

Floors sit at S_p (within 0.15 MeV), edges at V0_p minus the truncation of the ball by the
floor p_min(r), the maximum struck momentum equals p_F, and the means match the toy to
better than 0.1 MeV. The mean of |p_p' - q| (the local-frame momentum plus INCL's rescaling)
matches the toy to 1-2 MeV/c.

### 4.2 Post-FSI single proton (p_m < 300 MeV/c)

| variant | E_m q5 (floor) | median | q95 | fraction in [10,25) / [30,50) MeV | 1p survival | median \|p_m\| [MeV/c] |
|---|---|---|---|---|---|---|
| baseline S=6.83 | 16.38 | 23.39 | 43.03 | 56.8 / 24.6 % | 65.2 % | 162.3 |
| pF239 | 16.31 | 21.95 | 37.69 | 64.8 / 16.6 % | 67.8 % | 144.2 |
| pF270 (centre) | 16.39 | 23.44 | 43.14 | 56.6 / 24.7 % | 65.8 % | 163.0 |
| pF297 | 16.49 | 24.89 | 48.34 | 50.3 / 29.2 % | 64.1 % | 178.7 |
| Sp10 | 10.43 | 17.50 | 37.31 | 75.4 / 12.5 % | 68.1 % | 161.1 |
| Sp22 | 22.42 | 29.36 | 49.36 | 25.8 / 42.6 % | 62.8 % | 164.6 |

(Pre-FSI window fractions [10,25) / [30,50): baseline 57.6 / 10.2, pF239 60.8 / 20.4, centre
51.8 / 30.0, pF297 44.4 / 34.8, Sp10 72.3 / 15.6, Sp22 21.6 / 48.5 %.)

- The post-FSI floor is 16.0 MeV for the baseline, pF239, pF270 and pF297 alike, 10.1 for Sp10
  and 22.1 for Sp22: the free proton's E_m starts at the real S_p whatever the well depth,
  because INCL's transmission channel pays the mass-table separation energy at the surface.
- S_p moves the whole post-FSI spectrum rigidly and swaps the Dutta windows: the p-shell
  window [10,25) holds 75 % of the protons at S_p = 10 and 26 % at S_p = 22.
- T_F changes the shape: the upper edge and the [30,50) window grow with T_F, the median moves
  by -1.5 / +1.5 MeV, and |p_m| scales with p_F (medians 144 / 163 / 179 MeV/c).
- Deeper wells lose more protons to FSI (1p survival 68 % -> 63 % from Sp10 to Sp22, 68 % -> 64 %
  from pF239 to pF297).

### 4.3 Histdiag verdicts against the centre tune (`results/incl-pf-sp-scan/scan_readout.txt`)

| variant | E_m pre-FSI | E_m post-FSI | \|p_m\| pre-FSI | \|p_m\| post-FSI |
|---|---|---|---|---|
| Sp10 | rigid shift -5.99 MeV, std ratio 1.000 | rigid shift -5.90, std ratio 1.039 | - | - |
| Sp22 | rigid shift +6.05, std ratio 1.002 | rigid shift +5.91, std ratio 0.975 | - | - |
| pF239 | mean -2.22 MeV, narrower (std ratio 0.786) | mean -1.84, std ratio 0.908 | scale x0.882 | scale x0.889 |
| pF297 | mean +2.15, broader (std ratio 1.202) | mean +1.76, std ratio 1.104 | scale x1.098 | scale x1.092 |
| baseline S=6.83 | rigid shift -9.1 MeV (= 6.83 - 15.957) | mean -1.75; quantiles -1.5 / -1.3 / -2.1 | - | - |

The toy's readout for the same scan: Sp10 / Sp22 rigid -5.96 / +6.05; pF239 mean -2.25,
std ratio 0.788, |p_m| x0.889; pF297 +2.14, 1.203, x1.096.

### 4.4 Cross section

Run with the 2026-09-04 seed, the splines of the centre, Sp10 and Sp22 tunes reproduce the
09-04 `locframe-on` spline knot by knot (maximum relative difference 0 over 2 x 30 knots,
`genie-agent/scripts/spline_knot_diff.py`): the separation energy, and hence the well depth,
does not enter the QE cross section (the integrand sees the on-shell local-frame nucleon).
The pF239 and pF297 splines differ from nominal by up to 14-17 % (pF239) and at the
threshold knot (pF297).

## 5. Figures

- `figures/incl_scan_TF_c12.png`: T_F scan against the baseline and the Dutta data, E_m and
  |p_m| pre- and post-FSI (`results/template/make_incl_onoff_overlay.py`).
- `figures/incl_scan_Sp_c12.png`: the same for the S_p scan.
- `figures/ep_incl_C12_lfon_resample_scan.png`: the toy's prediction for both scans.

## 6. Verification performed

1. Six 20-event smoke runs (baseline + five sub-tunes): the NOTICE line shows the intended
   p_F / T_F / scheme / data directory; `dump_hitnuc` gives RemovalEnergy = V0 - T_ball inside
   [S_p, V0_p] and |p| <= p_F for every tune.
2. Every production chunk loaded its own tune's spline (two spline messages, no fallback to
   on-the-fly integration); all 20 chunks returned 0.
3. Spline equality (section 4.4) and the closed-form agreement (sections 4.1-4.3).

## 7. Caveats and possible next steps

- The real scheme also deepens the neutron well (S_n = 18.72 MeV, V0_n = T_F + 18.72); the
  scan isolates S_p by editing only the B11 row, so neutron knock-out and the neutron cascade
  differ from the baseline. A neutron-only S_n scan would edit the C11 row.
- The toy is flat phase space; the real chain carries the QE cross section, so the agreement
  is in the bookkeeping quantities (floors, edges, shifts, scales), not in absolute spectra.
- Editing the B11 mass also changes the remnant mass INCL uses for the residual nucleus
  (excitation energy fed to de-excitation) - irrelevant for the leading proton, but not for
  evaporation products.
- Run output is ~4 GB per tune, almost all GENIE stdout (1 GB per 50k chunk); the ghep and gst
  files are 75 MB per chunk.

## 8. Files and reproduction

```
# knobs and tunes
genie-agent/tunes/GEM26_44b/README.md                      section "p_F / S_p scan sub-tunes"
genie-agent/scripts/make_incl_data_variant.py --name Sp10 --sp 10.0
genie-agent/scripts/spline_knot_diff.py a.xml b.xml
# splines and events (per PP = 11..15)
pixi run python genie-agent/scripts/run_gmkspl.py --probes eminus --targets C12 --tune GEM26_44b_PP_000 \
    --genlist EMQE -n 30 -e 3.0 --gxmlpath genie-agent/tunes --installation genie_inclxx --seed 648585686 --label <variant>
pixi run python genie-agent/scripts/run_gevgen.py --probe eminus --target C12 -n 50000 -e 2.445 \
    --cross-sections <spline> --tune GEM26_44b_PP_000 --genlist EMQE --gxmlpath genie-agent/tunes \
    --installation genie_inclxx --seed 2026PP0c --label <variant>-200k        # c = 1..4, then run_gntpc.py -f gst
# analysis
pixi run python results/template/make_emiss_ladder_q2cut.py --target C12 --tune GEM26_44b_PP_000 --no-q2cut --proton-sel 1p --build-only
pixi run python results/template/make_incl_onoff_overlay.py --tunes ... --labels ... --out-dir results/incl-pf-sp-scan --stem ... --title "..."
pixi run python results/template/make_incl_scan_readout.py
```
Runs: `genie-agent/genie-runs/GEM26_44b_1N_000-2026-09-12/` (splines labelled `pF239-realS`,
`pF270-realS`, `pF297-realS`, `Sp10-pF270`, `Sp22-pF270`; chunks `<variant>-200k`).

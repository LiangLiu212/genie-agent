# Electron–Fe56 scattering — Q² slice, exactly-one-proton selection (v0.3)

v0.3 instance of
[`../prd-analyzer-v0.2/electron_fe56_scattering.md`](../prd-analyzer-v0.2/electron_fe56_scattering.md):
identical samples and constructions, with the post-FSI proton selection
changed from *leading proton* to **exactly one final-state proton**
(N_p = 1; "the" proton is then unambiguous and coincides with the leading
one). Neutrons and all other final-state particles are unconstrained. The
N_p = 1 requirement applies where a post-FSI proton is reconstructed
(sections 3/3.1, 4, 5, 7); the record-based sections are untouched by the
proton choice and link below. Sample: Fe56 full-EM t05 grid campaign
2026-07-16, 2M events/tune.

**Headline: within the Dutta window, N_p = 1 and leading-proton are nearly
the same analysis.** The window sample carries a large ≥2p population
(≈ 26 % of qel ∧ hit-p ∧ window events), but those events almost never pass
the E_m/p_m window — the in-window counts drop only ~0.7–1.8 % vs v0.2, and
every in-window observable shifts by ≲ 2 %. The selections differ materially
only in the inclusive (unwindowed) views of section 3.

## 1. Fe56 2D spectral function — the GENIE input table

Cut- and selection-independent — see
[v0.1 section 1](../prd-analyzer-v0.1/electron_fe56_scattering.md#1-fe56-2d-spectral-function--the-genie-input-table).

## 2. Struck nucleon in the record

Record-level (pre-FSI) — independent of the FS-proton choice; see
[v0.2 section 2](../prd-analyzer-v0.2/electron_fe56_scattering.md#2-struck-nucleon-in-the-record-sampled-p_miss-e_rm-and-p_miss-r).

## 3. QEL kinematics in the slice — E_e′, θ_e′, T_p, θ_p, Q²

![Fe56 QEL kinematics, Q² window && N_p=1, events/bin](kin_qel_q2cut_fe56_counts.png)

As v0.2 section 3 with the T_p/θ_p panels restricted to N_p = 1 events
(electron-arm panels unchanged; **events/bin above**, equal ntot = 2M/tune;
area-normalized shape companion `kin_qel_q2cut_fe56.png`). Multiplicity split of the qel ∧ window
sample (both hit-nucleon species):

| tune | 0p | 1p | ≥2p |
|---|---|---|---|
| GEM26_11a_05_000 | 19.2 % | 57.1 % | 23.7 % |
| GEM26_22a_05_000 | 20.6 % | 56.0 % | 23.3 % |
| GEM26_22b_05_000 | 17.2 % | 58.9 % | 23.9 % |
| GEM21_11a_05_000 | 17.8 % | 58.6 % | 23.6 % |

The visible v0.3 effect lives here: the ≥2p events populate the low-T_p
region, so requiring N_p = 1 removes much of the FSI-rescattered hump — the
two T_p peaks are now comparable on iron (the QE bump wins for 11a), where
the leading-proton selection of v0.2 had the low-T_p population clearly
dominant.

### 3.1 E_m and p_m in the slice — no E_m/p_m cuts

![Fe56 E_m/p_m in the slice, N_p=1](empm_q2cut_fe56.png)

![Fe56 E_m/p_m in the slice, N_p=1, linear y](empm_q2cut_fe56_lin.png)

As v0.2 subsection 3.1 with N_p = 1 (log-y above for the tails, linear-y
below for the true proportions; raw-counts companion
`empm_q2cut_fe56_counts.png`). The uncorrelated-proton p_m bump at
≈ |q| shrinks relative to v0.2 (much of it was multi-proton), raising the
in-window fractions to 49 / 42 / 45 / 45 % (11a/22a/22b/GEM21) from v0.2's
35 / 30 / 32 / 33 %.

Regenerate (this and 3.1):
`pixi run python results/template/make_kin_qel_q2cut.py --target Fe56 --proton-sel 1p`.

## 4. Missing energy: table vs simulation vs Dutta Fig. 11

Same windowed restored ladder as v0.2 section 4, stage 4 = the unique
proton of N_p = 1 events (stages 1–3 unchanged by construction):

![Fe56 v0.3 ladder, GEM26_11a](em_ladder_restored_fe56_GEM26_11a_05_000.png)
![Fe56 v0.3 ladder, GEM26_22a](em_ladder_restored_fe56_GEM26_22a_05_000.png)
![Fe56 v0.3 ladder, GEM26_22b](em_ladder_restored_fe56_GEM26_22b_05_000.png)
![Fe56 v0.3 ladder, GEM21_11a](em_ladder_restored_fe56_GEM21_11a_05_000.png)

| tune | N_sel | 1p fraction | I2r = I3r | I4r | I4r/I3r (v0.2) | 1p in-window (v0.2) |
|---|---|---|---|---|---|---|
| GEM26_11a_05_000 | 68,047 | 69.8 % | 26.000 | 10.546 | 0.406 (0.408) | 27,601 (27,785) |
| GEM26_22a_05_000 | 68,724 | 68.8 % | 23.340 | 8.942 | 0.383 (0.386) | 23,635 (23,816) |
| GEM26_22b_05_000 | 50,727 | 71.6 % | 23.952 | 9.799 | 0.409 (0.415) | 19,118 (19,390) |
| GEM21_11a_05_000 | 63,245 | 71.6 % | 24.203 | 10.053 | 0.415 (0.423) | 24,453 (24,899) |

I2r = I3r exact and record medians identical to v0.2 (stages 2–3
untouched); the in-window survival drops by only 0.003–0.008 despite the 1p
fraction being ~70 % — **the ≥2p events the new selection removes were
already almost entirely outside the window**. Post-FSI shape figures
(`em_postfsi_shape_fe56_*.png`, produced by the same run) are statistically
identical to v0.2's: the ΔT_p structure is a per-chain property, not a
multiplicity one.

Regenerate: `pixi run python results/template/make_emiss_ladder_q2cut.py --target Fe56 --all-tunes --proton-sel 1p`
(cache: `cache/ladder_fe56/` here).

### 4.1 Missing momentum: table vs record vs pre/post-FSI proton

The |p_m| projection of the same four-stage ladder
([`make_pmiss_ladder_q2cut.py`](../template/make_pmiss_ladder_q2cut.py),
reading the section-4 caches): each stage histogrammed in |p_m| (native
20 MeV/c bins, occupancy scale) with the E_m window applied instead —
`E_m + T_rec < 80 MeV` — and the folded Dutta fig 7 data overlaid on every
panel (L+R summed = the full |p_m| density on the published scale,
2×fig 7 ≡ fig 11 to 0.03 %; weighted 4πp_m² onto the occupancy axis).

![Fe56 v0.3 pm ladder, GEM26_11a](pm_ladder_fe56_GEM26_11a_05_000.png)
![Fe56 v0.3 pm ladder, GEM26_22a](pm_ladder_fe56_GEM26_22a_05_000.png)
![Fe56 v0.3 pm ladder, GEM26_22b](pm_ladder_fe56_GEM26_22b_05_000.png)
![Fe56 v0.3 pm ladder, GEM21_11a](pm_ladder_fe56_GEM21_11a_05_000.png)

Windowed strengths, |p_m| < 320 MeV/c (the data grid — slightly wider than
section 4's p_m < 300, so I2/I3 sit a little above I2r/I3r):
I1(table) = 22.852, I(data) = 18.206, **data/table = 0.80** — the folded
fig 7/11 ratio of the [normalization page](../../results/normalization/README.md).

| tune | I2 (record) | I3 (pre-FSI) | I4 (post-FSI) | I4/I3 | §4 I4r/I3r |
|---|---|---|---|---|---|
| GEM26_11a_05_000 | 26.000 | 26.000 | 10.600 | 0.408 | 0.406 |
| GEM26_22a_05_000 | 23.642 | 23.642 | 9.084 | 0.384 | 0.383 |
| GEM26_22b_05_000 | 24.163 | 24.163 | 9.925 | 0.411 | 0.409 |
| GEM21_11a_05_000 | 0 (record E < 0) | 24.543 | 10.216 | 0.416 | 0.415 |

- **I4/I3 reproduces the section-4 survivals to ≤ 0.002**: the two
  projections window the same events, and on iron the 0–80 MeV window is
  wide enough that the FSI energy loss does not carry survivors out of it.
- The E_m window on stage 2 only bites where the record keeps the sampled
  removal energy (22b: I2 = 24.16, genuinely windowed): for 11a/22a the
  record E is a δ at S_p inside the window, so I2 = the full k-marginal
  (dotted ≈ solid); for GEM21 the record E is negative and the window
  empties the stage (dotted = unwindowed reference).
- Shape: the pre-FSI stages track the input table bin by bin; the data are
  visibly *flatter* than both (the mid-|p_m| deficit of the folded
  normalization comparison). FSI suppresses ≈ 0.6 of the strength roughly
  shape-preservingly, with a slight shift of the surviving peak to higher
  |p_m|.

Regenerate: `pixi run python results/template/make_pmiss_ladder_q2cut.py --target Fe56 --all-tunes --proton-sel 1p`.

### 4.2 The same ladder in Dutta's units — ∫_win P dE_m [MeV⁻³]

The section-4.1 stages converted to the Dutta files' native units: the
**3D density** `∫_win P dE_m` [MeV⁻³] instead of the 1D occupancy density
— the MC histograms divided by 4πp_c² (bin centers), the table drawn as
`Z·Σ P·ΔE` directly, and the fig 7 folded data **exactly as tabulated**
(no weighting applied to the data at all). Log y, so the low-|p_m| region
is not suppressed by the p² phase-space factor; both figure sets carry the
same information, only the axis convention differs.

![Fe56 v0.3 pm ladder (density), GEM26_11a](pm_ladder_dens_fe56_GEM26_11a_05_000.png)
![Fe56 v0.3 pm ladder (density), GEM26_22a](pm_ladder_dens_fe56_GEM26_22a_05_000.png)
![Fe56 v0.3 pm ladder (density), GEM26_22b](pm_ladder_dens_fe56_GEM26_22b_05_000.png)
![Fe56 v0.3 pm ladder (density), GEM21_11a](pm_ladder_dens_fe56_GEM21_11a_05_000.png)

- What the occupancy view compresses is now explicit: the density falls
  ~2 decades over 0–320 MeV/c, and the 0.80 data deficit is **not
  uniform** — the data sit on the table at low |p_m| (≲ 120 MeV/c) and
  rejoin it in the outermost bins, with the missing strength concentrated
  in the 150–260 MeV/c falloff (the "flatter measured distribution" of
  the folded normalization comparison).
- Stage 4 in this view shows *where* FSI removes strength: the depletion
  is strongest below ~150 MeV/c, flattening the surviving distribution —
  qualitatively the same direction as the data-vs-table difference, but
  the renormalized data are not the raw distorted yield, so this is a
  shape observation only.

(Same run as 4.1 — the script writes both figure sets.)

### 4.3 Post-FSI E_m and |p_m| shapes, normalized to the survivors

Both post-FSI projections per tune
([`make_postfsi_empm_shape.py`](../template/make_postfsi_empm_shape.py)),
normalized by the **surviving in-window post-FSI count** instead of the
true-QEL selection count N_sel: every curve has unit integral over its
window, dividing out the ~Z × survival occupancy scale so only shapes
compare. Left: `E_m + T_rec` in [0, 80), p_m < 300 (the section-4
construction) vs unit-normalized fig 11; right: |p_m| in [0, 320) with the
E_m < 80 window (the section-4.1 construction) vs unit-normalized folded
fig 7. The pre-FSI shape (its own in-window count) and the unit-normalized
windowed table are drawn as references; pre-FSI record spikes may run off
the capped y-scale.

![Fe56 v0.3 post-FSI shapes, GEM26_11a](postfsi_shape_empm_fe56_GEM26_11a_05_000.png)
![Fe56 v0.3 post-FSI shapes, GEM26_22a](postfsi_shape_empm_fe56_GEM26_22a_05_000.png)
![Fe56 v0.3 post-FSI shapes, GEM26_22b](postfsi_shape_empm_fe56_GEM26_22b_05_000.png)
![Fe56 v0.3 post-FSI shapes, GEM21_11a](postfsi_shape_empm_fe56_GEM21_11a_05_000.png)

| tune | E panel pre → post | p panel pre → post |
|---|---|---|
| GEM26_11a_05_000 | 68,047 → 27,601 | 68,047 → 27,741 |
| GEM26_22a_05_000 | 61,692 → 23,635 | 62,492 → 24,012 |
| GEM26_22b_05_000 | 46,732 → 19,118 | 47,143 → 19,364 |
| GEM21_11a_05_000 | 58,874 → 24,453 | 59,700 → 24,851 |

(The E-panel post counts reproduce section 4's "1p in-window" column —
same selection, different normalization.)

- **The |p_m| shape is nearly FSI-invariant on iron**: post-FSI ≈ pre-FSI
  ≈ table ≈ data in every tune, even at 0.38–0.42 survival. The per-bin
  survival I4/I3 rises only mildly with |p_m| (22a: 0.32 → 0.46 across
  0–320 MeV/c), and the strongest depletion sits at low |p_m| where the
  distribution is small — so the survivor-normalized shape barely moves.
- The E_m shapes carry all the FSI distortion: 22a's survivors are broader
  than the data with the excess at 20–45 MeV (the broad ΔT_p smearing);
  GEM21's survivors lose the E_m > 35 MeV tail almost entirely (strongly
  E_m-dependent survival), while the data extend smoothly to 80 MeV.

Regenerate: `pixi run python results/template/make_postfsi_empm_shape.py --target Fe56 --all-tunes --proton-sel 1p`.

## 5. Pre- vs post-FSI proton

As v0.2 section 5 on the N_p = 1 in-window set (the dumper's `np` column;
`fsi_prepost_fe56_*.png` here):

![Fe56 v0.3 pre/post, GEM26_11a](fsi_prepost_fe56_GEM26_11a_05_000.png)
![Fe56 v0.3 pre/post, GEM26_22a](fsi_prepost_fe56_GEM26_22a_05_000.png)
![Fe56 v0.3 pre/post, GEM26_22b](fsi_prepost_fe56_GEM26_22b_05_000.png)
![Fe56 v0.3 pre/post, GEM21_11a](fsi_prepost_fe56_GEM21_11a_05_000.png)

Multiplicity on the qel ∧ hit-p ∧ window sample: 0p = 3.9/5.4/2.0/2.3 %
(≡ v0.2's proton-loss column), 1p = 69.8/68.8/71.6/71.6 %,
≥2p = 26.2/25.8/26.4/26.1 % (11a/22a/22b/GEM21). The ΔT_p physics is
unchanged from v0.2 — 11a: sharp +23.0 MeV line (96 % of survivors);
22a: broad, median 21.1 MeV; 22b/GEM21: 0.00 MeV — and the unique proton is
the primary's descendant in 100.0 % of in-window events.

Regenerate: `pixi run python results/template/make_fsi_proton_choice.py --target Fe56 --all-tunes --proton-sel 1p`.

## 6. Missing momentum: table vs QEL struck-nucleon record

Record-level — independent of the FS-proton choice; see
[v0.2 section 6](../prd-analyzer-v0.2/electron_fe56_scattering.md#6-missing-momentum-table-vs-qel-struck-nucleon-record).

## 7. Signed missing momentum (± asymmetry)

As v0.2 section 7 with N_p = 1 (`pmiss_signed_fe56_*.png` here):

| tune | generator | A pre-FSI | A post-FSI | v0.2 A post-FSI |
|---|---|---|---|---|
| GEM26_11a_05_000 | `QELKinematicsGenerator` | −0.0495 ± 0.0038 | −0.0436 ± 0.0060 | −0.0432 |
| GEM26_22a_05_000 | `QELKinematicsGenerator` | −0.0581 ± 0.0040 | −0.0565 ± 0.0064 | −0.0566 |
| GEM26_22b_05_000 | `QELEventGenerator` | −0.1416 ± 0.0046 | −0.1392 ± 0.0071 | −0.1385 |
| GEM21_11a_05_000 | `QELEventGeneratorSuSA` | +0.0036 ± 0.0041 | +0.0079 ± 0.0064 | +0.0085 |

Statistically identical to v0.2 (all shifts ≪ 1σ): the generator taxonomy
of the asymmetry is insensitive to the proton-multiplicity requirement
inside the estimator window.

Regenerate: `pixi run python results/template/make_pmiss_signed_q2cut.py --target Fe56 --all-tunes --proton-sel 1p`
(cache: `cache/pmiss_signed_fe56/` here).

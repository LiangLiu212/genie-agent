# Electron–C12 scattering — Q² slice applied (v0.2)

v0.2 instance of
[`../prd-analyzer-v0.1/electron_c12_scattering.md`](../prd-analyzer-v0.1/electron_c12_scattering.md):
the same section series with the analysis selection

**`qel && |Q²/1.28 − 1| ≤ 5 %`** (Q² ∈ [1.216, 1.344] GeV², inside the t05
generation cut)

applied to every event-level figure. Sample: the C12 full-EM t05 grid
campaign of 2026-07-26 (e⁻ 2.445 GeV, genlist EM, all four tunes on
`genie_inclxx_q2guard` with the `gem26/gem21_emq2lim` overlays, splines from
the persistent mirror), first 20 files = 2M events/tune, streamed/dumped over
XRootD. **Provenance upgrade over v0.1**: every section here — including the
ladder (v0.1: purged-June EMQE caches) and the signed p_m (v0.1: local
2026-07-17 samples) — runs on this one grid campaign, constructed identically
to Fe56; the explicit `qel` replaces v0.1's EMQE-implicit selection. The
uncut baselines live in the v0.1 note.

## 1. C12 2D spectral function — the GENIE input table

Theory input — cut-independent. See
[v0.1 section 1](../prd-analyzer-v0.1/electron_c12_scattering.md#1-c12-2d-spectral-function--the-genie-input-table)
(`sf2d_table_c12_GEM26_22a_05_000.png` there): `pke12_tot.data`, raw 4πk²
integral 6.000 = Z, E grid **[0, 400] MeV (aligned edges)**, sampling-weight
tails P(P_miss > 250 MeV/c) = 0.146, P(E_miss > 100 MeV) = 0.077.

## 2. Struck nucleon in the record: sampled (P_miss, E_rm) and (P_miss, r)

![C12 ground state realized, qel && Q² window](sf2d_events_c12_all_t05.png)

![C12 struck nucleon momentum vs position, qel && Q² window](struck_pr_c12_all_t05.png)

GHEP dumps with the `q2` column, masked to `scat = 1 && window` (the QEL
slice of the realized ground state; v0.1 section 2 used all single-nucleon
events uncut):

| tune | N (qel ∧ window) | P(p > 250) | P(E > 100) | corr(p, r) |
|---|---|---|---|---|
| GEM26_11a_05_000 | 103,338 | — | — | −0.707 |
| GEM26_22a_05_000 | 103,982 | 0.147 | 0.077 | −0.003 |
| GEM26_22b_05_000 | 75,661 | 0.103 | 0.035 | −0.003 |
| GEM21_11a_05_000 | 102,302 | — | — | −0.707 |

Reads: as on iron, **the window lifts 22a onto (and past) the table's
tails** — realized 0.147/0.077 vs table 0.146/0.077 (uncut all-process:
0.137/0.070) — while 22b's UnifiedQEL weighting suppresses the deep tail
(0.103/0.035). **GEM21's w = 0 QEL band is now the entire panel content**
(all its selected events sit in the bottom [0, 5) MeV bin — visible in-grid
on C12 because the grid starts at 0, unlike the empty Fe56 panel). The
(p, r) correlations are selection-stable: LFG wedge corr = −0.707, SF
factorized, ⟨r⟩ = 2.30 fm.

Regenerate: re-dump into `cache/hitnuc_c12/<tune>.csv`, then
`make_sf2d_events.py` / `make_struck_pr.py` with
`--target C12 --all-tunes --sel-qel-q2 --dump-dir results/prd-analyzer-v0.2/cache/hitnuc_c12 --out-dir results/prd-analyzer-v0.2`.

## 3. QEL kinematics in the slice — E_e′, θ_e′, T_p, θ_p, Q²

![C12 QEL kinematics, Q² window applied](kin_qel_q2cut_c12.png)

The window applied to the five-variable kinematics (v0.1 section 3 is the
uncut baseline; raw-counts companion `kin_qel_q2cut_c12_counts.png`; grey
dashed = the applied window edges):

| tune | N (qel ∧ window) | of qel | has_p |
|---|---|---|---|
| GEM26_11a_05_000 | 103,350 | 385,486 | 78.5 % |
| GEM26_22a_05_000 | 103,992 | 385,229 | 77.4 % |
| GEM26_22b_05_000 | 75,664 | 277,035 | 79.9 % |
| GEM21_11a_05_000 | 102,306 | 345,033 | 79.5 % |

Electron arm on the QE peak (E_e′ ≈ 1.75 GeV, θ_e′ ≈ 31.5°); **the T_p
double peak keeps the carbon ordering — the ≈0.7 GeV QE bump dominates the
low-T_p FSI population** (mirror of Fe56; transparency, section 4). 22b's
rate deficit is the smaller UnifiedQEL σ; GEM21 sits at full strength (its
C12 SuSAv2 tensor is genuine).

Regenerate: `pixi run python results/template/make_kin_qel_q2cut.py --target C12`
(also writes the 3.1 figures).

### 3.1 E_m and p_m in the slice — no E_m/p_m cuts

![C12 E_m/p_m in the slice, uncut](empm_q2cut_c12.png)

C12 instance of the Fe56 note's 3.1 (E_m = ω − T_p ≡ the restored axis;
leading proton, no-proton events dropped; section-4 window grey-dashed, not
applied; raw-counts companion `empm_q2cut_c12_counts.png`). The
out-of-window strength — the E_m continuum and the uncorrelated-proton p_m
bump at ≈ |q| — is visibly smaller than on iron: in-window fractions
53 / 45 / 49 / 48 % (11a/22a/22b/GEM21) vs Fe56's 30–35 %, the transparency
ordering again (slightly below section 4's 0.55–0.61 because this
qel-both-species sample includes hit-neutron events).

## 4. Missing energy: table vs simulation vs Dutta Fig. 9

Windowed restored ladder — now streamed from the fresh campaign (axis
E_m + T_rec, remnant B11, occupancy Z·hist/(N_sel·5 MeV), Z = 6; Dutta
fig9_q1p2 at its published scale with the fig9_common error model; the C12
table grid is aligned with the plot grid, no half-bin correction):

![C12 windowed ladder, GEM26_11a](em_ladder_restored_c12_GEM26_11a_05_000.png)
![C12 windowed ladder, GEM26_22a](em_ladder_restored_c12_GEM26_22a_05_000.png)
![C12 windowed ladder, GEM26_22b](em_ladder_restored_c12_GEM26_22b_05_000.png)
![C12 windowed ladder, GEM21_11a](em_ladder_restored_c12_GEM21_11a_05_000.png)

| tune | N_sel (of 2M) | I1 (table) | I2r = I3r | I4r | I4r/I3r | record median [p5, p95] MeV |
|---|---|---|---|---|---|---|
| GEM26_11a_05_000 | 72,490 (3.62 %) | — | 6.000 | 3.555 | 0.592 | 17.09 [16.09, 18.79] |
| GEM26_22a_05_000 | 72,953 (3.65 %) | 5.249 | 5.425 | 2.973 | 0.548 | 17.16 [16.18, 19.34] |
| GEM26_22b_05_000 | 53,517 (2.68 %) | 5.249 | 5.530 | 3.274 | 0.592 | 20.48 [15.50, 62.05] |
| GEM21_11a_05_000 | 71,630 (3.58 %) | — | 0.000 / 5.363 | 3.250 | 0.606 | −12.31 [−30.49, −1.49] |

**The fresh-sample, windowed ladder reproduces the v0.1 numbers**: I2r = I3r
exact, record medians identical (17.09/17.16/20.48/−12.31 vs v0.1's
17.09/17.15/20.37/−12.28), survivals 0.548–0.606 vs v0.1's 0.545–0.602 —
validating both the June-EMQE ≡ fresh-EM-qel equivalence and the Q²-slice
stability; the C12 > Fe56 transparency ordering (0.55–0.61 vs 0.39–0.42) is
untouched. (Numbers here carry the leading-proton **has-proton fix** — see
the Fe56 note section 4; v0.1 was re-derived with the fix on 2026-07-26 except its
C12 ladder, whose purged-June v0 caches — the survivals just quoted — retain the ~2–4 % defect.)

**Event counts, before and after FSI.** A pre-FSI primary proton exists in
100 % of selected events; a post-FSI proton exists in **95.7–98.2 %** — FSI
destroys the proton outright (absorption or charge exchange, section 5) in
the remainder. In-window ratios ≡ I4r/I3r:

| tune | N_sel | pre-FSI p (in-window) | post-FSI p (in-window) | in-window survival |
|---|---|---|---|---|
| GEM26_11a_05_000 | 72,490 | 72,490 (72,490) | 70,366 = 97.1 % (42,946) | 0.592 |
| GEM26_22a_05_000 | 72,953 | 72,953 (65,960) | 69,803 = 95.7 % (36,154) | 0.548 |
| GEM26_22b_05_000 | 53,517 | 53,517 (49,321) | 52,534 = 98.2 % (29,198) | 0.592 |
| GEM21_11a_05_000 | 71,630 | 71,630 (64,031) | 70,311 = 98.2 % (38,804) | 0.606 |

**Post-FSI shape, self-normalized** — each curve divided by its own
in-window event count (unit integral over [0, 80) MeV), data
unit-normalized too:

![C12 post-FSI shape, GEM26_11a](em_postfsi_shape_c12_GEM26_11a_05_000.png)
![C12 post-FSI shape, GEM26_22a](em_postfsi_shape_c12_GEM26_22a_05_000.png)
![C12 post-FSI shape, GEM26_22b](em_postfsi_shape_c12_GEM26_22b_05_000.png)
![C12 post-FSI shape, GEM21_11a](em_postfsi_shape_c12_GEM21_11a_05_000.png)

The carbon instance of the Fe56 finding, chain-resolved by the per-event
pre/post comparison of section 5 (an earlier revision claimed one universal
shift — wrong):

- **11a** — survivors are a **rigidly displaced δ**: ΔT_p = +20.0 MeV sharp
  (98 % within ±1 MeV) = the LFG removal energy (section 2's median
  w = 20.0 MeV, exactly), moving the record δ from 17.09 to ≈ 37 MeV, past
  the data's s-shell bump.
- **22a** — **smeared, not displaced**: ΔT_p broad (median 20.2 MeV, 20 %
  near the mode) = the sampled SF removal-energy distribution.
- **22b, GEM21** — survivors **unshifted** (ΔT_p = 0.00, 97 % within
  ±1 MeV); 22b's post-FSI ≈ pre-FSI ≈ data remains the cleanest shape
  match of the four.

Same reading as the Fe56 note section 4: the FSI write-out charges the
removal energy to the outgoing proton exactly when the FermiMover vertex
chain did not; post-FSI all four chains have paid w once. Both endpoint
protons exactly on-shell; precise code site still open
(`INUKE-NucRemovalE` = 0.00).

Regenerate: `pixi run python results/template/make_emiss_ladder_q2cut.py --target C12 --all-tunes`
(cache: `cache/ladder_c12/`; also writes the `em_postfsi_shape_c12_*`
figures).

## 5. Pre- vs post-FSI proton: the leading p against the primary-vertex p

C12 instance of the Fe56 note's section 5: the **post-FSI leading proton**
compared event-by-event against the **pre-FSI primary proton** (the
status-14 QEL vertex proton, before INTRANUKE), via the
`dump_fsiproton.cxx` GHEP dump on section 4's windowed selection (the
dumper reproduces N_sel exactly; comparison set = the post-FSI in-window
events; each figure: ω − T_p and T_p for both protons).

![C12 pre/post proton, GEM26_11a](fsi_prepost_c12_GEM26_11a_05_000.png)
![C12 pre/post proton, GEM26_22a](fsi_prepost_c12_GEM26_22a_05_000.png)
![C12 pre/post proton, GEM26_22b](fsi_prepost_c12_GEM26_22b_05_000.png)
![C12 pre/post proton, GEM21_11a](fsi_prepost_c12_GEM21_11a_05_000.png)

| tune | ΔT_p (pre − post) of survivors |
|---|---|
| GEM26_11a_05_000 | sharp line at **+20.0 MeV** (98 % within ±1 MeV) = the LFG w |
| GEM26_22a_05_000 | **broad**, median 20.2 MeV = the sampled SF w distribution |
| GEM26_22b_05_000 | **0.00 MeV** (97 % within ±1 MeV) — w paid at the vertex |
| GEM21_11a_05_000 | **0.00 MeV** (97 % within ±1 MeV) — SuSA's own prescription |

Both protons exactly on-shell in every tune.

**Why T_p here is so much narrower than in section 3.** Same variable,
different phase space: section 3 applies no E_m/p_m requirement, so its T_p
panel includes the FSI-rescattered low-T_p population (subordinate on
carbon but still large). Here E_m + T_rec = ω − T_p ∈ [0, 80) MeV pins T_p
to within 80 MeV of the energy transfer (ω ≈ 0.6–0.9 GeV in the slice) and
p_m < 300 MeV/c removes the same rescattered events on the momentum side —
section 3's low-T_p hump and section 4's out-of-window strength are the
same events on mirrored axes (T_p vs ω − T_p). The window keeps only the
~60 % quasi-elastic-like survivors, which differ from their pre-FSI selves
only by the removal-energy debit above.

**Provenance check** — within the window the leading proton IS the
primary's descendant in **100.0 % of events**, and over the full windowed
selection the breakdown is again binary:

| tune | N_sel | no FS proton at all | secondary proton leads |
|---|---|---|---|
| GEM26_11a_05_000 | 72,490 | 2,124 (2.9 %) | 0 |
| GEM26_22a_05_000 | 72,953 | 3,150 (4.3 %) | 0 |
| GEM26_22b_05_000 | 53,517 | 983 (1.8 %) | 0 |
| GEM21_11a_05_000 | 71,630 | 1,319 (1.8 %) | 0 |

Same mechanism as on iron: in hA2018 every final-state proton descends from
the primary (single-fate model), so the only FSI provenance effect is total
proton loss (absorption / p → n charge exchange, 1.8–4.3 % — smaller than
Fe56's 2.0–5.4 %, the transparency ordering again; largest for 22a). The
leading-proton reconstruction is provenance-pure within hA2018.

Regenerate: build `dump_fsiproton` (recipe in-file), dump per tune into
`cache/fsiproton_c12/`, then
`pixi run python results/template/make_fsi_proton_choice.py --target C12 --all-tunes`.

## 6. Missing momentum: table vs QEL struck-nucleon record

![C12 P_miss windowed, all t05 tunes](pmiss_struck_c12_t05.png)

Table-native 20 MeV/c grid, occupancy scale (curves integrate to Z = 6),
record from the windowed ladder caches:

| tune | median |p_n| [MeV/c] | P(p > 250 MeV/c) |
|---|---|---|
| table (sampling weight) | — | 0.146 |
| GEM26_11a_05_000 (LFG) | 152.3 | 0.027 |
| GEM26_22a_05_000 (SF) | 165.8 | 0.169 |
| GEM26_22b_05_000 (SF) | 160.1 | 0.126 |
| GEM21_11a_05_000 (LFG) | 152.5 | 0.027 |

Same pattern as v0.1 (22a ≈ table with the window enhancement 0.169 vs
0.146; 22b tail xsec-suppressed; LFG cutoff) — the slice moves the numbers
by ≲ 0.003.

Regenerate: `pixi run python results/template/make_pmiss_q2cut.py --target C12`.

## 7. Signed missing momentum (± asymmetry)

Same construction as v0.1 section 6 (sign of p_m·x̂, 4πp² divided out,
0 < E_m < 80 MeV, fig6 top+bottom combined overlay shape-scaled), now
**streamed from the grid campaign** (v0.1 used 500k-event local samples) and
with the Q² window applied:

![C12 signed p_m windowed, GEM26_11a](pmiss_signed_c12_GEM26_11a_05_000.png)
![C12 signed p_m windowed, GEM26_22a](pmiss_signed_c12_GEM26_22a_05_000.png)
![C12 signed p_m windowed, GEM26_22b](pmiss_signed_c12_GEM26_22b_05_000.png)
![C12 signed p_m windowed, GEM21_11a](pmiss_signed_c12_GEM21_11a_05_000.png)

| tune | generator | A pre-FSI | A post-FSI | v0.1 A pre-FSI (uncut, local) |
|---|---|---|---|---|
| GEM26_11a_05_000 | `QELKinematicsGenerator` | −0.0568 ± 0.0037 | −0.0499 ± 0.0048 | −0.0467 |
| GEM26_22a_05_000 | `QELKinematicsGenerator` | −0.0469 ± 0.0039 | −0.0493 ± 0.0052 | −0.0483 |
| GEM26_22b_05_000 | `QELEventGenerator` | **−0.1318 ± 0.0044** | **−0.1264 ± 0.0058** | −0.1111 |
| GEM21_11a_05_000 | `QELEventGeneratorSuSA` | **−0.0004 ± 0.0040** | **−0.0016 ± 0.0051** | +0.0030 |

The taxonomy replicates on carbon in the slice — QKG ≈ −0.05, QEG −0.13,
SuSA ≡ 0 — with 22b again amplified relative to uncut (−0.132 vs −0.111),
matching the Fe56 pattern: the Q² window concentrates the kinematic
generator asymmetry rather than removing it.

Regenerate: `pixi run python results/template/make_pmiss_signed_q2cut.py --target C12 --all-tunes`
(cache: `cache/pmiss_signed_c12/`).

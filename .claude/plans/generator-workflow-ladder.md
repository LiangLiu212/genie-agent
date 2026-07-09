# Generator workflow ladder — how GENIE implements the C12 spectral function

## Context

The input SF tables have already been compared to Dutta et al. (nucl-ex/0303011) Fig. 9
(`results/prd-analyzer/sf_input_em_fig9.png`, §8) and the pre-FSI missing energy exists
(`em_prefsi_fig9.png`, §9). This plan extends that into the full **four-stage ladder** exposing
where the generator workflow distorts the data-derived spectral function, for both the **energy
and momentum** distributions:

1. **Input** — SF tables (Benhar `pke12_tot.data`, 2024 `pke12_2024.table`). *Done (§8).*
2. **Initial state** — struck-nucleon 4-momentum in the event record (gst `En`, `pn`). *New.*
3. **Pre-FSI** — E_m/p_m reconstructed from the primary (pre-INTRANUKE) proton. *Done (§9), rebuilt into the shared cache.*
4. **Post-FSI** — same reconstruction from the post-FSI leading proton, uncut, occupancy-normalized. *New in this convention* (existing §5 uses acceptance cuts + area matching; §6 uses a Q² window + no-T_rec E_m — not apples-to-apples).

Known physics this will expose (README §9): the Rosenbluth a-tunes sample f(E) into the record
(stage 2) but do **not** propagate it into the outgoing proton — stage 3 collapses to a delta at
S_p = 15.957 MeV; the UnifiedQEL b-tunes propagate it. Stage 4 adds hA2018 FSI (absorption →
integral < Z shows transparency directly).

Everything runs on the existing five 10M-event samples (e⁻ on C12 @ 2.445 GeV, EMQE, t05),
streamed via XRootD per `results/prd-analyzer/samples.py`. No new event generation.
**Scope decision (2026-07-09):** p_m ladder included, **no external data overlay** (Fig. 6
normalization unresolved — deferred; note it in the docstring).

## Conventions (fixed, from the existing prefsi figure)

- Occupancy scale: `y = Z · hist / (n_hitp · binw)`, Z = 6; E_m: `EDGES = arange(0, 85, 5)` with
  `p_m < 300`; p_m: `P_EDGES = arange(0, 620, 20)` with `E_m < 80`.
- `M_P` from `selection.py`, `M_REC = 10.2526` GeV from `acceptance.py`; all stages conditioned on
  `hitnuc == 2212`; all arrays **float64** (bit-exact prefsi cross-check; ~340 MB total at ntot = 2M).
- Stage formulas (GeV → MeV at the end):
  - Stage 2: `E2 = (M_P − En − pn²/(2·M_REC))·1000`, `p2 = pn·1000`. The T_rec subtraction makes
    `E2 ≡ E3` for an energy-conserving chain (1-body QEL: `Ep = ω + En`, `p_miss = pn`) and lands on
    the SF-table E axis. Deliberately differs from `results/template/make_groundstate_*` (`M_N − En`,
    no T_rec, ~2 MeV at 200 MeV/c) — document in the builder docstring.
  - Stage 3: **bit-identical to `build_cache_prefsi.load_prefsi`** — leading `pdgi==2212` by
    argmax `Ei`; `p3 = |q − p_i|`; `E3 = (ω − (Ei − M_P) − p3²/(2·M_REC))·1000`.
  - Stage 4: `acceptance.py::load_events` idiom — leading `pdgf==2212` by argmax `pf`,
    `fill_none → NaN`; same E/p formulas with `Ef/pxf/pyf/pzf`. NaN (absorbed proton) drops from
    numerators, stays in `n_hitp` denominator.

## Files to create (all in `results/prd-analyzer/`)

1. **`fig9_common.py`** — shared constants/helpers lifted from `plot_sf_input_em_fig9.py` /
   `plot_em_prefsi_fig9.py` (existing plots untouched): `DATA`, `PM_MAX`, `BINW`, `EDGES`;
   `load_dutta()` (incl. the error model with the 17.5/22.5-MeV pixel-measured overrides
   0.081/0.047); `f_restricted`, `rebin`; new `n_restricted(k, E, P, dE, emax=80)` k-marginal
   (mirrors `marginals()` in `plot_spectral_function_2024.py`); `load_input_tables()` wrapping
   `find_sf_data()`/`load_old`/`load_2024`; re-export `Z`. Do NOT name it `plot_dutta_fig9.py`
   (collides with `results/template/plot_dutta_fig9.py` on sys.path).
2. **`build_cache_ladder.py`** — pattern-copy of `build_cache_prefsi.py` (spawn ctx,
   ProcessPoolExecutor, `MAX_FILES`/`WORKERS` env, savez_compressed). BRANCHES = prefsi list +
   `En, pn` + `pdgf, Ef, pxf, pyf, pzf, pf`. Writes `cache/ladder/<model>.npz`:
   `E2, p2, E3, p3, E4, p4, Q2` (masked to `hitnuc==2212`) + scalars `ntot`, `n_hitp`.
   Print survival `finite(E4).mean()` and a count of `hitp & ~finite(E3)` (expect 0; EMQE is pure QEL).
3. **`plot_em_ladder_fig9.py` → `em_ladder_fig9.png`** — `new_panels(ncols=2, nrows=2, sharey=False)`;
   panels = stages 1–4. Panel 1: the two input-table curves only (legend: LFG/SuSAv2 have no
   input-table analogue); panels 2–4: 5 model curves via `S.color/lw/zorder`; Dutta data
   (`load_dutta()`) in every panel; uniform `xlim (0, 85)`, `ylim (0, 1.3)` (a-tune delta tops ~1.2).
   Print per model: integrals I2/I3/I4 (E_m<80, p_m<300), raw survival, I4/I3, median |E2−E3|,
   frac(E_m<0) at stages 3/4 (SuSAv2 negative tail otherwise silently leaves the window).
4. **`plot_em_stages_by_model.py` → `em_stages_by_model.png`** — `new_panels(ncols=3, nrows=2)`,
   one panel per model + `axes[5].axis("off")` legend panel (the `plot_dists_q2.py` idiom). Model
   color kept; stage encoded by linestyle (2 dotted, 3 dashed, 4 solid thick); matching input table
   thin dashed where one exists; data in black. The direct "workflow impact per implementation" view.
5. **`plot_pm_ladder.py` → `pm_ladder.png`** — same 2×2 layout for p_m. Panel 1: input k-marginals
   `Z·Σ_E<80 4πk²P dE`; panels 2–4: `y = Z·hist(p_s[E_s<80])/(n_hitp·20 MeV)`; input marginals
   overlaid dashed in panels 2–4 as reference. No external data (deferred Fig. 6 — say so in docstring).

## Docs

- `results/prd-analyzer/README.md`: new **§10** with the three figures, the per-stage integral
  table, and a conventions paragraph distinguishing this from §5 (acceptance + area-matched) and
  §6 (Q² window, no T_rec); add the five Scripts entries.
- `.claude/plans/genie-experimental-spectral-function.md`: one cross-link line to README §10
  (the ladder localizes at which workflow stage the S^D distortion enters).

## Execution order & commands (repo root; all via `pixi run`)

1. `fig9_common.py`; check `load_dutta()` integral → 6.08.
2. `build_cache_ladder.py`; smoke: `MAX_FILES=1 WORKERS=1 pixi run python results/prd-analyzer/build_cache_ladder.py UnifiedQEL`
   (~1–2 min; expect ntot=100000, n_hitp≈68.7k, finite E3 == n_hitp). Doubles as the /pnfs scratch
   liveness check (samples are ~4 weeks old on scratch — if purged, stop and report; regeneration
   is out of scope).
3. Full build matching the discovered prefsi file lists (prefsi caches: ntot = 2,000,000/model):
   `export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)` (refresh: `htgettoken -a htvaultprod.fnal.gov -i dune`)
   `MAX_FILES=20 WORKERS=8 pixi run python results/prd-analyzer/build_cache_ladder.py LFG SF UnifiedQEL2024 UnifiedQEL`
   `MAX_FILES=4  WORKERS=8 pixi run python results/prd-analyzer/build_cache_ladder.py SuSAv2`
   (SuSAv2 files are 500k ev; ~20–50 min total.)
4. Verify (below), then the three plot scripts, then docs.

## Verification

- **Stage-3 reproduction (must be exact):** for each model, `n_hitp` equals the prefsi cache's and
  `histogram(E3[p3<300], EDGES)` is bin-identical to `histogram(E_miss[p_miss<300])` from
  `cache/prefsi/<model>.npz` (float64 + same file list ⇒ bit-exact).
- **Physics sanity from the printed table:**
  - SF+Rosenbluth: stage 2 rides the Benhar f(E) (peak bin ≈ 0.5); stage 3 = single-bin delta at
    15.957 MeV (SF 1.09, LFG 1.20 MeV⁻¹). LFG stage 2 = broad Fermi-gas band, no shells.
  - UnifiedQEL pair: median |E2 − E3| small (≲1 MeV) if the chain conserves energy against the
    sampled remnant — a larger offset is a finding, not a bug; report it either way.
  - Stage-2/3 integrals 5.2–6.0 (inputs 5.25/5.23, data 6.08); stage 4: I4 < I3 by ~30–45 %
    (Dutta T/1.11 ≈ 0.54 for orientation), raw survival > I4/I3 (absorption vs window migration).
- Figures render (Agg backend via `apply_style()`), README §10 images resolve.

## Out of scope / later

- Dutta Fig. 6 p/s-shell momentum overlays (normalization convention unresolved).
- Neutron-channel ladder and the "any final proton" (n→p feed-in) stage-4 variant — §5/§7
  acceptance/S^D figures already cover the data-facing selection; note as a §10 caveat.
- Full-10M cache rebuild (would revisit float32).

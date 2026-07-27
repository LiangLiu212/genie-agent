# prd-analyzer v0.3 — exactly-one-proton selection

## Context

v0.2 reconstructs the post-FSI proton as the **leading** (highest-|p|)
final-state proton. v0.3 mirrors v0.2 with that choice replaced by an
**exactly-one-proton** selection: events must have N_p(final state) = 1, and
"the" proton is that unique one (for such events it coincides with the
leading proton — the key implementation simplification). Neutrons and all
other final-state particles are unconstrained (user decision). The N_p = 1
requirement applies only where a post-FSI proton is reconstructed
(sections 3/3.1, 4-stage-4, 5, 7); the record-based sections (1, 2, 6) are
untouched by the proton choice and link to v0.1/v0.2 (user decision).

Base selection for the proton sections:
`qel && |Q²/1.28 − 1| ≤ 5 % && N_p = 1` (plus `hitnuc == 2212` where v0.2
has it: ladder, signed, §5). Samples: the same full-EM t05 campaigns
(Fe56 2026-07-16, C12 2026-07-26, 20 gst/ghep files = 2M events/tune).

## Machinery (all in `results/template/`; version-dir routing, no script duplication)

1. `results/prd-analyzer-v0/selection.py::load_events`: additionally return
   `n_p` = per-event count of final-state protons (additive key, existing
   readers unaffected).
2. `make_kin_qel.py`: KEYS += `n_p`; delete + re-stream the
   `kin_qel_<target>` caches (both targets, ~5 min; v0.1 figures unchanged).
3. `make_kin_qel_q2cut.py`, `make_emiss_ladder_q2cut.py`,
   `make_pmiss_signed_q2cut.py`, `make_fsi_proton_choice.py`: add
   `--proton-sel {leading,1p}` (default `leading` = current behavior, v0.2
   dirs). With `1p`: proton-panel/stage-4 masks use N_p = 1 instead of
   has-proton, and OUT_DIR/CACHE route to `results/prd-analyzer-v0.3/`
   (gst builders compute `n_p = ak.sum(pdgf == 2212, axis=1)` and NaN
   stage-4 columns unless n_p == 1; stages 2–3 untouched; the ladder's
   shape figures inherit automatically).
4. `dump_fsiproton.cxx`: append an `np` column (status-1 proton count);
   rebuild (in-file recipe, env -i spack shell); re-dump both targets into
   the existing `prd-analyzer-v0.2/cache/fsiproton_<target>/` (canonical
   shared source — column is additive, v0.2 outputs unaffected);
   `make_fsi_proton_choice.py --proton-sel 1p` masks np == 1 and writes to
   v0.3.
5. New v0.3 caches: `results/prd-analyzer-v0.3/cache/{ladder,pmiss_signed}_<target>/`
   (same npz schema as v0.2). The kin path needs no new cache (plot-time
   n_p mask on the v0.1 kin_qel caches, same as v0.2's window mask).

## Notes (results/prd-analyzer-v0.3/)

- `electron_fe56_scattering.md`, `electron_c12_scattering.md`: v0.2's
  section skeleton. §1/§2/§6 = one-paragraph link-sections (content
  unchanged by the proton choice, pointing at v0.1/v0.2). §3 (+3.1), §4,
  §5, §7 re-made with the 1p selection: figures, stats tables, and a short
  per-section comparison against the v0.2 (leading-proton) numbers.
- New headline stat everywhere relevant: the FS-proton **multiplicity
  split** of window events (0p / 1p / ≥2p per tune/target) — exactly what
  the selection drops relative to v0.2.
- `README.md`: index in the v0.2 style (version definition + links + the
  multiplicity-split summary).

## Execution order

1. selection.py `n_p`; kin KEYS + cache re-stream (background).
2. Dumper `np` column + rebuild + local sanity; re-dump both targets
   (background). Meanwhile add `--proton-sel` to the four scripts.
3. Ladder + signed v0.3 streams (both targets); kin + 3.1 v0.3 figures;
   §5 v0.3 figures.
4. Write the two notes + README from script stdout; view figures.
5. Report; commit only when asked. Copy this plan to
   `.claude/plans/prd-analyzer-v03-1p-selection.md` (house rule).

## Verification

- Multiplicity closure per tune: 0p + 1p + ≥2p = 100 % of window events;
  0p must reproduce v0.2 §5's no-FS-proton column (2.0–5.4 % Fe,
  1.8–4.3 % C12).
- v0.3 stage-4 in-window ⊆ v0.2's (the ≥2p in-window share is the
  difference); I2r = I3r identity unchanged (stages 2–3 untouched).
- §4 1p in-window count ≡ §5 comparison-set N (same mask, gst vs GHEP —
  the same cross-check that caught the argmax defect).
- Kin: n_p = 1 fraction from the gst cache ≡ np = 1 fraction from the GHEP
  dump (on the hitnuc==2212 subsample).
- View every figure before embedding; all table numbers from stdout.

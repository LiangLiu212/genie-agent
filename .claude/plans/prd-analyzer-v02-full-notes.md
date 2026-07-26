# prd-analyzer v0.2 — full per-target notes, all sections with the Q² cut

## Context

v0.2 currently holds only the Q²-cut kinematics figures + a README. The user
wants complete `electron_c12_scattering.md` and `electron_fe56_scattering.md`
notes in `results/prd-analyzer-v0.2/`, mirroring all six v0.1 sections with
every event-level figure re-made under the analysis selection

    qel  &&  |Q²/1.28 − 1| ≤ 5 %        (Q² ∈ [1.216, 1.344] GeV²)

on the full-EM t05 campaign samples (Fe56 2026-07-16, C12 2026-07-26,
2M events = 20 gst/ghep files per tune). Decisions taken with the user:
§1 links to v0.1 (cut-independent, no duplicated PNGs); §2 uses qel && window
(not all single-nucleon); C12 §4/§6 switch from the purged-June/local samples
to the fresh 2026-07-26 grid campaign, unifying both targets.

After approval, copy this plan to the repo's tracked
`.claude/plans/prd-analyzer-v02-full-notes.md` (house rule).

## Constraints / environment

- NFS /pnfs listing and `pixi` are broken (expired Kerberos key): all file
  listing goes over XRootD dirlist, all Python runs via
  `/exp/dune/data/users/liangliu/genie-dev/.pixi/envs/default/bin/python`,
  with `BEARER_TOKEN_FILE=/run/user/12900/bt_u12900` (refresh via htgettoken
  if expired; vault token valid).
- v0.1 scripts and outputs stay frozen; v0.2 gets its own scripts/caches so
  both versions remain independently regenerable.
- GEM26_22a C12 has 98/100 processes done (2 still running); its first-20
  file list skips process 5 — same list as v0.1 §2/§3, so consistent.

## Shared infrastructure (do first)

1. `results/template/pnfs_ls.py` (new, small): `xrootd_url(path)` +
   `gst_urls(gridlog_path, max_files)` via XRootD dirlist — factored from
   `make_kin_qel.py`; used by every v0.2 builder (NFS-free listing).
2. `results/template/dump_hitnuc.cxx`: append a `q2` column — computed as the
   experimental-like Q² from the event lepton (q = p_probe − p_fsl;
   Q² = −q·q, matching the gst `Q2` branch), i.e.
   `event->Probe()` / `event->FinalStatePrimaryLepton()` 4-momenta. CSV
   header becomes `pdg,px,py,pz,E,w,scat,r,q2` (appended → the v0.1
   named-column readers stay valid). Rebuild with the in-file recipe
   (env -i spack shell), quick sanity run on the local Fe56 ghep.
3. Re-dump both targets' 20-file GHEP lists (parallel background, pattern =
   scratchpad dump_all scripts) into
   `results/prd-analyzer-v0.2/cache/hitnuc_<target>/<tune>.csv`.

## Per-section work (both targets unless noted)

### §1 — SF input table (cut-independent)
Short section: one paragraph stating cut-independence, linking to the v0.1
note's section 1 and its figures. No new figures.

### §2 — struck nucleon (P_miss, E_rm) + (P_miss, r), qel && window
Extend `make_sf2d_events.py` and `make_struck_pr.py` (both already
`--target`-parameterized) with two optional args, default = current behavior:
`--sel-qel-q2` (mask `scat == 1 && |q2/1.28 − 1| ≤ 5 %`; requires the new q2
column) and `--out-dir` (default v0.1). Run with the v0.2 dumps and
`--out-dir results/prd-analyzer-v0.2`. Expected N ≈ 100k/tune (vs 1.9M).
Note text: v0.2 counterparts of v0.1 §2 — what the window does to the
realized ground state (Q²-acceptance shaping of (p,E) and the SRC tail;
(p,r) correlations should be selection-stable: LFG wedge, SF factorized).
GEM21 w = 0 caveat carries over (its QEL events are exactly the selection
now — the Fe56 (p,E) panel will be EMPTY in-grid; state it, keep the (p,r)
panel which is unaffected).

### §3 — QEL kinematics in the slice (already built)
Embed the existing `kin_qel_q2cut_<target>[_counts].png` + stats tables
(from the v0.2 README, which becomes an index — see below). No new plotting.

### §4 — E_m ladder vs Dutta, windowed
New `results/template/make_emiss_ladder_q2cut.py`, `--target {Fe56,C12}`:
the Fe56 streaming pattern (`make_emiss_ladder_fe56.py`) target-parameterized
with the window added:
- BRANCHES + `Q2`; keep = `qel && hitnuc==2212 && window`.
- File lists via `pnfs_ls.gst_urls` (XRootD); RUNS registries = the four
  Fe56 07-16 stems and four C12 07-26 stems (as in `make_kin_qel.py`).
- Per-target constants: Z (26/6), TGT_PDG, remnant mass (Mn55 from
  genie_pdg_table via the existing constant; B11 via `acceptance.M_REC` as in
  the C12 v0.1 script), Dutta file (fig11_q1p2.dat / fig9_q1p2.dat) +
  fig9_common error model, table via `make_sf2d_table.resolve_sf_table`.
- Reuse `load_table`/`f_restricted`/`rebin`/`occ_hist` logic (copy into the
  new script; they are short and the v0.1 scripts' module globals make import
  brittle).
- Cache `results/prd-analyzer-v0.2/cache/ladder_<target>/<tune>.npz`
  (E2/p2/E3/p3/E4/p4 + ntot/n_sel, same fields as v0.1 → §5 reads them).
- Figures `em_ladder_restored_<target>_<tune>.png` in v0.2.
Physics checks: I2r = I3r must hold per tune (energy conservation is
window-independent); C12 stage-2 record now from the fresh full-EM sample
(explicit `qel` cut replaces the EMQE-implicit one).

### §5 — P_miss struck record, windowed
New `results/template/make_pmiss_q2cut.py`, `--target`: the
`make_pmiss_fe56.py` construction (table k-marginal vs record p2 on the
native 20 MeV/c grid, occupancy scale) reading the v0.2 ladder caches.
Figure `pmiss_struck_<target>_t05.png` in v0.2.

### §6 — signed p_m, windowed
New `results/template/make_pmiss_signed_q2cut.py`, `--target`: the
`make_pmiss_signed_fe56.py` streaming construction with `Q2` added to
BRANCHES and the window in the selection (qel && hitnuc==2212 && window &&
0 < E_m < 80); import `signed_pm`, `occ_hist`, `asym` from
`make_pmiss_signed_fe56` (already imported that way by the C12 v0.1 script).
C12 now streams the grid campaign (not local runs); keep the fig7 (Fe56) /
fig6-combined (C12) data overlays by reusing the v0.1 scripts' data-loading
blocks. Cache `cache/pmiss_signed_<target>/`, figures
`pmiss_signed_<target>_<tune>.png` in v0.2. The A table is expected to move
vs v0.1 (the slice restricts the Q² lever arm of the kinematic asymmetry) —
report pre/post-FSI A per tune and compare with v0.1 in the text.

### Notes + README
- Write `electron_fe56_scattering.md` and `electron_c12_scattering.md` in
  v0.2: same section skeleton as v0.1, each section stating the windowed
  selection, its stats table, and a short read; §1 = link; cross-refs to the
  v0.1 notes for the uncut baselines.
- Rewrite `results/prd-analyzer-v0.2/README.md` as a short index (version
  definition + links to the two notes); its current §3-style content moves
  into the notes' section 3.

## Execution order

1. pnfs_ls.py helper; dumper q2 column + rebuild + local sanity.
2. Launch GHEP re-dumps (background). Meanwhile write the ladder script.
3. Ladder Fe56 + C12 (stream ~min each); pmiss from its caches.
4. Signed p_m both targets (stream).
5. §2 figures from the finished dumps.
6. Write the two notes + README rewrite, embedding printed stats.
7. Full verification pass; report. Commit only when the user asks.

## Verification

- Dumper: local 20k-event Fe56 ghep run; q2 column present, gst-like values
  (compare a few events' q2 against the gst sibling's Q2 branch).
- §4: I2r = I3r per tune/target; N_sel(§4) ≈ N(§3 window) × hit-proton
  fraction; C12 survival ratios vs v0.1 (0.55–0.60) for window-stability.
- §5: every curve integrates to Z by construction (assert in script output).
- §6: A values finite, errors ~1/√N; symmetric-data overlay renders.
- View every figure (Read) before embedding; all stats tables in the notes
  come from script stdout, not typed by hand.

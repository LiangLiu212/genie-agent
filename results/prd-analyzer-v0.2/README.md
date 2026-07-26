# prd-analyzer v0.2 — the Dutta Q² slice, cuts applied

The cut-applied version of [`../prd-analyzer-v0.1/`](../prd-analyzer-v0.1/):
every event-level figure of the v0.1 note series re-made under the analysis
selection

    qel  &&  |Q²/1.28 − 1| ≤ 5 %      (Q² ∈ [1.216, 1.344] GeV², inside t05)

on the full-EM t05 campaign samples (e⁻ 2.445 GeV, 2M streamed events/tune:
Fe56 grid 2026-07-16, C12 grid 2026-07-26 — the C12 sections all moved onto
the fresh campaign, retiring the purged-June caches and local samples of
v0.1). Constructions are identical to v0.1 up to the window; the uncut
baselines stay there.

The notes (v0.1's section skeleton plus a new section 5 — pre- vs post-FSI
proton comparison + provenance — so sections run 1–7; section 1 links to
v0.1, the SF input tables being cut-independent):

- [`electron_fe56_scattering.md`](electron_fe56_scattering.md)
- [`electron_c12_scattering.md`](electron_c12_scattering.md)

Headline v0.2 findings: the E_m ladder and its FSI in-window survival are
Q²-slice-stable on both targets (C12 fresh-sample ladder reproduces the v0.1
numbers, validating the EMQE ≡ EM+qel provenance switch); the Q² window
lifts the 22a struck-nucleon tails onto/past the SF table's sampling
weights; the signed-p_m generator taxonomy survives with slightly amplified
asymmetries (22b: −0.14 Fe56 / −0.13 C12); GEM21's w = 0 QEL population is
the entire section-2 selection (empty (p,E) panel on Fe56, bottom-bin band
on C12); the pre/post-FSI proton comparison (section 5) shows the FSI
write-out charges the nuclear-model removal energy to the surviving proton
exactly when the vertex chain skipped it — ΔT_p = the LFG w as a sharp line
for 11a (+23.0 Fe / +20.0 C), the broad SF w distribution for 22a, and zero
for 22b/SuSA (w already paid at the vertex; both endpoint protons exactly
on-shell; code site open) — so post-FSI is the first stage where all four
chains have paid w once; the GHEP provenance check shows leading ≡
primary-vertex proton in 100 % of in-window events, the only FSI provenance
effect being total proton loss (2–5 %), and exposed an unguarded-argmax
defect (non-proton posing as "leading proton" in no-proton events) now fixed
in the v0.2 builders — the v0.1 stage-4/signed numbers still carry it.

Scripts (all in `results/template/`, caches under `cache/` here):
`make_kin_qel_q2cut.py`, `make_emiss_ladder_q2cut.py`, `make_pmiss_q2cut.py`,
`make_pmiss_signed_q2cut.py` (each `--target {Fe56,C12}`), plus
`make_sf2d_events.py` / `make_struck_pr.py` with
`--sel-qel-q2 --out-dir results/prd-analyzer-v0.2` and the q2-extended
`dump_hitnuc.cxx`; XRootD listing via `pnfs_ls.py`.

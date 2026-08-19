# Fe56 EM-QE spline campaign (t04–t08) for the iron E91-013 study

Executed 2026-07-11 (from EAF). Tracked copy of the approved plan.

## Context

The (e,e′p) replication moves to Dutta's iron figures (figs 7/11). First step: Fe56
cross-section splines mirroring the carbon set. Carbon recipe (em-workflow §4):
`run_gmkspl_grid.py --probes eminus --targets C12 --tune <TUNE> --genlist EMQE -e 10
-n 30 --tarball-label genie_inclxx --tune-tarball-label gem26_emq2lim -N 1`, one job
per tune × cut-variant t04–t08.

Decisions: **4 models** — new Fe56 splines for GEM26_11a (LFG+Rosenbluth), GEM26_22a
(SF+Rosenbluth), GEM26_22b (SF+UnifiedQEL, focus); **reuse** the existing GEM21_11a
(SuSAv2, genie_dev) Fe56 splines (its t04–t08 C12-Fe56-Au197 jobs are done,
2026-06-01). 33b dropped: `pke12_2024` is C12-only; on Fe56 its param_set falls back
to `pke56_tot.data`, making 33b ≡ 22b. **Full t04–t08 ladder** → 3 × 5 = 15 grid
submissions.

**EAF constraints**: no `/pnfs` NFS mount — all PNFS verification via
`xrdfs fndca1.fnal.gov:1094` + `xrdcp` (pnfs-stream skill). `/cvmfs/fifeuser[1-4]`
mounted. Submission machinery is EAF-clean code-wise (`adapters/genie/pnfs.py`
string-only, `lib/submit.py` never touches /pnfs) — **but the pod's network
firewalls both RCDS publishers (rcds01/02:443) and every jobsub schedd
(jobsub01–05, jobsubdevgpvm01 :9618)** (measured 2026-07-11; collectors, gpce03/04
and the dCache doors fndca1:1094/fndcadoor:2880 are open). `tarball.py publish`
and `jobsub_submit` therefore hang ~15 min and die in urllib3 MaxRetryError.
**Publish + submissions run on a dunegpvm** via the hand-off script
`.claude/plans/submit_fe56_em_splines.sh` (dry-run by default, `--go` for real;
repo path identical on gpvms). Verification and analysis stay on EAF.

**Blocking fact**: GEM26_22a/22b mapped only C12 to `SpectralFunc/Default`; Fe56
silently fell back to global `LocalFGM`. The install's `SpectralFunc/Default` already
maps Fe56 → `pke56_tot.data` (file present in genie_inclxx), so the fix is one active
tune line. The 22b spline is SF-dependent (UnifiedQELPXSec integrates over the nuclear
model), so the edit must precede the submissions. Also: the published `gem26_emq2lim`
overlay had been RCDS-GC'd (>30 days) — republish was mandatory regardless.

## Steps (as executed)

1. Tune edits — `genie-agent/tunes/GEM26_2{2a,2b}/ModelConfiguration.xml`: active
   `NuclearModel@Pdg=1000260560 → genie::SpectralFunc/Default` after the C12 line;
   README notes (per-Pdg key ⇒ C12 physics byte-identical; `tune_xml_sha256` of
   records changes from 2026-07-11). GEM26_11a untouched (global LFG); 33a/33b as-is.
2. Local pilot: `run_gmkspl.py --probes eminus --targets Fe56 --tune GEM26_22b_05_000
   --genlist EMQE -n 10 -e 3 --gxmlpath genie-agent/tunes` → rc 0, spline_count > 0
   (validates pke56 loading through the overlay path).
3. Rebuild + republish overlay: `build_overlay_tarball(source_dir='genie-agent/tunes',
   subdirs=[GEM26_11a, GEM26_22a, GEM26_22b, GEM26_33a, GEM26_33b],
   label='gem26_emq2lim')` → `tarball.py publish --overwrite`, then `verify`.
4. Submit 15 jobs (fresh token; dry-run first):
   `run_gmkspl_grid.py --probes eminus --targets Fe56 --tune GEM26_{11a,22a,22b}_{04..08}_000
   --genlist EMQE -e 10 -n 30 --tarball-label genie_inclxx
   --tune-tarball-label gem26_emq2lim -N 1`.
5. Track (jobsub-jobs) + verify over XRootD only — do NOT trust `failed` status (known
   landscape-fetchlog flake; the carbon 22b records are spuriously failed). Parse each
   XML: PDG 1000260560 rows, σ(2.445 GeV) > 0; cross-checks 22a ≡ 11a (Rosenbluth
   ground-state independence), 22b ≠ 22a.
6. SuSAv2 reuse check: `xrdcp` + parse GEM21_11a_0X Fe56 σ(2.445); inspect genie_dev
   SuSAv2 tensor config for Fe56 handling (native vs nearest-nucleus scaling); record
   in v0.1 open_questions.md if scaled.
7. Bookkeeping: rebuild `run-manifest.jsonl` after the drain; commit tune edits + this
   plan when asked.

## Status after first drain (2026-07-12, verified over XRootD from EAF)

- 16 real submissions went out from the gpvm 2026-07-11 18:17 (15 + one 11a_04
  duplicate), all with the rebuilt `f433c6db…` overlay (Fe56 tunes ✓) but **default
  8 h lifetime** (pre-patch).
- **10/10 Rosenbluth splines landed and verify**: 2 channels × 30 knots each,
  σ(2.445) > 0, monotone in the Q² cut, and 22a ≡ 11a to 9 decimals per variant.
  Copies stashed in `genie-agent/splines/fe56-em/` (gitignored).
- **0/5 22b splines** — expected: the EAF pilot measures the SF-folded 22b Fe56
  spline at > 13 h CPU for n=10/e≤3, so the default-lifetime grid jobs get evicted.
  Kill + resubmit with `--expected-lifetime 48h` via
  `.claude/plans/resubmit_fe56_22b_splines.sh` (gpvm; cluster ids embedded).
- **SuSAv2 reuse**: only the **t05** June XML survived dCache's 30-day LRU (kept
  alive by the C12 campaign reads); t04/06/07/08 are evicted — 4 fresh GEM21 jobs
  needed if the SuSAv2 iron ladder is ever wanted. t05 verifies (Fe56
  σ(2.445) = 2.25×10⁻⁴, Fe56/C12 = 4.24) **but** genie_dev has **no Fe56 SuSAv2
  tensor** (tables: H1/C12/O16/Ar40 only) → Fe56 is served by nearest-nucleus
  scaling of Ar40. Recorded in v0.1 `open_questions.md`; label any iron SuSAv2
  curve as a scaled-Ar40 surrogate.

## Status after 22b resubmission drain (2026-07-15, gpvm)

- The 2026-07-14 13:38 resubmission (48 h lifetime) was 20 jobs = **4 channels
  (EMQE/EMMEC/EMRES/EMDIS) × 5 tunes** for GEM26_22b — all 20 done, one XML each
  on PNFS. Queue empty; gridlog statuses refreshed via `job.py list`.
- All 20 pulled to `genie-agent/splines/fe56-em/` as `GEM26_22b_0X_000_<GENLIST>.xml`
  (NFS cp; `job.py pull` fails on this gpvm — no `ifdh` on PATH).
- Verified: every spline is tgt 1000260560; σ(2.445) > 0 for EMQE/EMMEC and channel
  sums; 22b/22a EMQE ratio 0.55–0.70 (SF-dependence confirmed, 22b ≠ 22a). Two
  physics zeros, not defects: t08 EMDIS turns on at 2.465–2.473 GeV (Q² cut
  threshold above the 2.445 beam), and EMRES res 3/4/5/17 on the proton are zero
  over the full range in all five independent jobs (no EM proton coupling in
  Berger-Sehgal).
- Per-tune merges via `gspladd` (install env): `GEM26_22b_0X_000_EMALL.xml` =
  EMQE+EMMEC+EMRES+EMDIS, 55 splines each (2+1+36+16); verified merged names and
  σ(2.445) values identical to the parts. σ_tot(2.445) t04→t08: 1.12e-2, 1.39e-3,
  3.41e-4, 3.15e-4, 2.38e-6. Use `_EMALL` as gevgen `--cross-sections` for
  full-EM runs; per-channel files remain for single-channel runs.
- **Whole `fe56-em/` dir (36 XMLs: GEM26 11a/22a EMQE, 22b 4-channel ladder +
  EMALL merges, GEM21 t05 SuSAv2 surrogate) published to CVMFS** — label
  `fe56_em_splines`, tarball `tarball_f198b4097eb2.tar`, path
  `/cvmfs/fifeuser1.opensciencegrid.org/sw/dune/cddbdeb743097145a473f74444e1b1944f63e99abc0bf15e963ea6f83e3dd65f/fe56-em/`
  (republish moved it off the earlier fifeuser3 path — always resolve via the
  catalog label, not a hardcoded path). Future gevgen grid runs can pass those
  files directly as `--cross-sections` (CVMFS is mounted on the workers); RCDS
  GC still applies (~30 d) — re-verify the label before submitting.

## Measured runtime datapoint (EAF pilot, 2026-07-12)

The 22b_05 Fe56 local pilot (n=10 knots, e ≤ 3 GeV) passed 5 h CPU at 99 % and was
still integrating — the SF-folded UnifiedQEL spline on Fe56 is far more expensive
than C12. Consequence: the five grid 22b jobs (n=30, e=10) get
`--expected-lifetime 48h` in the hand-off script (gmkspl has no checkpointing; the
8 h default would evict them, cf. INCL26 tranche-1 NCDIS). 11a/22a Rosenbluth
splines are analytic-fast and keep the default lifetime.

## Verification

- Pilot rc 0, spline_count > 0.
- 15 XMLs on PNFS under `…/EM/genie_inclxx/<TUNE>/eminus_Fe56_*_spl/…`, each with
  Fe56 knot rows and σ(2.445) > 0.
- 22a ≡ 11a per variant; 22b differs.
- GEM21_11a Fe56 σ(2.445) sane for all five variants.

## Out of scope (next phases)

gevgen Fe56 event campaigns at 2.445 GeV per model, XRootD streaming + v0.1 iron
caches/plots. NB: `results/prd-analyzer-v0.1/samples.py::gst_urls` NFS-globs /pnfs —
on EAF it must switch to an `xrdfs` listing.

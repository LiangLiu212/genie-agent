# Produce the genie_xsec spline set for tune INCL26_07a_00_000 (NUsmall, grid)

## Context

INCL26_07a_00_000 now uses QE-CC = `genie::HybridXSecAlgorithm/Unified-CC-INCL` (updated by the
user from `Unified-CC`). The goal is to reproduce, for this tune, the AR23-style `genie_xsec` product

```
/exp/dune/data/users/liangliu/runarea/genie_xsec/v3_06_00/NULL/AR2320i00000-k250-e1000/
```

as

```
/exp/dune/data/users/liangliu/runarea/genie_xsec/v3_06_00/NULL/INCL2607a00000-k250-e1000/{data,ups}
```

Decisions taken with the user: **full 51-isotope NUsmall**, produced on the **grid**.

## The QE-CC model chain — why there is NO SF-coverage blocker and NO fallback tune

`Unified-CC-INCL` (`config/HybridXSecAlgorithm.xml:327`) sets
`DefaultXSecAlg = genie::UnifiedQELPXSec/ZExp_lqcd_incl`, whose `ZExp_lqcd_incl` param_set uses:
- `XSec-Integrator = genie::INCLQELXSec/Default`
- `IntegralNucleusGen = genie::NucleusGenHybridStruck/Default`
- `IntegralNuclearModel = genie::NuclearModelMap/Default`   ← **not** `SpectralFunc/Default`
- `CCFormFactorsAlg = genie::LwlynSmithFFCC/ZExp_lqcd`

`NuclearModelMap` reads the tune's per-nucleus `NuclearModel@Pdg` entries and, for any nucleus with no
override, returns the **global** model (`NuclearModelMap.cxx:141,193` — "default global model, should work
for all nuclei"). In INCL26_07a's `ModelConfiguration.xml` the nuclear model is now:
- C12 → `SpectralFunc/pke12_2024`
- Fe56, O16, Ar40 → `SpectralFunc/Default`  (user added, lines 41-43)
- everything else → global `LocalFGM/Default`

So the QE-CC xsec integrates over SF for the 4 SF nuclei and over LFG for the rest. **QE-CC therefore
builds for all 51 isotopes under the single tune INCL26_07a** — the previous two-tune / Nieves-fallback
design is dropped. Free nucleons (free-n, H1) are delegated to `LwlynSmithQELCCPXSec/Dipole` by the
param_set. FSI and the event generator do not affect splines; and note the tune's
`EventGenerator.xml` (`QELEventGeneratorINCL/Hybrid`) is the integrator-matched generator for the
`INCLQELXSec`/`NucleusGenHybridStruck` path, so the tune is now internally consistent (matters only for gevgen).

Residual check for execution: confirm a **non-SF nucleus** (e.g. Pb207) actually builds QE-CC under this
tune (validates the `NuclearModelMap` LFG fallback through `INCLQELXSec`) before the full run.

## Deliverable (mirror AR23 data/ + ups/)
`data/`: `gxspl-NUsmall.xml` (primary), `gxspl-freenuc.xml.gz`, `xsec_graphs.root`, `reduce_gxspl.awk`,
`isotopes.cfg`, `target.dat`, `README`, symlink `gxspl-FNALsmall.xml -> gxspl-NUsmall.xml`.
`ups/genie_xsec.table` with `Qualifiers="INCL2607a00000:k250:e1000"`, `GENIE_XSEC_TUNE="INCL26_07a_00_000"`.
Scope: 6 ν flavors (±12,±14,±16) × 51 isotopes × 250 log knots × 0.01–1000 GeV. **Charm excluded**
(matches the charm threads removed from the tune's TuneGeneratorList).

## Stage 1 — Publish a grid tarball (prerequisite)
Publish a fresh `genie_inclxx` tarball (jobsub-tarball skill) containing the `INCL26_07a` config **and**
the SF data tables it uses: `pke12_2024.table`, `pke16_tot.data`, `pke40p_tot.data`, `pke40n_tot.data`,
`pke56_tot.data` (under `data/evgen/nucl/spectral_functions/`) — these are data files, so a GXMLPATH
overlay is not enough, they must be in the base tarball. Record its `--tarball-label`; verify the tarball
contains `INCL26_07a/` and the five SF tables. (Global algs — HybridXSecAlgorithm, UnifiedQELPXSec,
INCLQELXSec, NucleusGenHybridStruck, NuclearModelMap, SpectralFunc — are already in the install.)

## Stage 2 — Grid gmkspl production  (single tune, all 51 targets)
`jobsub-agent/adapters/genie/run_gmkspl_grid.py`, `--tune INCL26_07a_00_000 -e 1000 -n 250
--tarball-label <label>`, `--probes numu,numubar,nue,nuebar,nutau,nutaubar`, targets = the 51 NUsmall
isotopes. `Default` genlist is rejected, so submit per non-charm genlist:
`CCQE, NCEL, CCRES, NCRES, CCDIS, NCDIS, CCMEC, NCMEC, CCCOHPI, NCCOHPI, CCDFR, NCDFR, NuElectronEL,
IMD, IMD-ANH, CCQE-LAMBDA` (exact strings resolved against the tune's EventGeneratorListAssembler).
- **CCQE is the bottleneck** and now covers all 51 nuclei via `INCLQELXSec`. Split it fine — per target
  (and optionally per probe) — so jobs stay short; batch cheaper genlists across many targets per job.
  `-N` replicates the same list (not a splitter); split by separate adapter calls.
- Build **free-nucleon** splines first (`--targets 1000000010,1000010010`, all flavors, all genlists) and
  reuse via `--input-cross-sections` where wanted.
- `--dry-run` each submission first.

## Stage 3 — Retrieve + combine
- `job.py status`/`job.py pull <jobid> --suffix .xml` for every submission -> local per-process XMLs.
- GENIE `gspladd` (in `$GENIE/bin`; no genie-agent helper): combine per (nu,target) across processes, then
  across targets, then across flavors -> one `total_xsec.xml`. Reference orchestration:
  `.../src/scripts/production/batch/xsec_splines/group_spline.pl`.
- `gspl2root -p 12,-12,14,-14,16,-16 -t <targets> -f total_xsec.xml -o xsec_graphs.root --tune INCL26_07a_00_000`.
- `gzip` the free-nucleon-only combination -> `gxspl-freenuc.xml.gz`.

## Stage 4 — Assemble the product dir
- Building exactly the 51 NUsmall isotopes means `total_xsec.xml` **is** `gxspl-NUsmall.xml` (rename; no
  reduce needed). Copy `reduce_gxspl.awk` + `isotopes.cfg` from AR23 for parity. (127-isotope
  `gxspl-NUbig.xml.gz` is out of scope unless requested.)
- Copy AR23 `README`; edit: tune -> `INCL26_07a_00_000`; QE-CC = `Unified-CC-INCL` (SF for
  C12[pke12_2024]/Fe56/O16/Ar40, LFG for all other nuclei, free nucleons via Llewellyn-Smith); charm excluded.
- Copy `ups/genie_xsec.table`, edit `Qualifiers`/`GENIE_XSEC_TUNE`; recreate the `gxspl-FNALsmall.xml` symlink.

## Verification
1. **Re-measure cost + confirm non-SF build**: the earlier ~21 min/30-knot figure was for the OLD
   `Unified-CC` (NewQELXSec integrator); `Unified-CC-INCL` uses `INCLQELXSec`. Run a short gmkspl (C12 and
   a non-SF nucleus e.g. Pb207, few knots, CCQE) to confirm Pb207 builds and to get the real per-spline time.
2. Spline sanity: 51 unique `tgt:`; `nknots="250"`; QE-CC spline names show the top-level
   `HybridXSecAlgorithm/Unified-CC-INCL` key for **all** targets, free nucleons included
   (verified 2026-07-07 on the produced XMLs: spline keys carry the EventGenerator-level
   algorithm; delegate names like `UnifiedQELPXSec/ZExp_lqcd_incl` or
   `LwlynSmithQELCCPXSec/Dipole` never appear in keys).
3. `gspl2root` opens; `run_gevgen.py` on C12, Ar40, and a non-SF nucleus (Pb207) with the produced
   `gxspl-NUsmall.xml` (`--tune INCL26_07a_00_000 --genlist CCQE -n 200 -e 3 --foreground`) exits 0.

## Key paths / reusable tools
- AR23 reference: `.../NULL/AR2320i00000-k250-e1000/{data,ups}` (README, isotopes.cfg, reduce_gxspl.awk, ups table).
- Grid: `jobsub-agent/adapters/genie/run_gmkspl_grid.py`, worker `templates/gmkspl_grid.sh`,
  `jobsub-agent/scripts/job.py`; skills `genie-grid`, `jobsub-tarball`, `jobsub-submit`, `jobsub-jobs`.
- Local: `genie-agent/scripts/run_gmkspl.py` / `run_gevgen.py`; PDG resolve `genie-agent/lib/pdg.py`.
- GENIE bins: `gspladd`, `gspl2root` in `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator/bin`.

## Stage 2 execution status (updated 2026-07-03)

- **Tranche 1 (submitted 2026-07-01):** free-n, H1, C12, O16, Ar40, Fe56 at full production
  settings (250 knots, e1000, all 6 flavors, tarball label `genie_inclxx`), CCQE per-target +
  the other genlists combined across the 6 targets. Resolved genlist names: CCQE NCEL CCRES
  NCRES CCDIS NCDIS CCMEC NCMEC CCCOHPION NCCOHPION CCDFR NCDFR NuEElastic IMD LambdaCCQE
  (15 — **IMD-ANH was not submitted**; open whether it resolves under this tune's assembler).
  19/20 jobs done with XMLs on PNFS; the 6-target **NCDIS** job was evicted at exactly its
  20 h `--expected-lifetime` and restarted from scratch (NumJobStarts=2; gmkspl has no
  checkpointing) — still running on attempt 2.
- **Pb207 residual check passed** locally 2026-07-01 (`gmkspl-numu_C12-Pb207_…-e69b3d`,
  rc 0, spline_count 2): the NuclearModelMap LFG fallback builds QE-CC through INCLQELXSec.
- **Tranche 2 (drafted 2026-07-03):** the remaining 45 NUsmall isotopes via
  `.claude/plans/submit_incl26_07a_tranche2_splines.sh` — 230 submissions, per-genlist chunk
  table in the script header. Two hard constraints discovered and now enforced:
  (a) every job must fit inside `--expected-lifetime` (eviction restarts gmkspl from zero);
  (b) **at most 6 targets per job** — the worker output filename embeds the probe+target
  symbol and PDG lists and hits NAME_MAX=255 (6-target names already run 237–251 chars);
  `run_gmkspl_grid.py` now rejects over-long combinations at submit time.
- **Bug fixed 2026-07-03** (`jobsub-agent/lib/submit.py`): `--dry-run` used to append
  `--no_submit` *after* the worker script in the jobsub argv, so jobsub passed it to the
  worker and submitted a **real** job. The 2026-07-01 "pending" C12-Pb207 gridlog record was
  such an accidental submission (no output, long gone); a 2026-07-03 accidental job
  (cluster 92147921) was `jobsub_rm`'d. `--no_submit` is now inserted before the `file://`
  executable.
- **Tranche 2 verified 2026-07-07 — complete except iron.** Queue fully drained; the
  tranche-1 6-target NCDIS job finished on its restart (all 20 tranche-1 jobs done).
  PNFS sweep: 247/251 July records have their XML (gridlog status agrees with PNFS
  everywhere; the 4th non-done record is the known dry-run-artifact `pending` C12-Pb207).
  Coverage vs the AR23 `gxspl-FNALsmall.xml` target list (51 unique `tgt:` codes —
  identical to our submitted set): **14/15 genlists at 51/51; CCQE at 48/51, missing
  Fe54/Fe57/Fe58** (all three failed, 0 output).
- **Root cause: NuclearModelMap keys per-nucleus overrides by Z, not full PDG.**
  `NuclearModelMap.cxx::LoadConfig` stores `fRefinedModels[IonPdgCodeToZ(pdg)]` and
  `SelectModel` looks up `t.Z()`, so the tune's `NuclearModel@Pdg=1000260560 ->
  SpectralFunc/Default` captures **all Z=26 isotopes**; `SpectralFunc::
  SelectSpectralFunction` finds no `SpectFuncTable@Pdg=10002605{4,7,8}0_*` entry and
  `std::exit(1)`s (worker log: "spectral function for target 1000260540 … isn't
  available"; job exit 1). A GENIE tune therefore **cannot express per-isotope SF-vs-LFG
  within one element** — the same trap will hit gevgen on any non-56 Fe isotope (and any
  non-12 C / non-16 O / non-40 Ar isotope, e.g. much of NUbig).
- **Fix for the 3 CCQE splines — resolved 2026-07-07 (user decision):** (a) SF for Fe
  disabled in the tune itself (`config/INCL26_07a/ModelConfiguration.xml`: the
  `Pdg=1000260560 -> SpectralFunc/Default` line commented out with a dated note; all
  iron now uses the global LFG, so gevgen no longer crashes on any Fe isotope); (b) the
  three missing CCQE splines were **copied from the AR23 product** instead of being
  rebuilt (see Stage 3 below). The GXMLPATH-overlay rebuild
  (`--tune-tarball-label` on the grid, or local `run_gmkspl.py --gxmlpath`) remains the
  way to produce native Unified-CC-INCL/LFG splines for them later if wanted.
  CAVEATS: the tune's SF-for-Fe56 is now gone everywhere (its already-built CCQE spline
  in this set *is* SF-based — rate SF, event kinematics LFG); the `genie_inclxx` grid
  tarball still contains the pre-edit ModelConfiguration (republish before any future
  grid job of this tune); the INCL26_07a config dir was untracked in the install's git
  checkout — **committed and pushed 2026-07-07** as `db97227af` ("config: track the
  INCL26_07a tune, with SpectralFunc disabled for Fe") on `feature/for_Anna` ->
  LiangLiu212/Generator, so `genie_install_git` now fingerprints the tune (the checkout
  stays `dirty:true` from unrelated modified configs — HybridXSecAlgorithm.xml,
  MECGeneratorINCL.xml — and the other untracked tune families).

## Stage 3 execution status (2026-07-07) — gxspl-NUsmall.xml built

- **Pulled** all 247 produced XMLs (`job.py pull --suffix .xml`, 0 failures; every July
  gridlog now has `outputs_pulled:true`). Host-side ifdh needs
  `IFDHC_DIR`/`IFDHC_CONFIG_DIR`/PATH from the CVMFS spack `ifdhc` (bare binary throws
  "no ifdhc config file environment variables found").
- **AR23 Fe splice:** 18 CC-QES splines (6 flavors x Fe54/57/58) extracted from the AR23
  `gxspl-NUsmall.xml` (sha256 `70035014a2ce…`), re-keyed
  `genie::NievesQELCCPXSec/ZExp` -> `genie::HybridXSecAlgorithm/Unified-CC-INCL` and
  wrapped under `genie_tune name="INCL26_07a_00_000"` (XSecSplineList's spline map is
  keyed by tune, then by algorithm+interaction — both levels had to be renamed; the
  interaction substrings are byte-identical between the two products). Physics note:
  these three splines are Nieves z-exp LFG numbers served under the Unified-CC-INCL key.
  Files: `INCL2607a00000-k250-e1000/work/gxspl_fe545758_ccqe_from_ar23.xml`
  + `.provenance.json` (also copied to `data/`; an XML comment in the spliced entries'
  file records the same).
- **Combined** with `gspladd -d <stage of 248 files> -o …` (34 s) ->
  `INCL2607a00000-k250-e1000/data/gxspl-NUsmall.xml`, 510,186,170 bytes,
  sha256 `c8568db959cf38debb6aa0f1782e8f59a70c9f87e882630c47406903e9caac9e`.
- **Verified:** 29,760 splines, one `genie_tune` section (INCL26_07a_00_000); 51 unique
  targets == AR23's; no duplicate keys; all `nknots="250"`; CC-QES for all 51 targets
  (incl. the spliced Fe) under the single Hybrid key. Diff vs AR23 is **exactly** the
  1,950 charm entries (1,500 `AivazisCharmPXSecLO/CC-Default` + 450
  `KovalenkoQELCharmPXSec/Default`) — nothing else, which also closes the tranche-1
  IMD-ANH question: AR23's NUsmall has no IMD-ANH splines, so the 15 submitted genlists
  were complete.
- **Smoke test:** `run_gevgen.py --probe numu --target Fe54 -n 50 -e 3 --genlist CCQE`
  against the final file: rc 0, 54 s wall, zero "Computing spline" lines (spliced spline
  found and loaded), GHEP written (`gevgen-numu_Fe54_20260707-100506-ef5-f5e311`) — the
  previously-crashing path now works end to end.
- **UPS instance created 2026-07-07 (AR23 analog):** `ups/genie_xsec.table` (Qualifiers
  `INCL2607a00000:k250:e1000`, `GENIE_XSEC_TUNE=INCL26_07a_00_000`, GENLIST Default,
  KNOTS 250, EMAX 1000.0), version declaration
  `genie_xsec/v3_06_00.version/NULL_INCL2607a00000-k250-e1000`, and the
  `gxspl-FNALsmall.xml -> gxspl-NUsmall.xml` symlink. The runarea lacked the
  `.upsfiles/dbconfig` db marker (even the AR23 instance could not `setup` from it);
  created a minimal one with `PROD_DIR_PREFIX = ${UPS_THIS_DB}`. Verified in a clean
  shell with `PRODUCTS=/exp/dune/data/users/liangliu/runarea:$PRODUCTS`: `ups list`
  shows both instances and `setup genie_xsec v3_06_00 -q INCL2607a00000:k250:e1000`
  exports GENIEXSECFILE/GENIE_XSEC_TUNE/… correctly (AR23 instance also set up as a
  regression check).
- **Product tarball built 2026-07-07 (scisoft-style, INCL26 instance only):**
  `runarea/genie_xsec-3.06.00-noarch-INCL2607a00000-k250-e1000.tar.bz2` (44,320,423 B,
  sha256 `7789db292a3d999b64af27a33d35b3542323e80142609519902ddd583f992190`), containing
  exactly `NULL/INCL2607a00000-k250-e1000/{data,ups}` + the
  `v3_06_00.version/NULL_INCL2607a00000-k250-e1000` declaration (the `work/` build
  scaffolding is deliberately excluded — a first attempt swept it in). Round-trip
  verified: extracted into a fresh db (needs a `.upsfiles/dbconfig`, as any products
  area does), `setup genie_xsec v3_06_00 -q INCL2607a00000:k250:e1000` -> SETUP-OK,
  tune env correct, and sha256 through the extracted `gxspl-FNALsmall.xml` symlink
  matches the source (`c8568db9…`). Note the tarball predates `xsec_graphs.root`/
  `README`/`isotopes.cfg` etc. — rebuild it if those are added for full AR23 parity.
- **Remaining for Stage 3/4:** `gspl2root` -> `xsec_graphs.root`; free-nucleon-only
  combination -> `gxspl-freenuc.xml.gz`; copy/edit `README`, `isotopes.cfg`,
  `reduce_gxspl.awk`; gevgen checks on C12/Ar40.

## Notes / open choices
- QE-CC = `HybridXSecAlgorithm/Unified-CC-INCL` for all 51 nuclei; no fallback tune (superseded by the
  NuclearModelMap LFG fallback).
- The tune now applies SF to 4 nuclei (C12=`pke12_2024`; Fe56/O16/Ar40=`SpectralFunc/Default` Benhar),
  changed from the earlier "C12 only"; all other nuclei use `LocalFGM/Default`.
- The earlier CCQE smoke-test spline used the OLD `Unified-CC`; rebuild a smoke test under `Unified-CC-INCL`.
- Charm excluded (tune's TuneGeneratorList). Build only the 51 NUsmall isotopes (skip 127-isotope NUbig).

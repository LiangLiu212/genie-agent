# Produce the genie_xsec spline set for tune INCL26_07a_00_000 (NUsmall, grid)

## Context

The tune `INCL26_07a_00_000` now exists and is verified (QE-CC = `HybridXSecAlgorithm/Unified-CC`,
C12 SF `pke12_2024`, INCL FSI; smoke-test gmkspl on C12 exited 0). The user wants the same kind of
`genie_xsec` product that exists for AR23, i.e. reproduce

```
/exp/dune/data/users/liangliu/runarea/genie_xsec/v3_06_00/NULL/AR2320i00000-k250-e1000/
```

for INCL26_07a. Target output dir (verified naming = tune with underscores stripped):

```
/exp/dune/data/users/liangliu/runarea/genie_xsec/v3_06_00/NULL/INCL2607a00000-k250-e1000/{data,ups}
```

Decisions taken with the user: **full 51-isotope NUsmall** (with a QE fallback for non-SF nuclei),
produced on the **grid**.

### The governing constraint (why a fallback is needed)
INCL26_07a's QE-CC (`Unified-CC` -> `UnifiedQELPXSec/ZExp_lqcd`) integrates over `SpectralFunc/Default`,
which has tables for **only C12, O16, Ar40, Fe56** (verified in `config/SpectralFunc.xml`) + free
nucleons via the LwlynSmith delegation. The AR23 NUsmall has **51 isotopes**; the other 47 cannot get a
QE-CC Unified spline. AR23 avoided this by using `NievesQELCCPXSec` (all nuclei). Note: **FSI (INCL) and
the event generator do NOT affect cross-section splines** — only the QE-CC XSec model and the nuclear
model matter for gmkspl. So the fallback only needs to swap the QE-CC XSec model for non-SF nuclei.

## Deliverable (mirror AR23 data/ + ups/)
`data/`: `gxspl-NUsmall.xml` (primary), `gxspl-freenuc.xml.gz`, `xsec_graphs.root`, `reduce_gxspl.awk`,
`isotopes.cfg`, `target.dat`, `README`, symlinks `gxspl-FNALsmall.xml -> gxspl-NUsmall.xml`.
`ups/genie_xsec.table` with `Qualifiers="INCL2607a00000:k250:e1000"`, `GENIE_XSEC_TUNE="INCL26_07a_00_000"`.
Scope: 6 ν flavors (±12,±14,±16) × 51 isotopes × 250 log knots × 0.01–1000 GeV, **charm excluded**
(matches the charm threads removed from the tune's TuneGeneratorList).

## Stage 0 — QE fallback tune  `INCL26_07a_fb`
Two-tune split (recommended over per-nucleus `HybridXSecAlgorithm` routing — no fragile
interaction-string matching, each tune self-consistent, the key SF nuclei can't silently misroute):
- Copy `config/INCL26_07a` -> `config/INCL26_07a_fb` (a full tune, id `INCL26_07a_fb_00_000`).
- In `INCL26_07a_fb/ModelConfiguration.xml`, change **only** the QE-CC line:
  `genie::HybridXSecAlgorithm/Unified-CC` -> `genie::NievesQELCCPXSec/ZExp` (AR23's model; works for all
  nuclei; Z-expansion axial FF). Everything else identical, so every non-QE process is identical to
  INCL26_07a.
- Partition of the 51 targets: **SF = {C12, O16, Ar40, Fe56} + free-n/H1 -> tune INCL26_07a**;
  **the other 47 nuclei -> tune INCL26_07a_fb**. Each nucleus is built entirely under one tune, so all
  its processes are consistent.
- Verify locally (cheap, few knots): `run_gmkspl.py --genlist CCQE` on e.g. `Pb207` under `_fb` exits 0
  and `spline_count>0`; C12 under INCL26_07a already verified (Unified).
- Alternative (documented, not recommended): single tune-local `INCL26_07a/HybridXSecAlgorithm.xml`
  with `DefaultXSecAlg=NievesQELCCPXSec/ZExp` + 24 `XSecAlg@Interaction=...tgt:<SF pdg>...` overrides ->
  `UnifiedQELPXSec/ZExp_lqcd`. Matching is exact-string (`HybridXSecAlgorithm.cxx:31-61`); proven format
  from the existing free-nucleon overrides, but a mismatch would silently drop an SF nucleus to Nieves.

## Stage 1 — Publish a grid tarball (prerequisite)
The grid worker needs the current install: **INCL26_07a + INCL26_07a_fb configs AND `pke12_2024.table`**
(a data file under `data/evgen/nucl/spectral_functions/`, so a GXMLPATH overlay is not enough — it must
be in the base tarball). Use the **jobsub-tarball** skill to publish a fresh `genie_inclxx` tarball;
record its label for `--tarball-label`. Verify the published tarball contains `INCL26_07a/`,
`INCL26_07a_fb/`, and `pke12_2024.table`.

## Stage 2 — Grid gmkspl production  (`jobsub-agent/adapters/genie/run_gmkspl_grid.py`)
Per-genlist submissions (250 knots, 1000 GeV). `Default` genlist is rejected, so enumerate the
non-charm processes seen in AR23's NUsmall:
`CCQE, NCEL, CCRES, NCRES, CCDIS, NCDIS, CCMEC, NCMEC, CCCOHPI, NCCOHPI, CCDFR, NCDFR, NuElectronEL,
IMD, IMD-ANH, CCQE-LAMBDA` (exact genlist strings resolved against the tune's EventGeneratorListAssembler
at run time). For each: `--probes numu,numubar,nue,nuebar,nutau,nutaubar`, targets = the partition list,
`--tune INCL26_07a[_fb]_00_000 -e 1000 -n 250 --tarball-label <label>`.
- **CCQE is the bottleneck** (~3 h/flavor-target for Unified). Split it fine: separate submission
  **per target** (and optionally per probe) so jobs stay short; cheaper genlists can batch many targets
  per job. `-N` replicates the same list (not a splitter) — split by making separate adapter calls.
- Build **free-nucleon** splines first (`--targets 1000000010,1000010010` = free-n,H1, all flavors, all
  genlists); reuse as `--input-cross-sections` for nuclear jobs where the workflow wants it.
- `--dry-run` each submission first to inspect argv.

## Stage 3 — Retrieve + combine
- `job.py status <jobid>` / `job.py pull <jobid> --suffix .xml` for every submission -> local per-process XMLs.
- Combine with GENIE `gspladd` (in `$GENIE/bin`; no genie-agent helper exists): per (nu,target) across
  processes, then across targets, then across flavors -> one `total_xsec.xml`. (AR23's Perl
  `.../src/scripts/production/batch/xsec_splines/group_spline.pl` is the reference orchestration.)
- `gspl2root -p 12,-12,14,-14,16,-16 -t <targets> -f total_xsec.xml -o xsec_graphs.root --tune INCL26_07a_00_000`.
- `gzip` the free-nucleon-only combination -> `gxspl-freenuc.xml.gz`.

## Stage 4 — Assemble the product dir
- Since we build exactly the 51 NUsmall isotopes, `total_xsec.xml` **is** `gxspl-NUsmall.xml` (rename;
  no reduce needed). Still copy `reduce_gxspl.awk` + `isotopes.cfg` from AR23 for parity. (Building the
  127-isotope `gxspl-NUbig.xml.gz` is out of scope unless requested — ~2.5x more targets.)
- Copy `README` from AR23 and edit: tune -> `INCL26_07a_00_000`, note the QE fallback (SF nuclei =
  Unified-CC; other 47 = Nieves/ZExp), and charm excluded.
- Copy `ups/genie_xsec.table`, edit `Qualifiers`/`GENIE_XSEC_TUNE`. Recreate the `gxspl-FNALsmall.xml`
  symlink.

## Verification (end-to-end)
1. Spline sanity: `grep -c '<spline name=' gxspl-NUsmall.xml`; unique `tgt:` count == 51; `nknots="250"`;
   confirm the 4 SF nuclei's QE-CC splines use the Unified algorithm name and the other 47 use
   `NievesQELCCPXSec` (grep spline names by `tgt:` pdg).
2. `gspl2root` succeeds and `xsec_graphs.root` opens.
3. Real event test: `run_gevgen.py --probe numu --target C12 --cross-sections <abs gxspl-NUsmall.xml>
   --tune INCL26_07a_00_000 --genlist CCQE -n 200 -e 3 --foreground` exits 0; repeat on `Ar40` and a
   fallback nucleus (e.g. `Pb207`) to confirm the whole set is usable.

## Key paths / reusable tools
- AR23 reference: `.../NULL/AR2320i00000-k250-e1000/{data,ups}` (README, isotopes.cfg, reduce_gxspl.awk,
  ups table templates).
- Grid: `jobsub-agent/adapters/genie/run_gmkspl_grid.py`, worker `templates/gmkspl_grid.sh`,
  `jobsub-agent/scripts/job.py`; skills `genie-grid`, `jobsub-tarball`, `jobsub-submit`, `jobsub-jobs`.
- Local: `genie-agent/scripts/run_gmkspl.py` / `run_gevgen.py`; PDG resolve `genie-agent/lib/pdg.py`.
- GENIE bins: `gspladd`, `gspl2root` in `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator/bin`.

## Open choices (sensible defaults taken; adjust if desired)
- Fallback QE model = `NievesQELCCPXSec/ZExp` (matches AR23). Alt: `LwlynSmithQELCCPXSec/Dipole`.
- Build only the 51 NUsmall isotopes (skip 127-isotope NUbig).
- Charm excluded (per the tune's TuneGeneratorList edit).
- Global nuclear model for non-C12 nuclei is `LocalFGM/Default` (set during tune build); this affects the
  47 fallback nuclei's QE/MEC/RES integrals vs AR23's `SpectralFunctionLikeWithCorrelation`.

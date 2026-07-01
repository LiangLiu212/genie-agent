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
2. Spline sanity: 51 unique `tgt:`; `nknots="250"`; QE-CC spline names show `UnifiedQELPXSec/ZExp_lqcd_incl`
   for nuclei and `LwlynSmithQELCCPXSec/Dipole` for free nucleons.
3. `gspl2root` opens; `run_gevgen.py` on C12, Ar40, and a non-SF nucleus (Pb207) with the produced
   `gxspl-NUsmall.xml` (`--tune INCL26_07a_00_000 --genlist CCQE -n 200 -e 3 --foreground`) exits 0.

## Key paths / reusable tools
- AR23 reference: `.../NULL/AR2320i00000-k250-e1000/{data,ups}` (README, isotopes.cfg, reduce_gxspl.awk, ups table).
- Grid: `jobsub-agent/adapters/genie/run_gmkspl_grid.py`, worker `templates/gmkspl_grid.sh`,
  `jobsub-agent/scripts/job.py`; skills `genie-grid`, `jobsub-tarball`, `jobsub-submit`, `jobsub-jobs`.
- Local: `genie-agent/scripts/run_gmkspl.py` / `run_gevgen.py`; PDG resolve `genie-agent/lib/pdg.py`.
- GENIE bins: `gspladd`, `gspl2root` in `/exp/dune/app/users/liangliu/GENIE/GENIE_INCLXX/Generator/bin`.

## Notes / open choices
- QE-CC = `HybridXSecAlgorithm/Unified-CC-INCL` for all 51 nuclei; no fallback tune (superseded by the
  NuclearModelMap LFG fallback).
- The tune now applies SF to 4 nuclei (C12=`pke12_2024`; Fe56/O16/Ar40=`SpectralFunc/Default` Benhar),
  changed from the earlier "C12 only"; all other nuclei use `LocalFGM/Default`.
- The earlier CCQE smoke-test spline used the OLD `Unified-CC`; rebuild a smoke test under `Unified-CC-INCL`.
- Charm excluded (tune's TuneGeneratorList). Build only the 51 NUsmall isotopes (skip 127-isotope NUbig).

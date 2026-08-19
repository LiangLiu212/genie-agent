# G18_02a_00_000 spline set, 0.01–5000 GeV, GENIE v3.6.2 — campaign log

Approved plan: `~/.claude/plans/hello-now-i-need-swirling-kahan.md` (2026-08-19).
Template campaign: `incl26_07a-xsec-spline-set.md`.

## Fixed inputs

- GENIE **v3.6.2**, tag `R-3_06_02`, commit `4a6d9e5e50ed9ae72636dd363a2f3fbf672330a6`
  ("Version 3.06.02", 2025-07-01), cloned `--depth 1` into
  `/exp/dune/app/users/liangliu/GENIE/GENIE_v3_6_2/Generator`.
- Installation key `genie_v3_6_2` (registered in `genie-agent/config/genie_env.json` 2026-08-19).
- Tune `G18_02a_00_000`, channels = tune Default (18 generators) as 16 genlists:
  `CCQE NCEL CCMEC NCMEC CCRES NCRES CCDIS NCDIS CCCOHPION NCCOHPION CCDFR NCDFR
   NuEElastic IMD LambdaCCQE Charm`.
- Probes: all 6 flavors. `-e 5000 -n 300`.
- Targets: 41 natural isotopes of H Be B C N O F Na Al Si Cl Ar Fe Ni Cu Br W
  (+ free neutron `1000000010` in the vN stage):
  H1 H2 Be9 B10 B11 C12 C13 N14 N15 O16 O17 O18 F19 Na23 Al27 Si28 Si29 Si30
  Cl35 Cl37 Ar36 Ar38 Ar40 Fe54 Fe56 Fe57 Fe58 Ni58 Ni60 Ni61 Ni62 Ni64
  Cu63 Cu65 Br79 Br81 W180 W182 W183 W184 W186
- Stage-4 chunks: K1 H2,Be9,B10,B11,C12,C13 · K2 N14,N15,O16,O17,O18,F19 ·
  K3 Na23,Al27,Si28,Si29,Si30,Cl35 · K4 Cl37,Ar36,Ar38,Ar40,Fe54,Fe56 ·
  K5 Fe57,Fe58,Ni58,Ni60,Ni61,Ni62 · K6 Ni64,Cu63,Cu65,Br79,Br81,W180 ·
  K7 W182,W183,W184,W186

## Stage 0 — build & register (2026-08-19)

- [x] Clone `R-3_06_02` → commit `4a6d9e5e50ed9ae72636dd363a2f3fbf672330a6`.
- [x] Config gates pre-build (all vs v3.6.0 reference, IDENTICAL):
      `config/G18_02a/TuneGeneratorList.xml` (18 generators),
      IMD/Charm `param_set`s in `EventGeneratorListAssembler.xml`,
      all 16 genlists present, `data/evgen/catalogues/iso/natural-isotopes.data`.
- [x] Configure: skill recipe **+ `--disable-lhapdf5`** (recorded into genie-install
      SKILL.md). libxml2 resolves to the system external (`/usr/include/libxml2`) —
      same as reference builds. Build script: `$GENIEBASE/build_genie.sh`,
      log `$GENIEBASE/build.log`.
- [x] `make` finished rc 0, BUILD_OK 2026-08-19 18:33 UTC (single-core EAF build,
      ~35 min). 188 libs; gmkspl/gspladd/gspl2root/gevgen/gntpc present.
- [x] `setup_env.sh` written (skill heredoc, non-INCL).
- [x] Registered `genie_v3_6_2` in `genie_env.json` (active_installation flip
      deferred to first grid submission; all commands pass `--installation`).
- [x] Env snapshot `config/env/genie_v3_6_2.json` (47 vars, GENIE + XSECSPLINEDIR
      point at the new install).
- [x] Smoke (a) CCQE C12: `gmkspl-numu_C12_20260819-183428-fd0-ca38ca`, rc 0,
      91.6 s, spline_count 1.
- [x] **Charm go/no-go** (b): `gmkspl-numu_C12_20260819-183629-588-5557ed`, rc 0,
      392.8 s, spline_count 9 = 6× AivazisCharmPXSecLO (DIS-CC-CHARM, n/p × s/v/3(s))
      + 3× KovalenkoQELCharmPXSec (QEL-CC-CHARM, Λc+/Σc+/Σc++). **GO.**

## Stage 1 — tarball

- [x] build: `jobsub-agent/tarballs/tarball_084bd2a68abc.tar` (405.5 MB, sha 084bd2a68abc),
      toplevel Generator+data+setup_env.sh, excl. src/.git/.o/.d.
- [x] publish label `genie_v3_6_2` →
      `/cvmfs/fifeuser1.opensciencegrid.org/sw/dune/120083695b901536884562f73373f8681cc7e5c5ba106dc0184d888f82801b86`
- [x] verify: exists / ok (age 0d).
- [x] 1-job grid smoke (numu C12 CCQE -n 30 -e 5):
      `gmkspl_grid-numu_C12_20260819-190343-ce0db8`, cluster 86282706.0@jobsub01,
      done in ~8 min wall; pulled XML: 1 spline, nknots=30, genie_tune=G18_02a_00_000.
      **ABI gate green** — the `--first`-concretized local build runs on workers.

### Tooling fixes required for EAF operation (2026-08-19)

- `job.py status/list` stamped a false "failed" at queue-drain: `count_pnfs_outputs`
  shells `ifdh` (absent on EAF) and silently returned 0. Fixed in
  `jobsub-agent/lib/monitor.py` + new `jobsub-agent/lib/pnfs_io.py`: ifdh falls
  back to `xrdfs` via root://fndca1.fnal.gov:1094 (pnfs-stream namespace mapping).
- `job.py pull` same story (`ifdh ls/cp`): `jobsub-agent/lib/outputs.py` now falls
  back to `xrdfs ls` / `xrdcp`.
- New `job.py status --recheck-outputs`: re-evaluates a "failed" record whose
  outputs were never pulled (queue-drain vs dCache-listing race); other terminal
  states stay sticky. Used to repair the smoke record (failed → done).
- `jobsub_fetchlog` → landscape returns 404 for these jobs (no worker logs
  available); timing must come from PNFS mtimes (upper bounds incl. queue wait).

### Host-environment findings (2026-08-19, supersede fe56-era notes)

- Grid submission + RCDS publish + jobsub_q all WORK from this EAF pod
  (2026-07-11 firewall no longer applies). Whole campaign runs from EAF.
- Bearer-token storage scopes: write only to `/pnfs/dune/scratch/users/liangliu`;
  persistent is read-only via tokens. With a kinit ticket, `ssh dunegpvm04.fnal.gov`
  works (NFS /pnfs there) → persistent mirrors go through ssh.

## Stage 2 — vN seed (18 submissions)

Script: `.claude/plans/submit_g18_02a_e5000_vn_splines.sh` (written 2026-08-19).

- [x] 18/18 submitted 2026-08-19 19:22–19:23 UTC (stems
      `numu-numubar-nue-nuebar-nutau-nutaubar_{1000000010|H1|1000000010-H1}_20260819-192*`),
      all running by 19:2x. Persistent status monitor active in-session.
- [ ] wall times: CCDIS free-n xxx, CCDIS H1 xxx, NCDIS xxx, Charm xxx, others xxx
- [ ] pulled; merged `gxspl-vN-e5000.xml`: spline count xxx, sha256 xxx
- [ ] seed on persistent `/pnfs/dune/persistent/users/liangliu/genie_xsec/g18_02a_e5000/seed/`: sha256 match xxx

## Stage 3 — pilot (6–7 jobs)

- [ ] CCDIS C12 / W186: t = xxx / xxx
- [ ] Charm C12 / W186: t = xxx / xxx
- [ ] CCQE C12 / W186: t = xxx / xxx
- [ ] CCMEC C12 (optional): t = xxx
- [ ] band table for Stage 4 (chunk = min(6, floor(L/(1.5·t)))): xxx

## Stage 4 — full campaign (baseline 112 submissions)

Script: `.claude/plans/submit_g18_02a_e5000_splines.sh` (to be written from the
pilot band table).

- [ ] submissions xxx / done xxx / resubmits xxx

## Stage 5 — merge & validate

- [ ] ledger complete xxx
- [ ] `gxspl-G18_02a_00_000-e5000-n300.xml`: unique-key count xxx, sha256 xxx
- [ ] checklist 1–9: xxx
- [ ] gevgen smoke (Ar40/W186/H1): xxx

## Stage 6 — publish

- [ ] persistent dir + sha256s xxx
- [ ] CVMFS label `g18_02a_e5000_splines`: xxx
- [ ] run-manifest rebuilt xxx

## Deviations / notes

- 2026-08-19: plan doc quoted upstream commit `c233656e…` for R-3_06_02; the
  actual tag target is `4a6d9e5e50ed9ae72636dd363a2f3fbf672330a6` (verified from
  the clone). Plan value superseded.

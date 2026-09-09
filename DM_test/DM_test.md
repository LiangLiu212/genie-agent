# GENIE boosted-dark-matter (BDM) test — rc-v380 sample F preparation

**Date:** 2026-09-09 · **Host:** Fermilab EAF pod · **Repo:** `genie-dev` (branch `main`, nothing committed)
**Installation:** `genie_rc` = `/exp/dune/app/users/liangliu/GENIE/GENIE_RC` (GENIE-MC/Generator `rc-v380` @ `29238ed`, Pythia8-only)
**Goal:** make row F of the rc-v380 spline campaign runnable — tune `GDM18_00a_00_000`, target Ar40,
DM beam 0.1–10 GeV — and verify the whole `gmkspl_dm → gevgen_dm → gntpc` chain locally.
**Status:** tooling built and verified end to end. The campaign runs are **not launched**: the DM mass
(`xxx` below) has not been given. Decisions: local runs only (no grid, tarball `genie_rc` not
republished), one mass, mediator ratio `-z 0.5`, coupling `-g 1.0` (GENIE defaults), flat flux for
the gevgen_dm check.

> The smoke runs below use a **test mass of 1.0 GeV** (GENIE's own `gntpc` default,
> `gNtpConv.cxx:247`). It is a mechanical test value, not a physics choice, and all such runs are
> labelled `smoke_dm` / `smoke_dm_subthreshold` in the runlogs.

---

## 1. Findings that shaped the work (verified in `GENIE_RC/Generator/src`)

| Fact | Where |
|---|---|
| No installation had `gmkspl_dm` / `gevgen_dm`: all were configured without `--enable-boosted-dark-matter` | `configure:34,168,207`, `src/make/Make.config` |
| Tune `GDM18_00a` exists; `Default` list = DMEL + DMDIS + DME + DMRES; named lists DMEL/DMDIS/DME/DMRES/DM/DMHAD/DMNORES | `config/GDM18_00a/TuneGeneratorList.xml`, `config/EventGeneratorListAssembler.xml:388-433` |
| `gmkspl_dm -m masses -t pdgs -o xml [-z][-g][-n][-e] …` — no `-p`; probe is always PDG 2000010000 (`chi_dm`) | `src/Apps/gMakeSplinesDM.cxx` |
| `gevgen_dm -n -e E\|emin,emax -m M -t pdg [-z][-g][-f flux] …`; a range **without** `-f` silently runs at fixed E = emin | `src/Apps/gEvGenDM.cxx:683-712` |
| Spline keys are `dm;tgt:<pdg>;N:…;proc:…` — **no mass, ratio or coupling** | `Framework/Interaction/Interaction.cxx:258-266`, `Utils/XSecSplineList.cxx:541` |
| BDM defaults: `ZpCoupling 1.0` in `CommonParam.xml` `BoostedDarkMatter`; `-z` default 0.5 in the apps | `config/CommonParam.xml:276-282` |
| Enabling BDM is additive: no `__GENIE_BDM*` preprocessor use anywhere; only builds `libGPhBDMEG`/`libGPhBDMXS` + 3 apps | `Makefile:149-157`, `src/Apps/Makefile:74-78` |
| `gspl2root` has no `AddDarkMatter` → cannot read DM splines; `gntpc` hardcodes `AddDarkMatter(1.0,0.5)` for name lookup only | `src/Apps/gSplineXml2Root.cxx`, `src/Apps/gNtpConv.cxx:247` |
| On-the-fly spline signature: `XSecSplLst … CreateSpline` NOTICE lines; selection failures: `IntSel … Could not select interaction` | `Utils/XSecSplineList.cxx:162-176`, `EventGen/PhysInteractionSelector.cxx:201` |
| Upstream `rc-v380` moved on 2026-09-05 (PR #514, Pythia8 RNG seeding rework); no `R-3_08_00` tag exists | GitHub API |

---

## 2. What was changed

### GENIE install (in place)
- `GENIE_RC/build_genie.sh`: added `--enable-boosted-dark-matter \` to `./configure` (backup `build_genie.sh.bak-20260909`), re-run → `GENIE_RC/build_bdm.log`, `BUILD_OK` after **2 min 43 s** (14:45:11 → 14:47:54 UTC).
- New: `Generator/bin/{gmkspl_dm,gevgen_dm,gevgen_lardm}`, `Generator/lib/libGPhBDM{EG,XS}*.so`.
- Only `src/Physics/BoostedDarkMatter/{EventGen,XSection}` (35 `.o`) and `src/Apps` (21 `.o`) were compiled; the other **96 `.so` are untouched**.
- **Deviation from the plan:** every app was relinked against the BDM libs, so the sha256 of the
  standard binaries changed with no physics change (runlog `genie_bin_sha256` differs before/after 14:48 UTC):

  | binary | before | after |
  |---|---|---|
  | gevgen | `31ca4335c726dce1…` | `21bb322b9caaf3c2…` |
  | gmkspl | `e47d59b456fcce60…` | `be3c2a489bdeb3e0…` |
  | gntpc  | `74268f2f887b61f1…` | `3c7e0157b66a44d7…` |

- `genie-agent/config/env/genie_rc.json` re-snapshotted; `genie-agent/config/genie_env.json` → `installations.genie_rc._note` records the rebuild.

### genie-agent code
| File | Change |
|---|---|
| `shared/build_pdg.py` | `_SYNTHETIC_PROBES`: `dm` = 2000010000 (`chi_dm`, kind `dark_matter`, aliases `dm, chi_dm, darkmatter, dark_matter, bdm`), bypassing GENIE-table/PDG-API lookups |
| `shared/pdg.json` | regenerated (13 probes). Side effect: the PDG API moved 0.2.3 → 2026.0, so a few lepton/nucleon mass digits changed; nothing reads `mass_gev` at runtime |
| `genie-agent/lib/pdg.py` | `DARK_MATTER_PDGS` |
| `genie-agent/lib/validation.py` | `_DM_LISTS`, `_validate_dm_common`, `validate_gmkspl_dm_inputs`, `validate_gevgen_dm_inputs`; the neutrino validators now **error** on a DM probe and point at the DM scripts |
| `genie-agent/lib/jobs.py:342` | `outputs.spline_count` also recorded for `runtype == "gmkspl_dm"` |
| `genie-agent/scripts/run_gmkspl_dm.py` (new) | copy of `run_gmkspl.py` for `gmkspl_dm`: `--targets --mass --med-ratio --zp-coupling --tune(required) --genlist(Default) -n -e --seed --input-cross-sections …`; stem `dm_<target>_<ts>-<hex>`; runtype `gmkspl_dm` |
| `genie-agent/scripts/run_gevgen_dm.py` (new) | copy of `run_gevgen.py` for `gevgen_dm`: `--target --mass --med-ratio --zp-coupling -n -e 'E'|'emin,emax' --flux --cross-sections --tune(required) --genlist(Default) -r --seed …`; records `energy_min/energy_max/flux`, `outputs.flux_hist`; **cross-checks mass/z/g against the spline's sibling `gmkspl_dm` runlog** |
| `.claude/plans/merge_rc_v380_dm_splines.sh` (new) | local `gspladd` merge of the 4 per-process runs selected by `dm_mass/med_ratio/zp_coupling/n_knots/max_energy` from the runlogs → `gxspl-<T>-dm-m<m>-z<z>-g<g>-k<n>-e<E>.xml` + checks |

### Docs / notes
`genie-agent/README.md` (new DM section), `CLAUDE.md`, `.claude/skills/genie-runlog/SKILL.md`,
`.claude/skills/genie-install/SKILL.md`, `.claude/plans/refactor-genie-mcp-to-genie-agent.md`,
`.claude/plans/rc-v380-spline-set.md` (row F + "Sample F" section with the launch block),
`genie-agent/run-manifest.jsonl` (rebuilt: 927 runs, 8 DM records), memory notes.

---

## 3. Results

### Smoke chain (Ar40, GDM18_00a_00_000, test mass 1.0 GeV, z 0.5, g 1.0, `genie_rc`)

| Step | jobid | Result |
|---|---|---|
| `gmkspl_dm` DMEL, `-n 10 -e 10` | `gmkspl_dm-dm_Ar40_20260909-144948-8c8-089a94` | rc 0, 28.5 s, **2 splines** (`AhrensDMELPXSec/Velocity0/dm;tgt:1000180400;N:2112\|2212;proc:DarkMatter,DMEL`), GENIE enforces `nknots="30"` minimum |
| `job.py status <jobid>` | — | jobid with underscored runtype decodes; `runtype gmkspl_dm`, `returncode 0` |
| `gevgen_dm` mass 2.0 vs the 1.0 GeV spline | — | **refused**, exit 2: "dm_mass mismatch … spline keys carry no dm_mass" |
| `gevgen_dm` `-e 3,10` without `--flux` | — | **refused**, exit 2: "energy range given without --flux" |
| `gevgen_dm` `-e 2,10 --flux 1`, **wrong spline** (DME-only XML fed to a DMEL run, my `ls -t \| head -1` mistake) | `gevgen_dm-dm_Ar40_20260909-145149-817-7533f5` | rc **−6** after 2.6 s: `GEVGDriver.cxx:456 Assertion 'fUseSplines' failed` — in flux mode a missing spline aborts instead of being computed |
| `gevgen_dm` `-e 0.5,10 --flux 1`, 5 events (sub-threshold test, emin < mass) | `gevgen_dm-dm_Ar40_20260909-145310-b93-d9c79e` | rc 0, 1.8 s, **5/5 events**; throws with E < m get `px = -nan` and are rejected ("no-interaction probability 100 %"), next throw |
| `gevgen_dm` `-e 2,10 --flux 1`, 20 events, correct DMEL spline | `gevgen_dm-dm_Ar40_20260909-145422-c28-f7838c` | rc 0, 1.7 s, **2 splines loaded, 0 `CreateSpline`, 0 `Could not select interaction`, 20 GHEP entries**, `input-flux.root` written |
| `gntpc -f gst` on that GHEP | `gntpc-dm_Ar40_20260909-145422-c28.gst-3eb3a6` | rc 0, 20 gst entries, `neu` = 2000010000, `tgt` = 1000180400, Ev 2.49–9.25 GeV, Q² 0.006–0.415, gst `qel/res/dis/cc/nc` all 0 (expected for DM); gst log inherits `canonical_probe "dm"`, `tune_resolved GDM18_00a_00_000` |
| `gevgen_dm` fixed `-e 5`, 10 events | `gevgen_dm-dm_Ar40_20260909-145425-5c7-c0d02f` | rc 0, 1.2 s, 10 GHEP entries |

### Cost probes (Ar40, `-e 10`, 30 knots = GENIE minimum, background, label `smoke_dm`)

| list | jobid | wall | splines |
|---|---|---|---|
| DMEL  | `…-144948-8c8-089a94` | 28.5 s | 2 |
| DME   | `…-145135-3c9-4322ed` | 0.5 s | 1 |
| DMRES | `…-145135-44a-36b92e` | **2193 s (36.6 min)** | 34 |
| DMDIS | `…-145135-806-ceef91` | still running at 15:36 UTC (45 min): 66 knot evaluations, 3rd spline in progress, ~20 min per spline | – |

At 100 knots expect roughly 3.3× these: DMRES ≈ 2 h, DMDIS ≈ 1 h per spline × (number of DMDIS splines, not yet known), DMEL ≈ 1.5 min, DME seconds.

### Traps confirmed
1. **Spline keys carry no mass/ratio/coupling** → one XML per (m, z, g); the values live only in the runlog (`inputs.dm_mass/med_ratio/zp_coupling`) and must go into the product filename. `run_gevgen_dm.py` refuses a mismatch when a sibling `gmkspl_dm` log exists; merged products only get a warning.
2. **Flux mode aborts on a missing spline** (rc −6, `fUseSplines` assertion) instead of computing it on the fly — merged products must be complete.
3. **Flux throws below the mass are rejected, not fatal** — `-e 0.1,10` works for any mass > 0.1 GeV but wastes throws.
4. gevgen_dm's per-event marker is `Generated Event GHEP Record` (gevgen's differs); count events from the GHEP tree.
5. `gspl2root` cannot read DM splines; gst process flags are all 0 for DM events — read the process from the GHEP `Scattering : DMEL|DMDIS|DME|DMRES` line.

---

## 4. Commands used (in order)

All from `/exp/dune/data/users/liangliu/genie-dev` unless noted. `$R` = `/exp/dune/app/users/liangliu/GENIE/GENIE_RC`, `$G` = `$R/Generator`.

### 4.1 Reconnaissance (read-only)
```bash
# install state + upstream
cd $G && git status -sb && git log -1 --format='%h %ad %s' --date=short && cat VERSION
git fetch --tags origin; git tag | grep -iE '3_08|3\.8|380'; git branch -r | grep -iE 'v380|rc'
git rev-list --count HEAD..origin/rc-v380; git log -3 --format='%h %ad %s' --date=short origin/rc-v380
curl -sS -H 'Accept: application/vnd.github+json' 'https://api.github.com/repos/GENIE-MC/Generator/tags?per_page=20'
curl -sS -H 'Accept: application/vnd.github+json' 'https://api.github.com/repos/GENIE-MC/Generator/compare/29238ed97a99aff90c32390951b607185e59f1c5...rc-v380' -o cmp.json

# DM support in the install
ls -d $G/config/GDM*; ls $G/config/GDM18_00a; ls $G/bin | grep -i dm; ls $G/src/Apps | grep -i dm
grep -n -i 'DM' $G/config/EventGeneratorListAssembler.xml
grep -n -i 'dm\|dark' $G/configure | head; grep -n BOOSTED $G/src/make/Make.config
for d in GENIE_DEV GENIE_INCLXX GENIE_master GENIE_v3_6_2; do ls /exp/dune/app/users/liangliu/GENIE/$d/Generator/bin | grep -i dm; done
sed -n '1,140p' $G/src/Apps/gEvGenDM.cxx; sed -n '1,90p' $G/src/Apps/gMakeSplinesDM.cxx
sed -n '158,230p;420,432p' $G/src/Apps/gMakeSplinesDM.cxx; sed -n '695,760p' $G/src/Apps/gEvGenDM.cxx
sed -n '276,292p' $G/config/CommonParam.xml
grep -n -A12 'string XSecSplineList::BuildSplineKey' $G/src/Framework/Utils/XSecSplineList.cxx
sed -n '250,275p' $G/src/Framework/Interaction/Interaction.cxx; sed -n '408,440p' $G/src/Framework/Interaction/InitialState.cxx
grep -n 'AddDarkMatter' $G/src/Apps/gNtpConv.cxx $G/src/Apps/gSplineXml2Root.cxx
grep -n -B2 -A8 'physics-boosted-dark-matter:' $G/Makefile; grep -n -B2 -A6 'BOOSTED_DARK' $G/src/Apps/Makefile
grep -rl '__GENIE_BDM\|__GENIE_BOOSTED' $G/src --include=*.h --include=*.cxx
sed -n '580,590p;650,664p' $G/src/Framework/EventGen/GEVGDriver.cxx
awk '/void XSecSplineList::CreateSpline/,/^}/' $G/src/Framework/Utils/XSecSplineList.cxx | grep -n 'LOG\|<<'
grep -rn 'Could not select' $G/src/Framework/EventGen/*.cxx
grep -E '^=== ' $R/build.log        # previous build's timing
```

### 4.2 Rebuild `genie_rc` with BDM (clean shell, not inside pixi)
```bash
cd $R && sha256sum Generator/bin/gevgen Generator/bin/gmkspl Generator/bin/gntpc > bin_sha_before.txt
cp build_genie.sh build_genie.sh.bak-20260909
sed -i 's|^    --enable-pythia8 \\$|    --enable-pythia8 \\\n    --enable-boosted-dark-matter \\|' build_genie.sh
# (+ a 3-line header comment inserted before "# Run in a clean shell (NOT inside pixi).")
sed -n '/^\.\/configure/,/libxml2"$/p' build_genie.sh      # confirm the flag is in the configure block

cd $R && env -i HOME="$HOME" USER="$USER" PATH=/usr/local/bin:/usr/bin:/bin TERM=dumb \
    bash --noprofile --norc ./build_genie.sh > build_bdm.log 2>&1        # ~2 min 43 s

# verify
grep -E '^=== ' build_bdm.log | tail -6; grep -c -i error build_bdm.log
ls -la Generator/bin | grep -i dm; ls Generator/lib | grep -i bdm; grep BOOSTED Generator/src/make/Make.config
sha256sum Generator/bin/gevgen Generator/bin/gmkspl Generator/bin/gntpc | diff bin_sha_before.txt -   # CHANGED (relink)
find Generator/src -name '*.o' -newer build_genie.sh.bak-20260909 | sed 's|/[^/]*\.o$||' | sort | uniq -c
find Generator/lib -name '*.so' -newer build_genie.sh.bak-20260909; find Generator/lib -name '*.so' ! -newer build_genie.sh.bak-20260909 | wc -l   # 96 untouched
env -i HOME="$HOME" USER="$USER" PATH=/usr/local/bin:/usr/bin:/bin bash --noprofile --norc -c \
  "source $R/setup_env.sh >/dev/null 2>&1 && gmkspl_dm -h | head -5; ldd \$(which gevgen_dm) | grep -i -E 'BDM|pythia8|not found'; ldd \$(which gevgen) | grep -c BDM"
```

### 4.3 genie-agent code changes
```bash
# inline Python patch script (exact-string replacements, asserted unique) applied to:
#   shared/build_pdg.py  genie-agent/lib/pdg.py  genie-agent/lib/jobs.py  genie-agent/lib/validation.py
# new files written with heredocs:
#   genie-agent/scripts/run_gmkspl_dm.py  genie-agent/scripts/run_gevgen_dm.py  .claude/plans/merge_rc_v380_dm_splines.sh
pixi run python shared/build_pdg.py                       # regenerate shared/pdg.json (13 probes)
git diff --stat shared/pdg.json; git diff shared/pdg.json | grep '^[-+]' | head -40
chmod +x genie-agent/scripts/run_gmkspl_dm.py genie-agent/scripts/run_gevgen_dm.py .claude/plans/merge_rc_v380_dm_splines.sh
pixi run python -m py_compile genie-agent/scripts/run_gmkspl_dm.py genie-agent/scripts/run_gevgen_dm.py
bash -n .claude/plans/merge_rc_v380_dm_splines.sh

# unit-style checks of the alias + validators (inline Python via pixi):
#   resolve_pdg('dm')==2000010000, resolve_pdg('chi_dm'), canonical_probe(2000010000)=='dm', DARK_MATTER_PDGS=={2000010000}
#   validate_gmkspl_dm_inputs / validate_gevgen_dm_inputs with good and bad inputs; DM-probe guards in the neutrino validators

pixi run python genie-agent/scripts/refresh_genie_env.py --installation genie_rc
# inline Python: append the rebuild note to installations.genie_rc._note in genie-agent/config/genie_env.json
pixi run python -c "import sys; sys.path.insert(0,'genie-agent'); from lib.config import load_config; print(load_config('genie_rc')['genie_bin_dir'])"
```

### 4.4 Smoke runs (test mass 1.0 GeV)
```bash
# spline: DMEL, 10 knots requested (GENIE uses 30), Emax 10 GeV, foreground
pixi run python genie-agent/scripts/run_gmkspl_dm.py --installation genie_rc --targets Ar40 --mass 1.0 \
    --tune GDM18_00a_00_000 --genlist DMEL -n 10 -e 10 --label smoke_dm --foreground
L=genie-agent/genie-runs/GDM18_00a_00_000-2026-09-09/dm_Ar40_20260909-144948-8c8.log
jq '{jobid,returncode,duration_s,spline_count:.outputs.spline_count,cmd:.outputs.genie_command}' $L
X=${L%.log}.xml; grep -o 'spline name="[^"]*"' $X; grep -c '<spline ' $X; grep -o 'nknots="[0-9]*"' $X | sort -u
pixi run python genie-agent/scripts/job.py status gmkspl_dm-dm_Ar40_20260909-144948-8c8-089a94

# negative tests (both exit 2 before any GENIE run)
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 2.0 -n 5 -e 3,10 --flux 1 \
    --cross-sections $X --tune GDM18_00a_00_000 --genlist DMEL --foreground        # dm_mass mismatch
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 1.0 -n 5 -e 3,10 \
    --cross-sections $X --tune GDM18_00a_00_000 --genlist DMEL --foreground        # range without --flux

# cost probes, background (default), label smoke_dm
for gl in DMDIS DMRES DME; do
  pixi run python genie-agent/scripts/run_gmkspl_dm.py --installation genie_rc --targets Ar40 --mass 1.0 \
      --tune GDM18_00a_00_000 --genlist $gl -n 10 -e 10 --label smoke_dm
done
pixi run python genie-agent/scripts/job.py list --active

# MISTAKE (kept for the record): `ls -t …/dm_Ar40_*.xml | head -1` picked the just-finished DME XML,
# so this DMEL run had no DMEL spline and aborted (rc -6, fUseSplines assertion):
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 1.0 -n 20 -e 2,10 --flux 1 \
    --cross-sections genie-agent/genie-runs/GDM18_00a_00_000-2026-09-09/dm_Ar40_20260909-145135-3c9.xml \
    --tune GDM18_00a_00_000 --genlist DMEL --label smoke_dm --foreground

# sub-threshold test: flux range starting below the mass (hard 240 s timeout)
timeout 240 pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 1.0 -n 5 -e 0.5,10 --flux 1 \
    --cross-sections $X --tune GDM18_00a_00_000 --genlist DMEL --label smoke_dm_subthreshold --foreground

# corrected flux-mode smoke with the DMEL spline, then gntpc, then fixed-energy mode
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 1.0 -n 20 -e 2,10 --flux 1 \
    --cross-sections $X --tune GDM18_00a_00_000 --genlist DMEL --label smoke_dm --foreground
G=genie-agent/genie-runs/GDM18_00a_00_000-2026-09-09/dm_Ar40_20260909-145422-c28.ghep.root; S=${G%.ghep.root}.stdout
echo "Loading spline: $(grep -c 'Loading spline:' $S)  CreateSpline: $(grep -c CreateSpline $S)  CouldNotSelect: $(grep -c 'Could not select interaction' $S)"
pixi run python -c "import uproot,sys; print(uproot.open(sys.argv[1])['gtree'].num_entries)" $G
pixi run python genie-agent/scripts/run_gntpc.py --installation genie_rc -i $G -f gst --foreground
jq '{jobid,returncode,probe:.inputs.canonical_probe,tune:.inputs.tune_resolved,src:.inputs.source_jobid}' ${G%.ghep.root}.gst.log
# inline Python (uproot): gst entries, neu/tgt sets, Ev min/max, qel/res/dis/cc/nc sums, Q2 range
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass 1.0 -n 10 -e 5 \
    --cross-sections $X --tune GDM18_00a_00_000 --genlist DMEL --label smoke_dm --foreground

# per-event process line and event marker in gevgen_dm stdout
grep -c 'Generated Event GHEP Record' $S; grep -o 'Scattering *:.*' $S | sort | uniq -c
```

### 4.5 Bookkeeping
```bash
pixi run python genie-agent/scripts/build_run_manifest.py            # 927 runs, 8 DM records
grep -o '"runtype": "[a-z_]*"' genie-agent/run-manifest.jsonl | sort | uniq -c
# inline Python patches: genie-agent/README.md, CLAUDE.md, .claude/skills/genie-runlog/SKILL.md,
#   .claude/skills/genie-install/SKILL.md, .claude/plans/refactor-genie-mcp-to-genie-agent.md (append),
#   .claude/plans/rc-v380-spline-set.md (row F + "Sample F" section), memory notes + MEMORY.md
# poll the DM runlogs
for l in genie-agent/genie-runs/GDM18_00a_00_000-2026-09-09/*.log; do
  jq -r 'select(.runtype=="gmkspl_dm") | [.jobid,.inputs.genlist_resolved,(.running|tostring),(.returncode|tostring),(.duration_s|tostring),((.outputs.spline_count//"-")|tostring)] | @tsv' "$l"
done | column -t
git status --short; git diff --stat
```

---

## 5. Artefacts

- Runs: `genie-agent/genie-runs/GDM18_00a_00_000-2026-09-09/dm_Ar40_*.{xml,ghep.root,gst.root,log,stdout,stderr}` + `input-flux.root`
- Build log: `$R/build_bdm.log`; backup `$R/build_genie.sh.bak-20260909`
- Plan: `~/.claude/plans/give-me-a-plan-encapsulated-wind.md`
- Campaign log: `.claude/plans/rc-v380-spline-set.md` ("Sample F — preparation done 2026-09-09")

## 6. Next step — launch sample F once the DM mass is known

```bash
for gl in DMEL DMDIS DME DMRES; do
  pixi run python genie-agent/scripts/run_gmkspl_dm.py --installation genie_rc --targets Ar40 \
      --mass xxx --tune GDM18_00a_00_000 --genlist $gl -n 100 -e 10 --label rc_v380_splines
done
pixi run python genie-agent/scripts/job.py list --active
.claude/plans/merge_rc_v380_dm_splines.sh --mass xxx     # -> runarea/genie_xsec/rc-v380/GDM18_00a_00_000/gxspl-Ar40-dm-mxxx-z0.5-g1.0-k100-e10.xml
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass xxx \
    -n 200 -e 0.1,10 --flux 1 --cross-sections <merged.xml> --tune GDM18_00a_00_000 --genlist Default --foreground
# checks: grep -c 'Loading spline:' == merged count; grep -c CreateSpline == 0; grep -c 'Could not select interaction' == 0;
#         GHEP entries == 200; run_gntpc.py -f gst; build_run_manifest.py; mirror_rc_v380_splines.sh --go; sha256 into the campaign table
```
Not done on purpose: grid tarball republish (`tarball.py … --label genie_rc --overwrite`), any commit.

---

## 7. Mass scan — 10 masses × 4 lists, Emax 1000 GeV, 100 knots (launched 2026-09-09 18:07 UTC)

**Request:** spline energy range 0 → 1000 GeV, DM mass 1 → 900 GeV in 10 steps.
**Decisions:** masses **1, 100, 200, …, 900 GeV** (10 values); `-n 100` knots; per-process lists
(DMEL/DMDIS/DME/DMRES) merged per mass; Ar40, tune `GDM18_00a_00_000`, `-z 0.5 -g 1.0`; label
`dm_scan_e1000`. One job and one XML **per mass** is mandatory: the spline key carries no mass and
`GEVGDriver::CreateSplines` skips a key that already exists, so a multi-mass `-m m1,m2,…` call would
only compute the first mass.

**Pre-checks (source):** the default validity context is `GVLD-Emin 0.010 / GVLD-Emax 1000`
(`config/CommonParam.xml:333-334`, used because the DM generators have an empty `VldContext`),
so `-e 1000` is exactly the allowed maximum and a 900 GeV threshold still fits. Probe at m = 900,
`-e 1000`, min knots: DMEL 2 splines (threshold 900 GeV), DME 1 spline — rc 0.

**Launch (as run):**
```bash
for m in 1 100 200 300 400 500 600 700 800 900; do
  for gl in DMEL DMDIS DME DMRES; do
    pixi run python genie-agent/scripts/run_gmkspl_dm.py --installation genie_rc --targets Ar40 \
        --mass $m --tune GDM18_00a_00_000 --genlist $gl -n 100 -e 1000 --label dm_scan_e1000
  done
done
```
Jobids: `DM_test/dm_mass_scan_e1000_jobs.tsv` (mass, list, jobid, log). 40 launched, 0 failed.

**Status at 18:12 UTC** (poll with the loop in §4.5 or `job.py list --active`):

| list | done | result |
|---|---|---|
| DMEL | all 10 masses | 2 splines each, 100 knots spanning 0.01–1000 GeV, non-zero from the threshold (m = 1: first non-zero knot 1.08 GeV, σ(9.8 GeV) = 0.359 ×10⁻³⁸ cm², matching the smoke run; m = 900: non-zero from 901 GeV, max 3×10⁻¹¹) |
| DME | all 10 masses | 1 spline each (m = 1: 60 non-zero knots from 1.05 GeV, falls to 0 at high E) |
| DMRES | m ≥ 500 done in ~1 s, m ≤ 400 running | **m ≥ 500: all 34 splines are identically zero** — `DMRESXSecFast` caches its resonance cross section only up to `ESplineMax` = 500 GeV (`config/DMRESXSec.xml:12`; `DMRESXSecFast.cxx:155,218`), so a threshold at/above 500 GeV gets nothing. For m ≤ 400 the DMRES cross section is **frozen at its 499 GeV value** between 500 and 1000 GeV. |
| DMDIS | all 10 running | at 30 knots the smoke probe is still running after 3.5 h (14+ splines); expect > 11 h per mass at 100 knots |

**Caveat to decide:** if resonance production is wanted above 500 GeV, `ESplineMax` must be
raised (e.g. 1000) in a copy of `DMRESXSec.xml` placed in a `--gxmlpath` overlay dir, and the
DMRES jobs re-run for every mass (that change is not in the tune family dir, so it shows up in the
runlog only as `inputs.gxmlpath`). Not done.

**Merge, once the DMDIS/DMRES jobs of a mass are finished** (one product per mass):
```bash
for m in 1 100 200 300 400 500 600 700 800 900; do
  .claude/plans/merge_rc_v380_dm_splines.sh --mass $m --emax 1000 --knots 100 --label dm_scan_e1000
done
# -> /exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380/GDM18_00a_00_000/gxspl-Ar40-dm-m<m>-z0.5-g1.0-k100-e1000.xml
```
The script refuses to merge a mass whose four lists are not all finished with rc 0 and > 0 splines.
Note: the zero DMRES files for m ≥ 500 **do** count as "> 0 splines" (34 entries, all zero), so
those merges will go through with an empty resonance contribution.

**Events from a merged file** (flux range must stay above the mass to avoid wasted throws):
```bash
pixi run python genie-agent/scripts/run_gevgen_dm.py --installation genie_rc --target Ar40 --mass <m> \
    -n 1000 -e <m>,1000 --flux 1 --cross-sections <merged.xml> --tune GDM18_00a_00_000 --genlist Default
```

### Merged products (2026-09-09 20:3x UTC), `runarea/genie_xsec/rc-v380/GDM18_00a_00_000/`

| mass (GeV) | file | splines | sha256 |
|---|---|---|---|
| 100 | `gxspl-Ar40-dm-m100-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `100]   sha256` |
| 200 | `gxspl-Ar40-dm-m200-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `200]   sha256` |
| 300 | `gxspl-Ar40-dm-m300-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `300]   sha256` |
| 400 | `gxspl-Ar40-dm-m400-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `400]   sha256` |
| 500 | `gxspl-Ar40-dm-m500-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `500]   sha256` |
| 600 | `gxspl-Ar40-dm-m600-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `600]   sha256` |
| 700 | `gxspl-Ar40-dm-m700-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `700]   sha256` |
| 800 | `gxspl-Ar40-dm-m800-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `800]   sha256` |
| 900 | `gxspl-Ar40-dm-m900-z0.5-g1.0-k100-e1000.xml` | 53 (2 DMEL + 16 DMDIS + 1 DME + 34 DMRES) | `900]   sha256` |

Each: 0 duplicate keys, nknots 100, one `genie_tune` section, spline count equal to the sum of the four
inputs (merge log `DM_test/merge_dm_scan_e1000.log`, staging `work/Ar40-dm-m<m>-z0.5-g1.0/`). m = 1 waits
for its DMDIS job. **Bug fixed on the way:** `merge_rc_v380_dm_splines.sh` used `--arg label`, and `label`
is a jq reserved word, so the selector never compiled and every list was reported MISSING; renamed to
`$lbl` (uncommitted). For m ≥ 500 the 34 DMRES splines in the product are all zero (§7 caveat).

### Spline plots (2026-09-09 20:4x UTC)

Generator `results/template/plot_dm_splines.py` (house style, parses the XML directly since
`gspl2root` cannot read DM splines; XML GeV⁻² → 10⁻³⁸ cm² with ×3.89379×10¹⁰; each process is the
sum of its splines on the union of their knots, so the dots are real knots). Re-run after the
m = 1 DMDIS job finishes:
```bash
pixi run python results/template/plot_dm_splines.py --label dm_scan_e1000 --out-dir DM_test
```
- `DM_test/dm_splines_dm_scan_e1000_per_mass.png` — one panel per mass, DMEL/DMDIS/DME/DMRES/Total,
  **linear x, log y** (the chosen look, 2026-09-09; shared y, floor 10⁻¹² for zeros)
- `DM_test/dm_splines_dm_scan_e1000_per_process.png` — one panel per process, one line per mass, same axes
- `DM_test/dm_splines_dm_scan_e1000_log_*.png` — log-log (`--logx --logy`);
  `DM_test/dm_splines_dm_scan_e1000_lin_*.png` — both linear (`--linear`, independent y ranges)
- `DM_test/dm_splines_dm_scan_e1000.txt` — readout: threshold, σ_max, σ at 10/100/1000 GeV per (mass, process)

What the numbers say (σ in 10⁻³⁸ cm², Ar40, z = 0.5, g = 1.0):
- m = 1 GeV (DMDIS still pending): DMEL 2.5×10¹⁰ plateau, DMRES 3.7×10¹¹, DME rising to 1.5×10¹¹ at
  1 TeV, total ≈ 5×10¹¹ = 5×10⁻²⁷ cm² — millibarn-scale, i.e. the GENIE default coupling g = 1 is not
  a weak-scale choice; scale g down if physical rates are wanted.
- m = 100 → 900 GeV: total at 1 TeV falls 1.3×10⁶ → 3.1, dominated by DMDIS (DMEL ≤ 10³,
  DMRES 2×10⁴ at m = 100 and ≤ 0.15 for m = 400 because of the 500 GeV cache; zero for m ≥ 500).
- **DME artefact:** the DM–electron spline carries small *negative* values below its threshold
  (m = 100: −0.014 at 10 GeV) and is negative at every knot for m ≥ 600 (≈ −10⁻⁶ … −10⁻⁵),
  i.e. numerical noise of the `DMElectronPXSec` integration. Harmless where other processes are
  non-zero (10⁶ larger) but note that GENIE will happily load them; they show as floored points.

---

## 8. 10k-event samples per mass (2026-09-09 21:34–21:45 UTC)

**Request:** 10 000 `gevgen_dm` events for each mass point of the scan. **Assumptions:** flat flux
(`--flux 1`) from the DM mass up to the top of the spline, `--genlist Default`, `-z 0.5 -g 1.0`,
label `dm_scan_e1000`, background jobs. Jobids in `DM_test/dm_mass_scan_e1000_events.tsv`; per-run
checks in `DM_test/dm_mass_scan_e1000_events_summary.tsv`; process mix in
`DM_test/dm_mass_scan_e1000_process_mix.tsv`. m = 1 waits for its DMDIS spline (last of 16 at 21:34 UTC).

### Two failure modes met on the way (both now guarded in `run_gevgen_dm.py`)

1. **Flux top edge = spline Emax** (`-e m,1000` against `-e 1000` splines): 8 of 9 jobs aborted at
   start with `GMCJDriver.cxx:649 Assertion fEmax<rE.max && fEmax>rE.min` (rc −6); m = 200 slipped
   through by a float hair and finished. Same class as the gevgen "generate strictly inside the
   spline range" gotcha. Runner now reads the largest knot of the spline XML and refuses a fixed
   energy or flux upper edge that is not strictly below it (verified: `-e 100,1000` → exit 2).
2. **Flux starting at the threshold** (`-e m,999`): 7 of 8 relaunched jobs aborted after 126–6289
   events with `PhysInteractionSelector.cxx:188 Assertion xsec>0` (rc −6). Reproduced bit-for-bit
   with the logged seed (m = 600, seed 413164798, unbuffered stdout): the failing flux particle has
   E = 602.18 GeV, i.e. between the threshold knot (600) and the second knot (603.3). Mechanism,
   from `PhysInteractionSelector::SelectInteraction`: for E below a spline's second knot the
   selector sets that channel's xsec to 0 (`ClosestKnotValueIsZero`), so all hadronic channels are
   0 there while the DM–electron spline is slightly **negative** (§7); the line
   `TMath::Max(0., xsec);` discards its result (GENIE bug: the clamp is never applied), the sum is
   negative, `R = sum × rnd < 0`, the first channel (xsec 0) is "selected" and the assert fires.
   GMCJDriver still throws interactions there because its summed spline interpolates to > 0 between
   the zero knot and the second knot. **Worth reporting upstream for rc-v380.** Work-around used:
   start the flux at **1.03 m** (above the second knot for every mass; for m = 100 and 200 the
   original runs from m had already survived and were kept).

### Result: 9 × 10 000 events, all rc 0, 0 on-the-fly splines, 0 selection failures, gst + rootracker written

| m [GeV] | flux range [GeV] | wall [s] | events | DMEL | DMDIS | DME | DMRES | ⟨σ_evt⟩ [10⁻³⁸ cm²] |
|---|---|---|---|---|---|---|---|---|
| 100 | 100,999 | 65.593 | 10000 | 26 | 9614 | 0 | 360 | 1.729e+05 |
| 200 | 200,1000 | 68.215 | 10000 | 135 | 8717 | 0 | 1148 | 3295 |
| 300 | 309,999 | 50.987 | 10000 | 360 | 8928 | 0 | 712 | 351.1 |
| 400 | 412,999 | 42.595 | 10000 | 822 | 9170 | 0 | 8 | 75.54 |
| 500 | 515,999 | 45.76 | 10000 | 1456 | 8544 | 0 | 0 | 21.47 |
| 600 | 618,999 | 43.732 | 10000 | 2623 | 7377 | 0 | 0 | 7.4 |
| 700 | 721,999 | 50.206 | 10000 | 4646 | 5354 | 0 | 0 | 2.715 |
| 800 | 824,999 | 53.218 | 10000 | 7483 | 2517 | 0 | 0 | 1.066 |
| 900 | 927,999 | 48.21 | 10000 | 9935 | 65 | 0 | 0 | 0.7687 |

Process mix from the rootracker `EvtCode` (gst has no DM process flags): DMDIS dominates up to
m ≈ 700 GeV, DMEL takes over above because DMDIS closes towards the 1 TeV edge; DMRES follows the
spline caveat (8 events at m = 400, none from 500 on); DME never fires (its σ is ≤ 10⁻⁶ of the
total, and negative where the hadronic channels are off). `input-flux.root` in the run dir is
written by every flux-mode run of the day (last writer wins) — bookkeeping only.

---

## 9. DME-only samples (DM–electron elastic), 2026-09-09 21:48–21:50 UTC

**Request:** generate only DME events. Done with `--genlist DME` against each mass's own DME spline
file from the scan (sibling `gmkspl_dm` log, so the provenance check passes), 10 000 events, flat
flux, label `dm_scan_e1000_DME`. Jobids: `DM_test/dm_mass_scan_e1000_DME_events.tsv`; checks:
`DM_test/dm_mass_scan_e1000_DME_summary.tsv`.

**Flux window per mass.** The DME spline is *negative* below its physical onset (§7), and GENIE's
selector would then pick a channel with σ ≤ 0 and abort (same assertion as in §8), so the flux
starts 1 % above the spline's **second positive knot** (m = 500: the only positive knots are 890 and
1000 GeV, so its window is 900–999 GeV). For **m ≥ 600 GeV the DME spline has no positive knot at
all → no DME events can be generated** with this build/config (4 masses skipped).

| m [GeV] | flux [GeV] | wall [s] | events | all DME | ⟨σ_evt⟩ [10⁻³⁸ cm²] | E_DM of events [GeV] |
|---|---|---|---|---|---|---|
| 1 | 1.18858,999 | 21.054 | 10000 | yes | 1.181e+11 | 14.83–998.8 |
| 100 | 139.874,999 | 24.898 | 10000 | yes | 0.8184 | 140.41–998.9 |
| 200 | 281.039,999 | 18.115 | 10000 | yes | 0.01168 | 281.39–999.0 |
| 300 | 502.679,999 | 21.061 | 10000 | yes | 0.0008863 | 502.99–999.0 |
| 400 | 712.535,999 | 18.588 | 10000 | yes | 0.0001212 | 712.59–999.0 |
| 500 | 900,999 | 11.818 | 10000 | yes | 1.758e-05 | 900.01–999.0 |

Notes: the m = 1 sample starts at 14.8 GeV although the flux began at 1.19 GeV — the DME cross
section rises steeply with E (10⁸ at 10 GeV vs 1.5×10¹¹ at 1 TeV), so low-energy throws rarely
interact. **gntpc `-f gst` cannot convert DME events**: `gNtpConv.cxx:665 ConvertToGST()` asserts
on the process type (DM–electron scattering has no hit nucleon and is not in its allowed list), rc −6;
`-f rootracker` works and carries the process in `EvtCode` — use that for DME samples.

---

## 10. DME recoil electron: (T_e, θ_e) per mass (2026-09-09 ~22:00 UTC)

Generator `results/template/plot_dme_recoil.py` (reads the rootracker files of §9: incoming DM =
StdHep entry 0, recoil electron = the status-1 e⁻; T_e = E_e − m_e, θ_e = angle to the DM
direction). Figure `DM_test/dme_recoil_Te_theta.png` (one log–log 2D panel per mass, colour =
events/bin), histdiag readouts `DM_test/dme_recoil_Te_theta.txt` (1D projections + 2D map, ridge,
profiles), band check `DM_test/dme_recoil_band_check.txt`.

Overlaid two-body relation cos θ_e = (E + m_e)/p · √(T_e/(T_e + 2m_e)) at the two flux edges: at a
given T_e the angle grows with E, so the E = 999 GeV curve is the upper edge of the band and the
E = E_min curve the lower one; every sample lies inside (see band check). Kinematic recoil limit
T_e,max = 2 m_e p²/(m² + m_e² + 2 m_e E).

| m [GeV] | T_e median | T_e max (kin. max at 999 GeV) | θ_e median | θ_e 5–95 % |
|---|---|---|---|---|
| 1 | 73096.991 MeV | 496685.523 MeV (504683.812) | 0.16° | 0.04°–0.78° |
| 100 | 29.629 MeV | 98.727 MeV (100.963) | 6.71° | 1.72°–27.19° |
| 200 | 7.445 MeV | 23.208 MeV (24.476) | 13.15° | 4.35°–36.84° |
| 300 | 3.365 MeV | 9.289 MeV (10.311) | 18.77° | 8.25°–39.07° |
| 400 | 1.962 MeV | 4.314 MeV (5.353) | 23.77° | 13.70°–37.55° |
| 500 | 1.353 MeV | 2.051 MeV (3.058) | 27.27° | 21.23°–34.30° |

Reading: for a light DM (m = 1) the electron takes up to half the DM energy (T_e up to ~500 GeV) and
is emitted within a fraction of a degree — the textbook boosted-DM electron signature. For heavy
DM the recoil is capped at 2 m_e p²/m² ≈ MeV (101 MeV at m = 100, 3 MeV at m = 500) and comes out at
tens of degrees, i.e. a low-energy, wide-angle electron that no longer points back to the source.
The band width is the flux range; at fixed T_e the pair (T_e, θ_e) fixes E for an assumed m.

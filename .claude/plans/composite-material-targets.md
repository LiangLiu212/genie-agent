# Plan: composite-material targets (`--target CH`) for gmkspl/gevgen

## Context

The MINERvA wiki page (`wiki/experiment/minerva.md`, source 2503.15047) measures
ν_μ CCQE-like on **CH scintillator** alongside C/H₂O/Fe/Pb. Today the runners
only accept a *single* nucleus: `--target` → `resolve_pdg` → one PDG code. CH is
a composite (polystyrene, ≈1:1 C:H atom ratio), so it cannot be run.

GENIE handles composites natively via a **target mix** on `-t`:
`code1[w1],code2[w2],…`. Two facts were verified from the GENIE source in this
install (`…/GENIE_DEV/Generator`):

1. **Weight convention = mass fraction.** `GMCJDriver::InteractionProbability`
   computes `P = N_A · xsec · pL / A` — it divides the bracket weight (`pL`,
   gr/cm²) by mass number `A` to get atom column density. So bracket weights are
   **mass-type**; to encode an atom ratio they must be **mass fractions**. The
   `gevgen` help text ("weight fractions", e.g. `O16[0.95],H[0.05]`) agrees.
2. **Mono-energetic + target mix works in this build.** `-t` sets
   `gOptUsingFluxOrTgtMix`; with no energy range, `FluxDriver()` returns
   `MonoEnergeticFluxDriver()`. `__CAN_GENERATE_EVENTS_USING_A_FLUX_OR_TGTMIX__`
   is defined (flux/geom drivers enabled). A live run parsed
   `1000060120[0.9225],1000010010[0.0775]` and proceeded to generation.

`gmkspl -t` already takes a comma-separated nuclide list (no weights) — the grid
`gmkspl` path is already multi-target.

**Goal:** add a curated materials database and let `--target <material>` (CH,
H₂O, CH₂, …) drive both gmkspl (spline over all constituent nuclides) and gevgen
(mono-energetic target mix), in **both** the local genie-agent runners and the
jobsub-agent grid adapters. Composition uses **G4-NIST element mass fractions**
expanded to a **natural isotopic mix**.

## Data model: new `shared/material.json` + `shared/build_material.py`

Mirror the existing `shared/pdg.json` + `shared/build_pdg.py` split (build-time
enrich, runtime read-only).

`shared/build_material.py` (build-time, like `build_pdg.py`):
- Input: a small **curated** table of materials → element mass fractions, with
  G4 names + densities + NIST citations, hand-entered in the script
  (G4_POLYSTYRENE: C 0.922582 / H 0.077418; G4_WATER: H 0.111894 / O 0.888106;
  plus CH₂/G4_POLYETHYLENE). Source of truth = NIST/Geant4 `G4_*` materials.
- Expand each element → **natural isotopes** using GENIE's
  `data/evgen/catalogues/iso/natural-isotopes.data` (already the kind of GENIE
  data file `build_pdg.py` reads; located via `$GENIE` from the loaded env, with
  a `--isotopes` override). For element E with mass fraction `w_E`, each isotope
  i gets material mass fraction `w_E · (a_i·A_i / Σ_j a_j·A_j)` where `a` =
  natural abundance, `A` = atomic mass (both columns in that file).
- Output `shared/material.json`:
  ```json
  {"_comment":"…","generated":"…","sources":["Geant4 G4_* NIST","GENIE natural-isotopes.data"],
   "materials":{
     "CH":{"canonical":"CH","aliases":["ch","scintillator","polystyrene","g4_polystyrene"],
           "g4_name":"G4_POLYSTYRENE","density_g_cm3":1.06,
           "elements":[{"symbol":"C","Z":6,"mass_fraction":0.922582,"source":"G4_POLYSTYRENE"},
                       {"symbol":"H","Z":1,"mass_fraction":0.077418,"source":"G4_POLYSTYRENE"}],
           "nuclides":[{"pdg":1000060120,"name":"C12","mass_fraction":0.9127…},
                       {"pdg":1000060130,"name":"C13","mass_fraction":0.0099…},
                       {"pdg":1000010010,"name":"H1","mass_fraction":0.0774…},
                       {"pdg":1000010020,"name":"H2","mass_fraction":8.9e-06}]}}}
  ```
  `elements` is the human-auditable curated input; `nuclides` is the build-time
  expansion the runners actually consume.
- Add `pixi.toml` note (build-time only) — no new runtime dep; reuse the `pdg`
  comment style. `periodictable` is **not** required (abundances come from
  GENIE's file).

## Shared resolver: `genie-agent/lib/pdg.py` + `jobsub-agent/adapters/genie/pdg.py`

Both files are kept byte-equivalent (only `_REPO_ROOT` depth differs) — edit
both identically. Add:
- Load `shared/material.json` next to the existing `pdg.json` load.
- `MATERIAL_ALIASES: dict[str,str]` (lowercased alias → canonical).
- `resolve_material(value) -> dict | None`: return the material entry if `value`
  matches an alias (case-insensitive), else `None`. Single nucleus / PDG inputs
  return `None` (they stay on the existing `resolve_pdg` path).
- `material_mix_arg(mat) -> str`: `",".join(f"{n['pdg']}[{n['mass_fraction']:.6g}]")`.
- `material_nuclide_pdgs(mat) -> list[int]`.
- `canonical_target` unchanged; the material canonical (e.g. `"CH"`) is taken
  straight from the entry for filename stems.

## Local runners

**`genie-agent/scripts/run_gevgen.py`** (single target → optional mix):
- After parsing, branch: `mat = resolve_material(args.target)`.
  - material: `target_arg = material_mix_arg(mat)`, `canon_target =
    mat["canonical"]`, `nuclide_pdgs = material_nuclide_pdgs(mat)`.
  - else (unchanged): `target_pdg = resolve_pdg(...)`,
    `target_arg = str(target_pdg)`, `canon_target = canonical_target(...)`,
    `nuclide_pdgs = [target_pdg]`.
- `cmd` uses `"-t", target_arg`.
- `inputs`: replace `target_pdg` with `target` (the `-t` string) and add
  `target_nuclides: nuclide_pdgs` + `material: mat["canonical"] or None` so the
  runlog records the mix.
- Validation: call `validate_gevgen_inputs` once per nuclide in `nuclide_pdgs`
  (or pass the list — see validation change).

**`genie-agent/scripts/run_gmkspl.py`** (list → expand materials):
- After resolving `target_aliases`, expand: for each alias, if
  `resolve_material` matches, extend with its nuclide PDGs and use its canonical
  for the label; else `resolve_pdg` as today. **Dedup** nuclide PDGs preserving
  order (a CH + explicit C12 job must not list C12 twice).
- `canonical_targets` for the stem: material canonical where matched, else
  `canonical_target`.
- `cmd -t` = comma-joined deduped nuclide PDGs (already the existing shape).

## Validation: `genie-agent/lib/validation.py`

- `validate_gevgen_inputs`: accept `tgt_pdgs: list[int]` instead of a single
  `tgt_pdg` (callers updated), validate each is a bare nucleon or nuclear PDG.
  Keeps the free-H caveat relevant: warn (not error) if a **mix** contains H1
  with a neutrino + CCQE genlist, since νμ CCQE can't occur on free H (no bound
  neutron) — advisory only.
- `validate_gmkspl_inputs` already loops `tgt_pdgs`; no signature change.

## Grid adapters (jobsub-agent)

Mirror the local logic; the extra concern is the **shell template + filename**.

**`adapters/genie/run_gevgen_grid.py`**:
- Same material branch as local. Pass the mix string as the `-t` worker arg
  (`worker_args = [… "-t", target_arg …]`) and a **clean canonical label**
  for filenames (the stem already carries `canon_target`; pass it explicitly to
  the worker via a label arg rather than letting the template build the filename
  from `$TARGET`).
- `inputs`/`extra`: store `target` (mix string), `target_nuclides`, `material`,
  and keep `canon_target` for `pnfs`/labels.

**`adapters/genie/run_gmkspl_grid.py`**: expand materials in `tgt_pdgs` (dedup),
exactly like the local gmkspl change. The `_split` + list shape already exists.

**`adapters/genie/common.py`**: `validate_target` is per-PDG and stays as-is
(callers loop over expanded nuclide PDGs).

**Templates** — the critical quoting/filename fixes:
- `templates/gevgen_grid.sh`:
  - line ~132: quote the mix so `[ ]` aren't shell-globbed →
    `gevgen -p ${PROBE} -t "${TARGET}" …`.
  - line ~125 `FILENAME=…_${TARGET}_…`: replace `${TARGET}` with a sanitized
    label. Add a worker option carrying the canonical label (e.g. reuse the
    job-stem arg, or add `-N <label>`), and build `FILENAME` from that, not from
    the bracketed mix string. Without this the GHEP filename would contain
    `[`,`]`,`,`.
- `templates/gmkspl_grid.sh`: already does `TARGET_LABEL=$(echo $TARGET | tr ','
  '-')` and quotes nothing problematic (no brackets in gmkspl `-t`). Confirm the
  comma list still works (it does); no change expected beyond verifying.

## Docs

- `CLAUDE.md` "Custom tunes"/PDG section: add a short "Composite targets" note —
  `--target CH` resolves via `shared/material.json` (G4-NIST mass fractions →
  natural isotopic mix), gmkspl splines all constituent nuclides, gevgen runs a
  mono-energetic target mix; regenerate with `pixi run python
  shared/build_material.py`. Note the free-H/CCQE caveat.
- `genie-grid` skill: one line that `--target` accepts materials.

## Verification (real runs, per project convention — no test suite)

1. **Build the DB:** `pixi run python shared/build_material.py` → inspect
   `shared/material.json`; check CH nuclide mass fractions sum to 1.0 and the
   C:H *atom* ratio recovers ≈1:1 (Σ mass_frac/A per element).
2. **Resolver:** `pixi run python -c "import sys; sys.path.insert(0,'genie-agent');
   from lib.pdg import resolve_material, material_mix_arg;
   print(material_mix_arg(resolve_material('CH')))"` → prints
   `1000060120[…],1000060130[…],1000010010[…],1000010020[…]`.
3. **gmkspl (foreground, real):** `pixi run python
   genie-agent/scripts/run_gmkspl.py --probes numu --targets CH --tune
   G18_02a_00_000 --genlist CCQE -n 30 -e 5 --foreground` → exits 0, XML lists
   splines for C12/C13 (H1/H2 may be empty for CCQE — expected, free H has no
   bound neutron; the warning should fire). Verify via the `genie-runlog` skill.
4. **gevgen (foreground, real):** feed the CH spline from step 3:
   `… run_gevgen.py --probe numu --target CH -n 100 -e 3.0 --cross-sections
   <CH.xml> --tune G18_02a_00_000 --genlist CCQE --foreground` → exits 0,
   produces a GHEP; runlog `inputs.target` shows the mix string and
   `inputs.material == "CH"`.
5. **Grid dry-run (no submission):** `… run_gevgen_grid.py --probe numu --target
   CH … --dry-run` and `run_gmkspl_grid.py --targets CH … --dry-run` → inspect
   the printed `gevgen -t "…"` is quoted and the generated FILENAME is sanitized
   (no `[`/`]`/`,`).
6. **Regression:** a plain `--target C12` gevgen/gmkspl still works unchanged
   (material branch returns None).

## Files touched

- new: `shared/material.json`, `shared/build_material.py`
- `genie-agent/lib/pdg.py`, `jobsub-agent/adapters/genie/pdg.py` (identical edits)
- `genie-agent/lib/validation.py`
- `genie-agent/scripts/run_gevgen.py`, `genie-agent/scripts/run_gmkspl.py`
- `jobsub-agent/adapters/genie/run_gevgen_grid.py`,
  `jobsub-agent/adapters/genie/run_gmkspl_grid.py`
- `jobsub-agent/adapters/genie/templates/gevgen_grid.sh` (quote `-t`, sanitize
  FILENAME); verify `gmkspl_grid.sh`
- `CLAUDE.md`, `.claude/skills/genie-grid` (docs)

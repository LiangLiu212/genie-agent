---
name: genie-tune
description: Create or customize a GENIE tune for genie-agent runs — a GXMLPATH overlay under genie-agent/tunes/ with per-tune parameter overrides (e.g. CommonParam values like EM-MinQ2Limit). Use when the user wants to make a custom tune, override a tune/CommonParam parameter, vary a physics parameter across tunes, or run gmkspl/gevgen with a tweaked tune. NEVER edit $GENIE/config directly.
---

# Custom GENIE tunes (`genie-agent/tunes/` + `--gxmlpath`)

GENIE resolves a tune by **directory name** on its config search path. The repo
convention (CLAUDE.md "Custom tunes via `--gxmlpath`") is to put custom tunes in
the **git-tracked `genie-agent/tunes/`** overlay and point GENIE at it with
`--gxmlpath genie-agent/tunes` — **never edit `$GENIE/config/`** (it's the
pristine install; `lib/genie_env.py::with_gxmlpath` prepends the overlay so it
wins).

## Tune-id anatomy (this is the part people get wrong)

A tune id is `<PREFIX><YY>_<MM><x>_<PP>_<FFF>`, e.g. `GEM21_11a_02_000`:

| field | example | meaning |
|-------|---------|---------|
| CMC   | `GEM21_11a` | first two parts = **comprehensive model config** = the **directory** |
| `PP`  | `02`    | tuned-param-set id (5th field) |
| `FFF` | `000`   | fit/fates id (6th field) |

GENIE loads the CMC dir's XMLs (`CommonParam.xml`, `ModelConfiguration.xml`, …),
then — **only when `PP != "00"`** — loads override files from a subdir
`<CMC>/<full-tune-id>/`. This is `OnlyConfiguration() == (PP=="00")` in
`TuneId.cxx`. Real examples: `G18_10c/G18_10c_02_11a/CommonParam.xml`.

⇒ **To give variants their own parameters, vary `PP` (e.g. `_01_000`, `_02_000`),
NOT `FFF` (`_00_001` etc.).** `_00_xxx` all collapse back to the CMC dir and
share one config.

## Recipe A — per-tune parameter override (most common)

Override a `CommonParam` (or any tune XML) value, keeping everything else:

```bash
CMC=GEM21_11a                                   # the family/CMC to base on
SRC="$GENIE/config/$CMC"                        # read-only template (don't edit it)
DST=genie-agent/tunes/$CMC
cp -r "$SRC" "$DST"                             # copy the CMC into the overlay

# one PP-variant subdir per value (PP must be != 00):
for pp_val in 01:0.02 02:0.20 03:0.50; do
  pp=${pp_val%%:*}; v=${pp_val##*:}
  mkdir -p "$DST/${CMC}_${pp}_000"
  # full copy of the CMC CommonParam, with the override param added/changed.
  # The stock [Lepton] set has no EM-MinQ2Limit, so INSERT it (append after a
  # line that's already in the set). If the param already exists, substitute its
  # value with `sed 's#\(name="EM-MinQ2Limit"> \)[0-9.]*#\1'"$v"'#'` instead.
  sed '/name="ApplyCoulombCorrection"/a\    <param type="double" name="EM-MinQ2Limit"> '"$v"' </param>' \
      "$DST/CommonParam.xml" > "$DST/${CMC}_${pp}_000/CommonParam.xml"
done
```

Notes:
- The subdir `CommonParam.xml` is a **full copy** of the CMC's with the one param
  added/changed (mirrors stock tunes like `G18_10c_02_11a`); GENIE merges it over
  the CMC config.
- `CommonParam.xml` param sets are read via
  `AlgConfigPool::CommonList("Param", "<set>")` — e.g. `EM-MinQ2Limit` lives in
  the `[Lepton]` set. Add the param under the right `<param_set>`.

## Recipe B — whole new family overlay

Copy an existing CMC family to a new name and edit its algorithm configs (e.g.
form-factor model, axial mass). Keep the CMC dir name = the first two tune-id
parts. The tune resolves as `_00_000` (uses the CMC dir directly). GENIE finds
the family on `--gxmlpath` before `$GENIE/config`, and
`lib/validation.py::_tune_family_dir` validates it from the overlay too.

## Running with the custom tune

```bash
# local
pixi run python genie-agent/scripts/run_gmkspl.py \
    --probes eminus --targets C12 --genlist EMQE -n 30 -e 5 \
    --tune GEM21_11a_02_000 --gxmlpath genie-agent/tunes \
    --installation <install> --foreground

# grid: tarball genie-agent/tunes as an overlay and pass --tune-tarball-label
#       (see the jobsub-tarball + genie-grid skills; worker flag -X)
```

## Verifying an override took effect

Use a parameter that changes an observable. Worked example — `EM-MinQ2Limit`
(EM Q² threshold; raising it lowers the EM QEL cross-section because more low-Q²
phase space is cut):

```bash
# run gmkspl EMQE on e-/C12 for three PP variants (0.02 / 0.20 / 0.50), then:
grep "EM-MinQ2Limit =" <run>.stdout          # NOTICE shows the value read + "registry found"
grep -oE "<E>[^<]+</E> <xsec>[^<]+</xsec>" <run>.xml | tail -1   # compare last knot
```

Pass: the NOTICE prints each tune's value with `registry found` (i.e. read from
the overlay, not the 0.02 fallback), and the spline σ decreases monotonically as
the limit rises. (`EM-MinQ2Limit` is wired via the `EMMinQ2LimitProxy` in
`KineUtils.{h,cxx}` reading `CommonParam.xml [Lepton]`.)

## Gotchas
- `_00_xxx` variants share one config — vary `PP` (≥`01`), not `FFF`.
- Don't touch `$GENIE/config/`; copy into `genie-agent/tunes/`.
- Splines/events are valid only for the tune that made them — a parameter change
  invalidates previously generated splines; regenerate.
- After changing `CommonParam.xml`, the value is read **once per process** and
  cached; start a fresh run to pick up an edit.

---
name: genie-install
description: Install (build from source) an official GENIE release into a new genie-agent installation, with dependencies managed by spack. Use when the user wants to build/install a new GENIE Generator version, add a new installation to genie_env.json, or set up GENIE from the GENIE-MC/Generator GitHub release. This is a one-time, shell-driven build — NOT for running gmkspl/gevgen (use genie-agent's run_gmkspl/run_gevgen) or grid jobs (genie-grid).
---

# Install a GENIE release (`genie-agent`)

One-time, shell-driven build of an **official** GENIE Generator release into a
new `genie-agent` installation. Dependencies come from **spack** (larsoft
CVMFS) — pythia6/root/lhapdf/… are already provided there. This is the
non-INCL build; see [Adding INCL/Reweight later](#adding-inclreweight-later).

The result is a `GENIEBASE` dir + `setup_env.sh`, registered in
`config/genie_env.json` and snapshotted to `config/env/<name>.json`, after which
the normal runners (`run_gmkspl.py`, `run_gevgen.py`, `run_gntpc.py`) and the
grid adapter work against it like any other installation.

## Inputs
- `GENIEBASE` — install root, e.g. `/exp/dune/app/users/$USER/GENIE/GENIE_v3_6_0`
- `TAG` — GENIE release tag, e.g. `R-3_06_00` (see github.com/GENIE-MC/Generator/releases),
  or a branch such as `rc-v380` (pre-release of v3.8; see the [GENIE ≥ 3.8](#genie--38-rc-v380-pythia8-is-required) notes)
- `NAME` — installation key for `genie_env.json`, e.g. `genie_v3_6_0_spack`

## Prerequisites
- A node with `/cvmfs/larsoft.opensciencegrid.org` mounted and spack available.
- `git`, a C++/Fortran toolchain via the spack `gcc` package (loaded below).

## Steps

### 1. Activate the spack env (deps incl. pythia6)
The pinned **version** set matches what the grid worker scripts load
(`jobsub-agent/adapters/genie/templates/gmkspl_grid.sh:76-100`); here we use
`--first` (pick any concretization) instead of the worker's `/hash` pins.

```bash
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh
spack load --first gcc@12.5.0 root@6.28.12 pythia6@6.4.28 log4cpp@1.1.3 \
                   lhapdf@6.5.5 libxml2@2.9.13 boost@1.82.0 gsl@2.8 \
                   xrootd@5.8.4 eigen@3.4.1

# Derive *_PKG_DIR + LD_LIBRARY_PATH (same loop as the worker scripts):
while IFS=' ' read -r name prefix; do
  varname="${name^^}_PKG_DIR"
  export "${varname}"="${prefix}"
  [[ -d "${prefix}/lib64" ]] && export LD_LIBRARY_PATH="${prefix}/lib64:${LD_LIBRARY_PATH}"
  [[ -d "${prefix}/lib"   ]] && export LD_LIBRARY_PATH="${prefix}/lib:${LD_LIBRARY_PATH}"
done < <(spack find --loaded --format "{name} {prefix}")

export PYTHIA6_LIB_DIR=${PYTHIA6_PKG_DIR}/lib
source ${ROOT_PKG_DIR}/bin/thisroot.sh        # root-config now on PATH
```

### 2. Clone the official release
```bash
GENIEBASE=/exp/dune/app/users/$USER/GENIE/GENIE_<ver>    # set this
TAG=R-3_06_00                                            # set this
mkdir -p "$GENIEBASE"
git clone --branch "$TAG" --depth 1 \
    https://github.com/GENIE-MC/Generator "$GENIEBASE/Generator"
```

### 3. Configure + build
GENIE's `./configure` finds ROOT via `root-config` on PATH. Confirm the exact
flag names for your tag with `./configure --help` and **record the working
invocation back into this file**. Typical:

```bash
cd "$GENIEBASE/Generator"
export GENIE=$PWD
./configure \
    --with-pythia6-lib="$PYTHIA6_LIB_DIR" \
    --disable-lhapdf5 \
    --enable-lhapdf6 \
    --with-lhapdf6-lib="$LHAPDF_PKG_DIR/lib" \
    --with-lhapdf6-inc="$LHAPDF_PKG_DIR/include" \
    --with-log4cpp-lib="$LOG4CPP_PKG_DIR/lib" \
    --with-log4cpp-inc="$LOG4CPP_PKG_DIR/include" \
    --with-libxml2-lib="$LIBXML2_PKG_DIR/lib" \
    --with-libxml2-inc="$LIBXML2_PKG_DIR/include/libxml2"
make -j"$(nproc)"
mkdir -p "$GENIEBASE/data"     # XSECSPLINEDIR
```
Reweight/nusystematics/nuisance are **not** built here (unused by the runners) —
see [Adding INCL/Reweight later](#adding-inclreweight-later).

Confirmed working for `R-3_06_02` (2026-08-19) with exactly the invocation above.
`--disable-lhapdf5` matters: lhapdf5 is default-enabled and both reference builds
(`GENIE_INCLXX`, `GENIE_v3_6_0`) carry `GOPT_ENABLE_LHAPDF5=NO`. Note the spack
`libxml2` is an *external* (prefix `/usr`), so `LIBXML2_PKG_DIR=/usr` and the
recorded include path is `/usr/include/libxml2` — same as the reference builds;
not a bug.

### GENIE ≥ 3.8 (`rc-v380`): Pythia8 is required
`rc-v380` flips the configure defaults to `pythia8` enabled / `pythia6` disabled, **and**
the stock configs (`AGKY2019.xml`, `AGKYLowW2019.xml`, `UnstableParticleDecayer.xml`,
`DISHadronicSystemGenerator.xml`) name the `Pythia8Hadro2019` / `Pythia8Decayer2023` /
`AGCharmPythia8Hadro2023` algorithms. Those `std::exit(1)` when GENIE is built without
Pythia8, so the v3.6-style Pythia6-only recipe above builds fine but dies on the first
gevgen event (gmkspl still works — it never touches the hadronizer). Recipe deltas,
confirmed working for `rc-v380` @ `29238ed` on 2026-09-03 (Pythia8 **only**, recorded in
`/exp/dune/app/users/liangliu/GENIE/GENIE_RC/build_genie.sh`, installation key `genie_rc`):

- spack has `pythia8@8.317` (gcc 12.5.0, cxxstd=17, x86_64_v2). Add it to the
  `spack load --first` line of both the build script and `setup_env.sh`; drop
  `pythia6@6.4.28`, `PYTHIA6_LIB_DIR` and the `LIBRARY_PATH=…PYTHIA6_LIB_DIR` line
  (with Pythia6 disabled nothing links it, not even ROOT's `libEGPythia6`).
- spack does **not** set `PYTHIA8DATA`; add
  `export PYTHIA8DATA=${PYTHIA8_PKG_DIR}/share/Pythia8/xmldoc` to both scripts.
- configure: replace `--with-pythia6-lib=…` with
  `--disable-pythia6 --enable-pythia8 --with-pythia8-inc="$PYTHIA8_PKG_DIR/include"
  --with-pythia8-lib="$PYTHIA8_PKG_DIR/lib"` (the lhapdf6/log4cpp/libxml2 flags are
  unchanged). Pythia6 and Pythia8 can also be enabled together (nothing in `configure`
  or `Make.include` forbids it; built and run once on 2026-09-03 before switching to
  Pythia8-only at the user's request).
- Stock configs that still name Pythia6 algorithms (`HEDISGenerator.xml`,
  `GLRESGenerator.xml`, `PhotonRESGenerator.xml`, `PhotonCOHGenerator.xml`) are unusable
  in a Pythia8-only build; the standard tunes/genlists don't touch them.
- Verification beyond step 7: the CCQE chain exercises no hadronization, so also run a
  free-proton DIS sample — `gmkspl --probes numu --targets H1 --genlist CCDIS -n 30 -e 5`
  (4 splines, ~9 min) then `gevgen … --target H1 --genlist CCDIS -n 50 -e 4.5`; the
  stdout must show the `This is PYTHIA version 8.317` banner and gst must contain
  events with W > 2.3 GeV (the Pythia8 regime of AGKY). **Gotcha:** generating at
  exactly the spline's `Emax` (`-e 5` against a `-e 5` spline) makes gevgen loop
  forever on `Could not select interaction` (10M log lines, 0 events) — always
  generate strictly inside the spline range.
- The grid worker templates still `spack load pythia6@6.4.28` and set
  `PYTHIA6_LIB_DIR`; to run this install on the grid they need `pythia8@8.317` +
  `PYTHIA8DATA` added (not done as of 2026-09-03).

### Parallel make on EAF
`nproc` reports 1 on the EAF pod (`OMP_NUM_THREADS=1`) but the cgroup allows 32 cores.
`make -jN` at the top level is **unsafe**: `apps` hangs every `INITIAL_BUILD_TARGET` off
it as unordered prerequisites, so header generation (`GBuild.h`/`GVersion.h`) and
`lib/` creation race the compiles — a half-written `GBuild.h` could silently drop
`__GENIE_PYTHIA8_ENABLED__`. Safe pattern (used for `rc-v380`, 6.7 min vs 12 min serial
for v3.6.2): serial `make print-make-info make-bin-lib-dir save-build-env
autogenerated-headers`, then `make -j16 <target>` for each `INITIAL_BUILD_TARGET` in
Makefile order (each recipe walks its packages sequentially; inside a package the
rootcint/lib rules declare their dependencies), then a final serial `make`. The final
pass recompiles and relinks the 18 apps (the Apps Makefile has no dependency
tracking, ~1 min) but must compile nothing else — grep its section of `build.log`
for `Generating shared library` to confirm.

### 4. Write `$GENIEBASE/setup_env.sh`
Static reference script the env-snapshotter sources. Modeled on the worker
env block but **without** the `thisinclxx.sh` / `setup.nusystematics.sh` /
`GENIE_REWEIGHT` lines (no INCL/Reweight in this build).

```bash
cat > "$GENIEBASE/setup_env.sh" <<'EOF'
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh
spack load --first gcc@12.5.0 root@6.28.12 pythia6@6.4.28 log4cpp@1.1.3 \
                   lhapdf@6.5.5 libxml2@2.9.13 boost@1.82.0 gsl@2.8 \
                   xrootd@5.8.4 eigen@3.4.1
while IFS=' ' read -r name prefix; do
  varname="${name^^}_PKG_DIR"
  export "${varname}"="${prefix}"
  [[ -d "${prefix}/lib64" ]] && export LD_LIBRARY_PATH="${prefix}/lib64:${LD_LIBRARY_PATH}"
  [[ -d "${prefix}/lib"   ]] && export LD_LIBRARY_PATH="${prefix}/lib:${LD_LIBRARY_PATH}"
done < <(spack find --loaded --format "{name} {prefix}")
export PYTHIA6_LIB_DIR=${PYTHIA6_PKG_DIR}/lib
source ${ROOT_PKG_DIR}/bin/thisroot.sh
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export GENIE=${THIS_DIR}/Generator
export XSECSPLINEDIR=${THIS_DIR}/data
export PATH=$GENIE/bin:$PATH
export LD_LIBRARY_PATH=$GENIE/lib:${LD_LIBRARY_PATH}
export LIBRARY_PATH=${LIBRARY_PATH}:${PYTHIA6_LIB_DIR}
EOF
```
`refresh_genie_env.py`/`load_genie_env` only require `$GENIE` to be set after
sourcing (`genie-agent/lib/genie_env.py:71`), so omitting `GENIE_REWEIGHT` is safe.

### 5. Register the installation
Add an entry to `genie-agent/config/genie_env.json` (gitignored, machine-local)
under `installations` — same shape as the existing entries. Leave
`active_installation` and the others untouched:

```json
"genie_v3_6_0_spack": {
  "genie_bin_dir": "<GENIEBASE>/Generator/bin",
  "genie_lib_dir": "<GENIEBASE>/Generator/lib",
  "genie_setup_script": "<GENIEBASE>/setup_env.sh"
}
```

### 6. Snapshot the env (existing tooling)
```bash
pixi run python genie-agent/scripts/refresh_genie_env.py --installation <name>
```
Writes `genie-agent/config/env/<name>.json`. The snapshot runs in a
parent-stripped shell, so the static `setup_env.sh` above must use absolute
paths (it does — spack/CVMFS are absolute).

### 7. Verify locally
```bash
pixi run python genie-agent/scripts/run_gmkspl.py \
    --probes numu --targets C12 --tune G18_02a_00_000 --genlist CCQE \
    -n 30 -e 5 --installation <name> --foreground
```
Must exit 0 **and** produce a non-empty spline: check
`jq '.outputs.spline_count' <run.log>` is > 0. Use **C12**, not free `H1` (no
bound neutron → empty spline list despite `returncode==0`; the launcher warns
and records `spline_count: 0`). Inspect with the `genie-runlog` skill.

## Grid (notes only)
The grid worker scripts already `spack load` the matching deps and now guard the
INCL source, so a non-INCL install runs unmodified. To use this install on the
grid (see the **jobsub-tarball** and **genie-grid** skills):

```bash
# Tarball the base dir, dropping trees absent in a non-INCL build:
pixi run python jobsub-agent/scripts/tarball.py build \
    --build-dir "$GENIEBASE" \
    --toplevel Generator --toplevel data --toplevel setup_env.sh \
    --exclude-component src --exclude-suffix .o
pixi run python jobsub-agent/scripts/tarball.py publish \
    --tarball <built.tar> --label <label>
# then submit (genie-grid skill):
pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
    --probes numu --targets C12 --tune G18_02a_00_000 --genlist CCQE \
    --tarball-label <label> -N 1 --dry-run
```
**ABI caveat:** the local `--first` concretization may differ from the workers'
hash-pinned specs. If the published tarball fails to link on the worker,
re-concretize locally to match (or pin the same `/hash`). Always smoke-test a
single `-N 1` job before scaling.

## Adding INCL/Reweight later
For the GENIE-INCL variant (shipping later): build `inclxx_genie`, `Reweight`,
`nusystematics`, `nuisance` under `$GENIEBASE`, then add back to `setup_env.sh`
the `source .../thisinclxx.sh`, `source .../setup.nusystematics.sh`, and
`export GENIE_REWEIGHT=.../Reweight` (+ its PATH/LD_LIBRARY_PATH) lines — i.e.
the full reference at `/exp/dune/app/users/liangliu/GENIEINCLXX/GENIE_RC/setup_env.sh`
(the deprecated INCL RC install — **not** `GENIE/GENIE_RC`, which since 2026-09-03 is the
`rc-v380` Pythia8-only build without INCL). The grid worker guard
already sources `thisinclxx.sh` when present, so no worker change is needed.

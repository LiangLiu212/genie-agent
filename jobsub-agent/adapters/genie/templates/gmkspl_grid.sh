#!/bin/bash
# gmkspl_grid.sh — HTCondor worker script for grid-mode GENIE spline generation.
#
# Invoked by jobsub_lite. The GENIE installation tarball is unpacked at
# $INPUT_TAR_DIR_LOCAL (its parent contains setup_env.sh). An optional input
# cross-section XML can be shipped via `jobsub_submit -f <xml>` and lands at
# $CONDOR_DIR_INPUT/<basename>.xml.
#
# Per-process seed is $CLUSTER + $PROCESS so reruns are reproducible.
# Output XML is copied to PNFS scratch under
#   /pnfs/dune/scratch/users/$GRID_USER/genie-mcp/$JOB_ID/<probe>_<target>_<tune>/<process_str>/
#
# Usage (set by gmkspl_grid_tool.py):
#   gmkspl_grid.sh -p <probe_pdgs> -t <target_pdgs> [-e <max_e>] [-n <n_knots>] \
#                  -T <tune> -L <gen_list> [-S <input_xsec_basename>] -j <job_id>
#
# Comma-separated PDG lists for -p / -t are passed through to gmkspl verbatim.

set -e
date

MAXE=""
NKNOTS=""
INPUT_XSEC=""
RCDS_DIR_OVERRIDE=""
PNFS_OUTPUT_DIR=""
TUNE_CVMFS_DIR=""

while getopts "p:t:e:n:T:L:S:j:R:O:X:" opt; do
  case $opt in
    p) PROBE=$OPTARG ;;
    t) TARGET=$OPTARG ;;
    e) MAXE=$OPTARG ;;
    n) NKNOTS=$OPTARG ;;
    T) TUNE=$OPTARG ;;
    L) GENLIST=$OPTARG ;;
    S) INPUT_XSEC=$OPTARG ;;
    j) JOB_ID=$OPTARG ;;
    R) RCDS_DIR_OVERRIDE=$OPTARG ;;
    O) PNFS_OUTPUT_DIR=$OPTARG ;;
    X) TUNE_CVMFS_DIR=$OPTARG ;;
    *) echo "Bad flag: $opt" >&2; exit 2 ;;
  esac
done

if [ -z "${PNFS_OUTPUT_DIR}" ]; then
  echo "-O <pnfs_output_dir> is required" >&2
  exit 2
fi

PROCESS_STR=$(printf "%04d" $PROCESS)
RDMSEED=$((CLUSTER + PROCESS))
echo "JOB_ID=${JOB_ID} CLUSTER=${CLUSTER} PROCESS=${PROCESS} SEED=${RDMSEED}"

# ── Environment ───────────────────────────────────────────────────────────────
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh
spack load --first ifdhc

if [ -n "${RCDS_DIR_OVERRIDE}" ]; then
  RCDS_DIR="${RCDS_DIR_OVERRIDE%/}"
elif [ -n "${INPUT_TAR_FILE}" ]; then
  if [ -d "${INPUT_TAR_FILE}" ]; then
    RCDS_DIR="${INPUT_TAR_FILE%/}"
  else
    RCDS_DIR=$(dirname ${INPUT_TAR_FILE})
  fi
else
  echo "Neither -R override nor INPUT_TAR_FILE is set; cannot locate GENIE install" >&2
  exit 3
fi
echo "RCDS_DIR=${RCDS_DIR}"

# Inline setup_env.sh, skipping setup.nusystematics.sh (line 12 has a hardcoded
# cd to /exp/dune/app/...GENIE_INCL/... which is absent on grid workers).
# gmkspl does not need nusystematics or nuisance.
spack load gcc@12.5.0/jwtfpk6 root@6.28.12/aanuckv pythia6@6.4.28/oxfghfn \
           log4cpp@1.1.3/j6hsjvy lhapdf@6.5.5/hyycqlx libxml2@2.9.13/n5wbwlp \
           boost@1.82.0/dad7iqe gsl@2.8/4urojfl xrootd@5.8.4/mqueum7 \
           eigen@3.4.1/excfmns

while IFS=' ' read -r name prefix; do
  varname="${name^^}_PKG_DIR"
  export "${varname}"="${prefix}"
  if [[ -d "${prefix}/lib64" ]]; then
    export LD_LIBRARY_PATH="${prefix}/lib64:${LD_LIBRARY_PATH}"
  fi
  if [[ -d "${prefix}/lib" ]]; then
    export LD_LIBRARY_PATH="${prefix}/lib:${LD_LIBRARY_PATH}"
  fi
done < <(spack find --loaded --format "{name} {prefix}")

export PYTHIA6_LIB_DIR=${PYTHIA6_PKG_DIR}/lib
source ${ROOT_PKG_DIR}/bin/thisroot.sh
source ${RCDS_DIR}/inclxx_genie/install/bin/thisinclxx.sh
export GENIE=${RCDS_DIR}/Generator
export XSECSPLINEDIR=${RCDS_DIR}/data
export GENIE_REWEIGHT=${RCDS_DIR}/Reweight
export PATH=$GENIE/bin:$GENIE_REWEIGHT/bin:$PATH
export LD_LIBRARY_PATH=$GENIE/lib:$GENIE_REWEIGHT/lib:${LD_LIBRARY_PATH}
export LIBRARY_PATH=${LIBRARY_PATH}:${PYTHIA6_LIB_DIR}
echo "GENIE=${GENIE}"
which gmkspl || { echo "gmkspl not on PATH after env setup" >&2; exit 5; }

# ── Tune overlay (GXMLPATH) ───────────────────────────────────────────────────
if [ -n "${TUNE_CVMFS_DIR}" ]; then
  if [ -d "${TUNE_CVMFS_DIR}" ]; then
    export GXMLPATH="${TUNE_CVMFS_DIR}:${GXMLPATH}"
    echo "GXMLPATH=${GXMLPATH}"
    ls -la "${TUNE_CVMFS_DIR}/" || true
  else
    echo "TUNE_CVMFS_DIR not present on worker: ${TUNE_CVMFS_DIR}" >&2
    exit 6
  fi
fi

# ── Optional input cross-section ──────────────────────────────────────────────
INPUT_OPT=""
if [ -n "${INPUT_XSEC}" ]; then
  INPUT_PATH="${CONDOR_DIR_INPUT}/${INPUT_XSEC}"
  if [ ! -f "${INPUT_PATH}" ]; then
    echo "Input cross-section not found at ${INPUT_PATH}; CONDOR_DIR_INPUT contents:" >&2
    ls -la ${CONDOR_DIR_INPUT} >&2 || true
    exit 4
  fi
  INPUT_OPT="--input-cross-sections ${INPUT_PATH}"
fi

# ── Run gmkspl ────────────────────────────────────────────────────────────────
PROBE_LABEL=$(echo $PROBE | tr ',' '-')
TARGET_LABEL=$(echo $TARGET | tr ',' '-')
FILENAME="spl_grid_${JOB_ID}_${PROBE_LABEL}_${TARGET_LABEL}_${TUNE}_${GENLIST}"
if [ -n "${MAXE}" ]; then
  FILENAME="${FILENAME}_e${MAXE}gev"
fi
if [ -n "${NKNOTS}" ]; then
  FILENAME="${FILENAME}_n${NKNOTS}"
fi
FILENAME="${FILENAME}_p${PROCESS_STR}_c${CLUSTER}"

OPTS=""
if [ -n "${MAXE}" ]; then OPTS="$OPTS -e ${MAXE}"; fi
if [ -n "${NKNOTS}" ]; then OPTS="$OPTS -n ${NKNOTS}"; fi

echo "gmkspl -p ${PROBE} -t ${TARGET} ${OPTS} \\"
echo "       --tune ${TUNE} --event-generator-list ${GENLIST} \\"
echo "       --seed ${RDMSEED} ${INPUT_OPT} \\"
echo "       -o ${FILENAME}.xml"

gmkspl -p ${PROBE} -t ${TARGET} ${OPTS} \
       --tune ${TUNE} --event-generator-list ${GENLIST} \
       --seed ${RDMSEED} ${INPUT_OPT} \
       -o ${FILENAME}.xml

ls -alh

# ── Copy outputs to PNFS scratch ──────────────────────────────────────────────
DEST="${PNFS_OUTPUT_DIR%/}/${PROCESS_STR}"
echo "ifdh mkdir_p ${DEST}"
ifdh mkdir_p ${DEST}
echo "ifdh cp -D *.xml ${DEST}/"
ifdh cp -D *.xml ${DEST}/
date
echo "DONE"

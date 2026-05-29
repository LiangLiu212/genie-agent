#!/bin/bash
# gevgen_grid.sh — HTCondor worker script for grid-mode GENIE event generation.
#
# Invoked by jobsub_lite. The GENIE installation tarball is unpacked at
# $INPUT_TAR_DIR_LOCAL (its parent contains setup_env.sh). The cross-section
# spline is shipped via `jobsub_submit -f <spline.xml>` and lands at
# $CONDOR_DIR_INPUT/<basename>.xml.
#
# Per-process seed is $CLUSTER + $PROCESS so reruns are reproducible.
# Output ghep.root is copied to PNFS scratch under
#   /pnfs/dune/scratch/users/$GRID_USER/genie-mcp/$JOB_ID/<probe>_<target>_<tune>/<process_str>/
#
# Usage (set by gevgen_grid_tool.py):
#   gevgen_grid.sh -p <probe_pdg> -t <target_pdg> -e <energy> -n <n_events> \
#                  -T <tune> -L <gen_list> -S <spline_basename> \
#                  -j <job_id> -P <project_name>

set -e
date

RCDS_DIR_OVERRIDE=""
PNFS_OUTPUT_DIR=""
TUNE_CVMFS_DIR=""

while getopts "p:t:e:n:T:L:S:j:P:R:O:X:" opt; do
  case $opt in
    p) PROBE=$OPTARG ;;
    t) TARGET=$OPTARG ;;
    e) ENERGY=$OPTARG ;;
    n) NEVT=$OPTARG ;;
    T) TUNE=$OPTARG ;;
    L) GENLIST=$OPTARG ;;
    S) SPLINE=$OPTARG ;;
    j) JOB_ID=$OPTARG ;;
    P) PROJECT=$OPTARG ;;
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
# gevgen does not need nusystematics or nuisance.
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
which gevgen || { echo "gevgen not on PATH after env setup" >&2; exit 5; }

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

# ── Locate spline ─────────────────────────────────────────────────────────────
SPLINE_PATH="${CONDOR_DIR_INPUT}/${SPLINE}"
if [ ! -f "${SPLINE_PATH}" ]; then
  echo "Spline not found at ${SPLINE_PATH}; CONDOR_DIR_INPUT contents:" >&2
  ls -la ${CONDOR_DIR_INPUT} >&2 || true
  exit 4
fi

# ── Run gevgen ────────────────────────────────────────────────────────────────
FILENAME="gev_grid_${JOB_ID}_${PROBE}_${TARGET}_${TUNE}_${GENLIST}_n${NEVT}_p${PROCESS_STR}_c${CLUSTER}"

echo "gevgen -p ${PROBE} -t ${TARGET} -e ${ENERGY} -n ${NEVT} \\"
echo "       --cross-sections ${SPLINE_PATH} --tune ${TUNE} \\"
echo "       --event-generator-list ${GENLIST} --seed ${RDMSEED} \\"
echo "       -o ${FILENAME}.ghep.root"

gevgen -p ${PROBE} -t ${TARGET} -e ${ENERGY} -n ${NEVT} \
       --cross-sections ${SPLINE_PATH} --tune ${TUNE} \
       --event-generator-list ${GENLIST} \
       --seed ${RDMSEED} \
       -o ${FILENAME}.ghep.root

# ── Convert GHEP → GST (fatal: nothing is copied if this fails) ──────────────
echo "gntpc -i ${FILENAME}.ghep.root -f gst -o ${FILENAME}.gst.root"
gntpc -i ${FILENAME}.ghep.root -f gst -o ${FILENAME}.gst.root

ls -alh

# ── Copy outputs to PNFS scratch ──────────────────────────────────────────────
DEST="${PNFS_OUTPUT_DIR%/}/${PROCESS_STR}"
echo "ifdh mkdir_p ${DEST}"
ifdh mkdir_p ${DEST}
echo "ifdh cp -D *.ghep.root ${DEST}/"
ifdh cp -D *.ghep.root ${DEST}/
echo "ifdh cp -D *.gst.root ${DEST}/"
ifdh cp -D *.gst.root ${DEST}/
ifdh cp -D *.ghep.status ${DEST}/ 2>/dev/null || true
date
echo "DONE"

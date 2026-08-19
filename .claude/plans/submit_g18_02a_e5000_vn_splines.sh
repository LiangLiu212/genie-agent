#!/bin/bash
# Stage-2 (free-nucleon vN seed) gmkspl grid submissions for the
# G18_02a_00_000 5-TeV spline set, GENIE v3.6.2 (R-3_06_02).
# Plan: hello-now-i-need-swirling-kahan.md (Stage 2); campaign doc
# .claude/plans/g18_02a-v362-5tev-spline-set.md. Modeled on
# submit_incl26_07a_tranche2_splines.sh.
#
# All 6 nu flavors x {free-n, H1} x the 16 genlists whose union = the tune's
# Default (18 generators). 18 submissions:
#   CCDIS/NCDIS per-target (4 jobs, 72000 s)  -- DIS is the 5-TeV cost driver
#   Charm,CCDFR,NCDFR,CCRES,NCRES both targets (5 jobs, 72000 s)
#   CCQE,NCEL,CCMEC,NCMEC,CCCOHPION,NCCOHPION,NuEElastic,IMD,LambdaCCQE
#     both targets (9 jobs, 14400 s)          -- cheap/physics-empty on vN
# Expected physics-empty combos (MEC/COH on free nucleons, NuEElastic/IMD on
# free-n, charge-forbidden QE flavors) exit 0 with few/no splines -- fine.
#
# Run on a dunegpvm with a token:
#   export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
#   htgettoken -a htvaultprod.fnal.gov -i dune
# Modes:
#   ./submit_g18_02a_e5000_vn_splines.sh        print all commands
#   ./submit_g18_02a_e5000_vn_splines.sh --go   submit for real

set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO"

GO=0
for arg in "$@"; do
  case "$arg" in
    --go) GO=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

PROBES="numu,numubar,nue,nuebar,nutau,nutaubar"
TUNE="G18_02a_00_000"
TARBALL="genie_v3_6_2"
INSTALL="genie_v3_6_2"
KNOTS=300
EMAX=5000

TARGETS_VN=(1000000010 H1)   # free neutron, free proton

NSUB=0

submit_chunks() {  # genlist chunk_size expected_lifetime_s target...
  local genlist=$1 chunk=$2 lifetime=$3; shift 3
  local -a tgts=("$@")
  local i n=${#tgts[@]}
  for ((i = 0; i < n; i += chunk)); do
    local csv
    csv=$(IFS=,; echo "${tgts[*]:i:chunk}")
    local -a cmd=(pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py
      --probes "$PROBES" --targets "$csv" --tune "$TUNE" --genlist "$genlist"
      --tarball-label "$TARBALL" --installation "$INSTALL"
      -n "$KNOTS" -e "$EMAX" -N 1 --expected-lifetime "$lifetime")
    NSUB=$((NSUB + 1))
    if [ "$GO" = 1 ]; then
      # Resume guard: skip if a live/terminal-success record already exists for
      # this (genlist, target set, tune) — makes a partial campaign rerunnable.
      local label=${csv//,/-} existing
      existing=$(jq -r --arg gl "$genlist" --arg tgt "$label" --arg tune "$TUNE" \
        'select(.extra.genlist==$gl and .extra.target==$tgt and .extra.tune==$tune
                and (.status=="submitted" or .status=="running" or .status=="held"
                     or .status=="done" or .status=="partial"))|.jobid' \
        jobsub-agent/jobsub-runs/gmkspl_grid-*/*.gridlog 2>/dev/null | head -1) || true
      if [ -n "$existing" ]; then
        echo "[$NSUB/skip] $genlist <- $csv (already: $existing)"
        continue
      fi
      echo "[$NSUB] $genlist <- $csv"
      "${cmd[@]}"
      sleep 1   # stems are second-granular; keep them unique
    else
      printf '%q ' "${cmd[@]}"; echo
    fi
  done
}

# Heavy bands first so the long jobs enter the queue earliest.
submit_chunks CCDIS      1 72000 "${TARGETS_VN[@]}"
submit_chunks NCDIS      1 72000 "${TARGETS_VN[@]}"
submit_chunks Charm      2 72000 "${TARGETS_VN[@]}"
submit_chunks CCDFR      2 72000 "${TARGETS_VN[@]}"
submit_chunks NCDFR      2 72000 "${TARGETS_VN[@]}"
submit_chunks CCRES      2 72000 "${TARGETS_VN[@]}"
submit_chunks NCRES      2 72000 "${TARGETS_VN[@]}"
submit_chunks CCQE       2 14400 "${TARGETS_VN[@]}"
submit_chunks NCEL       2 14400 "${TARGETS_VN[@]}"
submit_chunks CCMEC      2 14400 "${TARGETS_VN[@]}"
submit_chunks NCMEC      2 14400 "${TARGETS_VN[@]}"
submit_chunks CCCOHPION  2 14400 "${TARGETS_VN[@]}"
submit_chunks NCCOHPION  2 14400 "${TARGETS_VN[@]}"
submit_chunks NuEElastic 2 14400 "${TARGETS_VN[@]}"
submit_chunks IMD        2 14400 "${TARGETS_VN[@]}"
submit_chunks LambdaCCQE 2 14400 "${TARGETS_VN[@]}"

if [ "$GO" = 1 ]; then
  echo "submitted $NSUB jobs"
else
  echo "# $NSUB submissions total; re-run with --go to submit" >&2
fi

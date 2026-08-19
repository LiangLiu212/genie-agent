#!/bin/bash
# Stage-3 pilot/timing tranche for the G18_02a_00_000 5-TeV spline set
# (GENIE v3.6.2). Plan: hello-now-i-need-swirling-kahan.md (Stage 3);
# campaign log .claude/plans/g18_02a-v362-5tev-spline-set.md.
#
# 7 production-quality jobs that calibrate the Stage-4 lifetime bands:
#   CCDIS  C12 / W186   172800 s  (DIS is the 5-TeV cost driver; A-dependence)
#   Charm  C12 / W186   172800 s  (no prior at all; proves charm on the worker)
#   CCQE   C12 / W186    72000 s  (G18 QE != INCL QE; prior does not transfer)
#   CCMEC  C12           72000 s  (G18 empirical MEC should be minutes; confirm)
# All seeded with the Stage-2 vN XML so nuclear jobs never recompute free-
# nucleon DIS. Requires the seed on persistent /pnfs (Stage 2 done).
#
# Run with a token (works from EAF):
#   export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
#   htgettoken -a htvaultprod.fnal.gov -i dune   # if expired
# Modes: no args = print; --go = submit.

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
SEED_XML=/pnfs/dune/persistent/users/liangliu/genie_xsec/g18_02a_e5000/seed/gxspl-vN-e5000.xml

NSUB=0

submit_one() {  # genlist target expected_lifetime_s
  local genlist=$1 tgt=$2 lifetime=$3
  local -a cmd=(pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py
    --probes "$PROBES" --targets "$tgt" --tune "$TUNE" --genlist "$genlist"
    --tarball-label "$TARBALL" --installation "$INSTALL"
    -n "$KNOTS" -e "$EMAX" -N 1 --expected-lifetime "$lifetime"
    --input-cross-sections "$SEED_XML")
  NSUB=$((NSUB + 1))
  if [ "$GO" = 1 ]; then
    local existing
    existing=$(jq -r --arg gl "$genlist" --arg tgt "$tgt" --arg tune "$TUNE" \
      'select(.extra.genlist==$gl and .extra.target==$tgt and .extra.tune==$tune
              and (.status=="submitted" or .status=="running" or .status=="held"
                   or .status=="done" or .status=="partial"))|.jobid' \
      jobsub-agent/jobsub-runs/gmkspl_grid-*/*.gridlog 2>/dev/null | head -1) || true
    if [ -n "$existing" ]; then
      echo "[$NSUB/skip] $genlist <- $tgt (already: $existing)"
      return
    fi
    echo "[$NSUB] $genlist <- $tgt"
    "${cmd[@]}"
    sleep 1
  else
    printf '%q ' "${cmd[@]}"; echo
  fi
}

submit_one CCDIS C12  172800
submit_one CCDIS W186 172800
submit_one Charm C12  172800
submit_one Charm W186 172800
submit_one CCQE  C12   72000
submit_one CCQE  W186  72000
submit_one CCMEC C12   72000

if [ "$GO" = 1 ]; then
  echo "submitted $NSUB jobs"
else
  echo "# $NSUB submissions total; re-run with --go to submit" >&2
fi

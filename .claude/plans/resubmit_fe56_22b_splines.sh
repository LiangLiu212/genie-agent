#!/bin/bash
# Kill + resubmit the five GEM26_22b Fe56 spline jobs WITH --expected-lifetime 48h.
# Plan: .claude/plans/fe56-em-splines-t04-t08.md. Drafted 2026-07-12.
#
# RUN ON A dunegpvm (EAF firewalls the schedds). Why: the 2026-07-11 18:17 batch
# went out with the default 8 h lifetime, before the lifetime patch landed. The
# EAF pilot measured the 22b Fe56 SF-folded spline at >13 h CPU for a mere
# n=10/e<=3 config -- the grid n=30/e=10 jobs will be evicted at 8 h and, with no
# gmkspl checkpointing, loop forever (NumJobStarts growing, cf. INCL26 tranche-1
# NCDIS). The ten 11a/22a Rosenbluth jobs already produced their XMLs on PNFS
# (verified over XRootD 2026-07-12: 30 knots, sigma(2.445)>0, 22a==11a) -- they
# are NOT touched here.
#
# Modes:
#   ./resubmit_fe56_22b_splines.sh          print commands (dry-run submissions)
#   ./resubmit_fe56_22b_splines.sh --go     jobsub_rm + submit for real

set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

# cluster ids of the 2026-07-11 18:17 default-lifetime 22b submissions
declare -A OLD=(
  [GEM26_22b_04_000]=92374697.0@jobsub02.fnal.gov
  [GEM26_22b_05_000]=70844002.0@jobsub03.fnal.gov
  [GEM26_22b_06_000]=92374698.0@jobsub02.fnal.gov
  [GEM26_22b_07_000]=85358595.0@jobsub01.fnal.gov
  [GEM26_22b_08_000]=28735864.0@jobsub04.fnal.gov
)

echo "== 1. remove the default-lifetime 22b jobs"
for tune in "${!OLD[@]}"; do
  echo "-- jobsub_rm ${OLD[$tune]}  ($tune)"
  if [ "$GO" = "--go" ]; then
    jobsub_rm -G dune --jobid "${OLD[$tune]}" || echo "RM FAILED (may have already left the queue): ${OLD[$tune]}" >&2
  fi
done

echo "== 2. resubmit the five 22b jobs with --expected-lifetime 48h"
DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for cut in 04 05 06 07 08; do
  tune="GEM26_22b_${cut}_000"
  echo "-- $tune"
  pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
      --probes eminus --targets Fe56 --tune "$tune" --genlist EMQE \
      -e 10 -n 30 \
      --tarball-label genie_inclxx --tune-tarball-label gem26_emq2lim \
      -N 1 --expected-lifetime 48h $DRY || echo "SUBMIT FAILED: $tune" >&2
done

echo "done ($([ "$GO" = "--go" ] && echo resubmitted || echo dry-run))"

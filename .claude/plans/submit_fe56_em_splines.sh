#!/bin/bash
# Fe56 EM-QE spline submissions (t04-t08) for the iron E91-013 study.
# Plan: .claude/plans/fe56-em-splines-t04-t08.md. Drafted 2026-07-11.
#
# RUN THIS ON A dunegpvm (NOT on EAF): the EAF jupyter pods firewall the RCDS
# publishers (rcds01/02:443) and every jobsub schedd (jobsub01-05:9618), so
# both the tarball publish and jobsub_submit hang there. The repo path below
# is identical on gpvms (/exp/dune/data mount).
#
# What it does:
#   1. token check (htgettoken; interactive OIDC only if no vault token)
#   2. republish the gem26_emq2lim tune overlay (--overwrite) -- REQUIRED:
#      the 2026-06-09 publication was RCDS-GC'd AND the tunes gained the Fe56
#      SpectralFunc mapping (22a/22b) on 2026-07-11
#   3. submit 15 gmkspl grid jobs: GEM26_{11a,22a,22b}_{04..08}_000 x Fe56,
#      eminus EMQE, -e 10 -n 30 (the carbon recipe with the target swapped)
#
# Modes:
#   ./submit_fe56_em_splines.sh          print all commands (dry-run submissions)
#   ./submit_fe56_em_splines.sh --go     publish + submit for real

set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
TARBALL=jobsub-agent/tarballs/overlay_gem26_emq2lim_995473238921.tar
DESC="GEM26 tune overlay; Fe56 SpectralFunc mapping added to 22a/22b (2026-07-11)"

export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

if [ ! -f "$TARBALL" ]; then
  echo "overlay tarball missing -- rebuilding from genie-agent/tunes" >&2
  pixi run python -c "
import sys; sys.path.insert(0, 'jobsub-agent')
from lib.tarball import build_overlay_tarball
r = build_overlay_tarball(source_dir='genie-agent/tunes',
        subdirs=['GEM26_11a','GEM26_22a','GEM26_22b','GEM26_33a','GEM26_33b'],
        label='gem26_emq2lim')
print(r['message']); print(r['tarball_path'])
" || exit 1
  TARBALL=$(ls -t jobsub-agent/tarballs/overlay_gem26_emq2lim_*.tar | head -1)
fi

echo "== 1. republish GC'd tarballs (gem26_emq2lim + genie_dev + gem21_emq2lim; genie_inclxx alive 2026-07-01)"
if [ "$GO" = "--go" ]; then
  pixi run python jobsub-agent/scripts/tarball.py publish \
      --tarball "$TARBALL" --label gem26_emq2lim --description "$DESC" --overwrite || exit 1
  pixi run python jobsub-agent/scripts/tarball.py publish \
      --tarball jobsub-agent/tarballs/genie_dev_7af93f627ab5.tar --label genie_dev \
      --description "genie_dev install (June-01 build, matches existing SuSAv2 samples); republish after RCDS GC" --overwrite || exit 1
  pixi run python jobsub-agent/scripts/tarball.py publish \
      --tarball jobsub-agent/tarballs/gem21emq2_overlay_0f7f1564b7f1.tar --label gem21_emq2lim \
      --description "GEM21_11a tune overlay; republish after RCDS GC" --overwrite || exit 1
  for L in gem26_emq2lim genie_dev gem21_emq2lim; do
    pixi run python jobsub-agent/scripts/tarball.py verify --label "$L" || exit 1
  done
else
  echo "   (skipped -- dry mode)"
fi

echo "== 2. submit 15 gmkspl jobs (3 tunes x t04-t08)"
# GEM26_22b (UnifiedQEL, SF-folded xsec) needs a long lifetime: the EAF local
# pilot (n=10 knots, e<=3 GeV, single Fe56 target) measured >5 h CPU at 99% and
# still running -- the grid config (n=30, e=10) will exceed the 8 h default and
# gmkspl has no checkpointing (cf. the INCL26 tranche-1 NCDIS eviction).
# Rosenbluth splines (11a/22a) are analytic-fast and keep the default.
DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for fam in GEM26_11a GEM26_22a GEM26_22b; do
  LIFE=""
  [ "$fam" = "GEM26_22b" ] && LIFE="--expected-lifetime 48h"
  for cut in 04 05 06 07 08; do
    tune="${fam}_${cut}_000"
    echo "-- $tune"
    pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py \
        --probes eminus --targets Fe56 --tune "$tune" --genlist EMQE \
        -e 10 -n 30 \
        --tarball-label genie_inclxx --tune-tarball-label gem26_emq2lim \
        -N 1 $LIFE $DRY || echo "SUBMIT FAILED: $tune" >&2
  done
done

echo "done. Track with: pixi run python genie-agent/scripts/job.py list --active"

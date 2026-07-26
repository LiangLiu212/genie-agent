#!/bin/bash
# C12 t05 full-EM spline batch -- one gmkspl grid job per tune, mirroring the
# Fe56 batch of 2026-07-15 (.claude/plans/fe56-em-t05-fullem-splines.md) with
# the target swapped: eminus C12, genlist EM (QEL+RES+DIS+MEC in one XML,
# expect 55 splines), -e 10 -n 30, -N 1.
#
# Tarball: genie_inclxx_q2guard (the RESKinematicsGenerator-guarded install,
# commit 3d97c78aa). The guard is irrelevant for spline integration (never
# crashed) but the eventual C12 full-EM gevgen jobs REQUIRE it -- C12 carries
# the same 22a/22b SpectralFunc mapping + t05 EM-MinQ2Limit=1.18 that killed
# the unpatched Fe56 event jobs -- so the whole C12 chain runs on one install.
# Overlays: gem26_emq2lim / gem21_emq2lim (same as Fe56; freshness re-verified
# by resolve_tarball at submit).
#
# Lifetimes mirror Fe56: 24h default, 48h for 22b (SF-folded UnifiedQEL QE;
# the local C12 EMQE-only spline already exceeds 1 h single-core).
#
# RUN ON a dunegpvm (EAF firewalls the jobsub schedds).
#
# Modes:
#   ./submit_c12_em_splines.sh          dry-run all 4 (adapter --dry-run)
#   ./submit_c12_em_splines.sh --go     submit for real

set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
export HOME=/exp/dune/data/users/liangliu   # robust against /nashome krb expiry
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

PY=/exp/dune/data/users/liangliu/genie-dev/.pixi/envs/default/bin/python

declare -A OVERLAY LIFE
OVERLAY[GEM26_11a_05_000]=gem26_emq2lim; LIFE[GEM26_11a_05_000]=""
OVERLAY[GEM26_22a_05_000]=gem26_emq2lim; LIFE[GEM26_22a_05_000]=""
OVERLAY[GEM26_22b_05_000]=gem26_emq2lim; LIFE[GEM26_22b_05_000]="--expected-lifetime 48h"
OVERLAY[GEM21_11a_05_000]=gem21_emq2lim; LIFE[GEM21_11a_05_000]=""

DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for tune in GEM26_11a_05_000 GEM26_22a_05_000 GEM26_22b_05_000 GEM21_11a_05_000; do
  echo "-- $tune"
  $PY jobsub-agent/adapters/genie/run_gmkspl_grid.py \
      --probes eminus --targets C12 --tune "$tune" --genlist EM \
      -e 10 -n 30 -N 1 \
      --tarball-label genie_inclxx_q2guard \
      --tune-tarball-label "${OVERLAY[$tune]}" \
      ${LIFE[$tune]} $DRY || echo "SUBMIT FAILED: $tune" >&2
  sleep 2   # gridlog stems have 1 s resolution; same-second submits clobber
done

echo "done. Track with: $PY jobsub-agent/scripts/job.py list --active"

# Outcome (2026-07-26): all 4 jobs done 1/1, 55 splines each (spot-checked).
#
# Persistent mirror (2026-07-26): all four spline XMLs copied from scratch to
# /pnfs/dune/persistent/users/liangliu/... with the directory structure
# preserved (same path, scratch -> persistent), sha256-verified both sides:
#   GEM26_11a 61a2675f9847...  (jobid ...140621-7349ff, cluster 92518805)
#   GEM26_22a 894f73d4d9ff...  (jobid ...140625-bf3e6b, cluster 29183579)
#   GEM26_22b 28c09ec5ac0b...  (jobid ...140629-0f7cd8, cluster 29183580)
#   GEM21_11a 19d8721c064a...  (jobid ...140632-2e3c54, cluster 85488212)
# The scratch originals expire ~30 d after 2026-07-17; the gridlog
# pnfs_output_dir paths map to the mirror by the same substitution.

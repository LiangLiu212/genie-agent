#!/bin/bash
# Resubmit the two Fe56 full-EM gevgen campaigns that died on the RES-EM
# Q2toQD2 assert (GEM26_22a_05_000, GEM26_22b_05_000), now with the patched
# install tarball genie_inclxx_q2guard (RESKinematicsGenerator empty-Q2-window
# guard, Generator commit 3d97c78aa). Root cause + fix:
# .claude/plans/fix-res-em-q2window-assert.md
#
# Identical campaign parameters to submit_fe56_em_gevgen.sh (2026-07-16 first
# attempt): eminus Fe56, genlist EM, -e 2.445, -n 100000 -N 100, 24h lifetime,
# PNFS-direct splines from the 07-15 gmkspl jobs. Only the tarball label
# differs. The completed 11a/GEM21 samples (unpatched genie_inclxx tarball)
# are untouched.
#
# NOTE while the /nashome Kerberos key is expired on this host, run with HOME
# redirected (jobsub_lite stats $HOME): the script does this itself.
#
# Modes:
#   ./submit_fe56_em_gevgen_q2guard.sh          dry-run both (adapter --dry-run)
#   ./submit_fe56_em_gevgen_q2guard.sh --go     submit for real

set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
export HOME=/exp/dune/data/users/liangliu   # dodge expired /nashome krb key
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

PY=/exp/dune/data/users/liangliu/genie-dev/.pixi/envs/default/bin/python

# tune -> stem of the DONE 07-15 spline gridlog + overlay label
declare -A STEM OVERLAY
STEM[GEM26_22a_05_000]=eminus_Fe56_20260715-181410; OVERLAY[GEM26_22a_05_000]=gem26_emq2lim
STEM[GEM26_22b_05_000]=eminus_Fe56_20260715-181412; OVERLAY[GEM26_22b_05_000]=gem26_emq2lim

DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for tune in GEM26_22a_05_000 GEM26_22b_05_000; do
  gl=jobsub-agent/jobsub-runs/gmkspl_grid-2026-07-15/${STEM[$tune]}.gridlog
  st=$(jq -r '.status' "$gl")
  [ "$st" = "done" ] || { echo "spline gridlog $gl not done (status=$st)" >&2; exit 1; }
  d=$(jq -r '.pnfs_output_dir' "$gl")
  mapfile -t xmls < <(find "$d" -name '*.xml' 2>/dev/null)
  [ ${#xmls[@]} -eq 1 ] || { echo "expected 1 spline xml for $tune, got ${#xmls[@]}" >&2; exit 1; }
  echo "-- $tune"
  echo "   spline: ${xmls[0]}"
  $PY jobsub-agent/adapters/genie/run_gevgen_grid.py \
      --probe eminus --target Fe56 --tune "$tune" --genlist EM \
      -e 2.445 -n 100000 -N 100 \
      --cross-sections "${xmls[0]}" \
      --tarball-label genie_inclxx_q2guard --tune-tarball-label "${OVERLAY[$tune]}" \
      --expected-lifetime 24h $DRY || echo "SUBMIT FAILED: $tune" >&2
  sleep 2   # gridlog stems have 1 s resolution; same-second submits clobber
done

echo "done. Track with: $PY jobsub-agent/scripts/job.py list --active"

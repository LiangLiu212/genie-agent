#!/bin/bash
# C12 full-EM gevgen batch -- one grid campaign per tune, mirroring the Fe56
# event batches of 2026-07-16 (.claude/plans/submit_fe56_em_gevgen.sh +
# submit_fe56_em_gevgen_q2guard.sh) with the target swapped: eminus C12,
# genlist EM, -e 2.445 (Dutta nucl-ex/0303011 beam energy), -n 100000 -N 100
# (10M events/tune), 24h lifetime.
#
# Tarball: genie_inclxx_q2guard for ALL four tunes (RESKinematicsGenerator
# empty-Q2-window guard, Generator commit 3d97c78aa) -- C12 carries the same
# 22a/22b SpectralFunc mapping + t05 EM-MinQ2Limit=1.18 that killed the
# unpatched Fe56 22a/22b event jobs, and the whole C12 chain runs on one
# install (see submit_c12_em_splines.sh header). Overlays: gem26_emq2lim /
# gem21_emq2lim.
#
# Splines: the DONE 2026-07-17 C12 gmkspl outputs (55 splines each, verified),
# taken from the sha256-verified PERSISTENT mirror (2026-07-26) rather than
# scratch -- scratch purges ~2026-08-16 and the job logs should record a path
# that still resolves. Derived from each spline gridlog's pnfs_output_dir by
# the standard scratch -> persistent substitution.
#
# RUN ON a dunegpvm (EAF firewalls the jobsub schedds).
#
# Modes:
#   ./submit_c12_em_gevgen.sh          dry-run all 4 (adapter --dry-run)
#   ./submit_c12_em_gevgen.sh --go     submit for real
set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
export HOME=/exp/dune/data/users/liangliu   # dodge expired /nashome krb key
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

PY=/exp/dune/data/users/liangliu/genie-dev/.pixi/envs/default/bin/python

# tune -> stem of the DONE 07-17 C12 spline gridlog + overlay label
declare -A STEM OVERLAY
STEM[GEM26_11a_05_000]=eminus_C12_20260717-140621; OVERLAY[GEM26_11a_05_000]=gem26_emq2lim
STEM[GEM26_22a_05_000]=eminus_C12_20260717-140625; OVERLAY[GEM26_22a_05_000]=gem26_emq2lim
STEM[GEM26_22b_05_000]=eminus_C12_20260717-140629; OVERLAY[GEM26_22b_05_000]=gem26_emq2lim
STEM[GEM21_11a_05_000]=eminus_C12_20260717-140632; OVERLAY[GEM21_11a_05_000]=gem21_emq2lim

DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for tune in GEM26_11a_05_000 GEM26_22a_05_000 GEM26_22b_05_000 GEM21_11a_05_000; do
  gl=jobsub-agent/jobsub-runs/gmkspl_grid-2026-07-17/${STEM[$tune]}.gridlog
  st=$(jq -r '.status' "$gl")
  [ "$st" = "done" ] || { echo "spline gridlog $gl not done (status=$st)" >&2; exit 1; }
  d=$(jq -r '.pnfs_output_dir' "$gl")
  dp=${d/\/pnfs\/dune\/scratch\//\/pnfs\/dune\/persistent\/}
  mapfile -t xmls < <(find "$dp" -name '*.xml' 2>/dev/null)
  [ ${#xmls[@]} -eq 1 ] || { echo "expected 1 persistent spline xml for $tune, got ${#xmls[@]}" >&2; exit 1; }
  echo "-- $tune"
  echo "   spline: ${xmls[0]}"
  $PY jobsub-agent/adapters/genie/run_gevgen_grid.py \
      --probe eminus --target C12 --tune "$tune" --genlist EM \
      -e 2.445 -n 100000 -N 100 \
      --cross-sections "${xmls[0]}" \
      --tarball-label genie_inclxx_q2guard --tune-tarball-label "${OVERLAY[$tune]}" \
      --expected-lifetime 24h $DRY || echo "SUBMIT FAILED: $tune" >&2
  sleep 2   # gridlog stems have 1 s resolution; same-second submits clobber
done

echo "done. Track with: $PY jobsub-agent/scripts/job.py list --active"

# Submitted 2026-07-26 (dry-run clean, then --go; 100 processes/tune):
#   GEM26_11a_05_000  gem26_emq2lim  gevgen_grid-eminus_C12_20260726-105638-3145f0  29313647@jobsub05
#   GEM26_22a_05_000  gem26_emq2lim  gevgen_grid-eminus_C12_20260726-105642-07b2c9  92764670@jobsub02
#   GEM26_22b_05_000  gem26_emq2lim  gevgen_grid-eminus_C12_20260726-105646-de11f9  92764671@jobsub02
#   GEM21_11a_05_000  gem21_emq2lim  gevgen_grid-eminus_C12_20260726-105650-1b755d  71090425@jobsub03
# The 105619/105621/105624/105626 pending records from the same minute are the
# dry-run artifacts, not real submissions.

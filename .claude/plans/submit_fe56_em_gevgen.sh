#!/bin/bash
# Fe56 full-EM gevgen campaign: 4 tunes x 10M events (100 procs x 100k), eminus
# at 2.445 GeV, genlist EM. Executes step 4 of
# .claude/plans/fe56-em-t05-fullem-splines.md with one deviation (user,
# 2026-07-16): splines are passed PNFS-direct via --cross-sections (jobsub -f
# by reference) -- no local pull, no CVMFS fe56_em_splines republish.
#
# Pre-flight done 2026-07-16 before drafting this: the four 07-15 spline XMLs
# verified in place on /pnfs -- 55 splines each, tgt 1000260560, channel sums
# at 2.445 GeV match t05 references (<1%), MEC/RES/DIS bit-identical across
# tunes, GEM21 SuSAv2 QE = 2.25e-4 (report-only).
#
# RUN THIS ON a dunegpvm (NOT EAF: jupyter pods firewall the jobsub schedds).
#
# --expected-lifetime 24h (uniform): 10x the events of the proven 07-14
# 10k-EMQE jobs + RES/DIS/MEC hadronization; 22b's SF-folded UnifiedQEL QE is
# the slow outlier. Clears the 8h default without 48h matching penalties.
#
# Modes:
#   ./submit_fe56_em_gevgen.sh          dry-run all 4 (adapter --dry-run)
#   ./submit_fe56_em_gevgen.sh --go     submit for real

set -uo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

GO=${1:-}
export BEARER_TOKEN_FILE=${BEARER_TOKEN_FILE:-/tmp/bt_u$(id -u)}
htgettoken -a htvaultprod.fnal.gov -i dune || { echo "token failed" >&2; exit 1; }

# tune -> stem of the DONE 07-15 spline gridlog (avoids the stale 181343
# pending record) and GXMLPATH overlay label
declare -A STEM OVERLAY
STEM[GEM26_11a_05_000]=eminus_Fe56_20260715-181408; OVERLAY[GEM26_11a_05_000]=gem26_emq2lim
STEM[GEM26_22a_05_000]=eminus_Fe56_20260715-181410; OVERLAY[GEM26_22a_05_000]=gem26_emq2lim
STEM[GEM26_22b_05_000]=eminus_Fe56_20260715-181412; OVERLAY[GEM26_22b_05_000]=gem26_emq2lim
STEM[GEM21_11a_05_000]=eminus_Fe56_20260715-181414; OVERLAY[GEM21_11a_05_000]=gem21_emq2lim

DRY=--dry-run; [ "$GO" = "--go" ] && DRY=
for tune in GEM26_11a_05_000 GEM26_22a_05_000 GEM26_22b_05_000 GEM21_11a_05_000; do
  gl=jobsub-agent/jobsub-runs/gmkspl_grid-2026-07-15/${STEM[$tune]}.gridlog
  st=$(jq -r '.status' "$gl")
  [ "$st" = "done" ] || { echo "spline gridlog $gl not done (status=$st)" >&2; exit 1; }
  d=$(jq -r '.pnfs_output_dir' "$gl")
  mapfile -t xmls < <(find "$d" -name '*.xml' 2>/dev/null)
  [ ${#xmls[@]} -eq 1 ] || { echo "expected 1 spline xml for $tune, got ${#xmls[@]}" >&2; exit 1; }
  echo "-- $tune"
  echo "   spline: ${xmls[0]}"
  pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
      --probe eminus --target Fe56 --tune "$tune" --genlist EM \
      -e 2.445 -n 100000 -N 100 \
      --cross-sections "${xmls[0]}" \
      --tarball-label genie_inclxx --tune-tarball-label "${OVERLAY[$tune]}" \
      --expected-lifetime 24h $DRY || echo "SUBMIT FAILED: $tune" >&2
  sleep 2   # gridlog stems have 1 s resolution; same-second submits clobber
done

echo "done. Track with: pixi run python jobsub-agent/scripts/job.py list --active"

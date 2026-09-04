#!/bin/bash
# rc-v380 spline set (samples A-G): gmkspl grid submissions, one per
# (tune, target, probe, genlist), -N 1 each.
# Plan: ~/.claude/plans/plan-a-multi-tune-gmkspl-abundant-snowglobe.md (2026-09-03);
# campaign log .claude/plans/rc-v380-spline-set.md.
# Modeled on submit_g18_02a_e5000_vn_splines.sh (resume guard, print/--go modes).
#
# Rows: sample tune target emax knots (see ROWS). Genlists: the 16 whose union is
# the tunes' Default (18 generators). IMD is skipped for rows with emax <= 10 GeV:
# inverse muon decay opens at 10.9 GeV, so gmkspl writes an empty spline there
# (local gate 2026-09-03, 0 splines at -e 5). CCDFR/NCDFR are skipped on all (nuclear)
# targets and LambdaCCQE for numu: physics-empty (0 splines locally, same in v3.6.2).
#
# Modes:
#   ./submit_rc_v380_splines.sh                 print every command (202 total)
#   ./submit_rc_v380_splines.sh --go            submit; the resume guard skips any
#                                               (tune,target,probe,genlist) that already has a
#                                               live or done gridlog for installation genie_rc
# Filters (comma lists): --sample A,B   --lists CCQE,CCDIS   --probes numu
#   --dry-run   pass the adapter's --dry-run (jobsub --no_submit; prints the argv)
# Lifetimes (seconds, env-overridable after the Stage-3 pilot):
#   LIFE_LONG  (default 43200) for CCQE CCDIS NCDIS Charm CCRES NCRES
#   LIFE_SHORT (default 14400) for everything else
# Needs a DUNE token (works from EAF):  htgettoken -a htvaultprod.fnal.gov -i dune

set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO"

GO=0; DRY=0; SAMPLES=""; LISTS=""; PROBES="numu numubar"
while [ $# -gt 0 ]; do
  case "$1" in
    --go)      GO=1 ;;
    --dry-run) DRY=1 ;;
    --sample)  SAMPLES=${2//,/ }; shift ;;
    --lists)   LISTS=${2//,/ };   shift ;;
    --probes)  PROBES=${2//,/ };  shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

TARBALL=genie_rc
INSTALL=genie_rc
PROJECT=rc_v380_splines
LIFE_LONG=${LIFE_LONG:-43200}
LIFE_SHORT=${LIFE_SHORT:-14400}

# sample tune target emax knots
ROWS=(
  "A G18_10a_02_11b  Ar40 10 100"
  "B AR23_20m_00_000 Ar40 10 100"
  "C AR23_20n_00_000 Ar40 10 100"
  "D G24_12a_00_000  C12   5 100"
  "D G24_12a_00_000  Ar40  5 100"
  "E AR25_20i_00_000 C12   3 100"
  "E AR25_20i_00_000 Ar40  3 100"
  "G G18_10a_02_11b  Fe56 50 200"
)
ALL_LISTS="CCQE NCEL CCMEC NCMEC CCRES NCRES CCDIS NCDIS CCCOHPION NCCOHPION CCDFR NCDFR NuEElastic IMD LambdaCCQE Charm"
LONG_LISTS=" CCQE CCDIS NCDIS Charm CCRES NCRES "   # CCQE: Nieves QE on Ar40 ~3 h at 100 knots (local probe 2026-09-03)

in_filter() {  # value filter-list ("" = no filter)
  local v=$1 f=$2
  [ -z "$f" ] || [[ " $f " == *" $v "* ]]
}
lifetime_for() {
  if [[ "$LONG_LISTS" == *" $1 "* ]]; then echo "$LIFE_LONG"; else echo "$LIFE_SHORT"; fi
}

NSUB=0; NSKIP=0
for row in "${ROWS[@]}"; do
  read -r sample tune target emax knots <<<"$row"
  in_filter "$sample" "$SAMPLES" || continue
  for probe in $PROBES; do
    for gl in $ALL_LISTS; do
      in_filter "$gl" "$LISTS" || continue
      if [ "$gl" = IMD ] && [ "$emax" -le 10 ]; then continue; fi
      # Physics-empty on these (nuclear) targets, verified locally 2026-09-03 (0 splines, also
      # in v3.6.2): diffractive production exists only on free nucleons; QEL-CC-LAMBDA needs an
      # antineutrino. Skipped so the merge coverage check stays strict.
      case "$gl" in CCDFR|NCDFR) continue ;; esac
      if [ "$gl" = LambdaCCQE ] && [ "$probe" = numu ]; then continue; fi
      life=$(lifetime_for "$gl")
      cmd=(pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py
           --probes "$probe" --targets "$target" --tune "$tune" --genlist "$gl"
           -e "$emax" -n "$knots" --tarball-label "$TARBALL" --installation "$INSTALL"
           --project "$PROJECT" -N 1 --expected-lifetime "$life")
      [ "$DRY" = 1 ] && cmd+=(--dry-run)
      NSUB=$((NSUB + 1))
      if [ "$GO" = 1 ]; then
        # Resume guard: skip if a live or terminal-success record exists for this
        # (tune, target, probe, genlist) on installation genie_rc.
        existing=$(jq -r --arg gl "$gl" --arg tgt "$target" --arg tune "$tune" --arg probe "$probe" \
          'select(.extra.genlist==$gl and .extra.target==$tgt and .extra.tune==$tune
                  and .extra.probe==$probe and .extra.installation=="genie_rc"
                  and (.status=="submitted" or .status=="running" or .status=="held"
                       or .status=="done" or .status=="partial"))|.jobid' \
          jobsub-agent/jobsub-runs/gmkspl_grid-*/*.gridlog 2>/dev/null | head -1) || true
        if [ -n "$existing" ]; then
          echo "[$NSUB/skip] $sample $tune $target $probe $gl (already: $existing)"
          NSKIP=$((NSKIP + 1))
          continue
        fi
        echo "[$NSUB] $sample $tune $target $probe $gl life=${life}s"
        "${cmd[@]}"
        sleep 1   # stems are second-granular; keep them unique
      else
        printf '%q ' "${cmd[@]}"; echo
      fi
    done
  done
done
echo "# $NSUB submissions considered, $NSKIP skipped by the resume guard$( [ "$GO" = 1 ] || echo '; re-run with --go to submit')" >&2

#!/bin/bash
# Stage-5 merge for the rc-v380 spline set: per (tune, target) pull every done
# gmkspl XML of this campaign (installation genie_rc, project rc_v380_splines),
# stage them, and gspladd them into one file holding numu + numubar and all
# genlists. Campaign log: .claude/plans/rc-v380-spline-set.md.
#
#   ./merge_rc_v380_splines.sh [--sample A,B] [--no-pull]
#
# Output: $PRODUCT_BASE/<TUNE>/gxspl-<Target>-numu-numubar-k<knots>-e<emax>.xml
# Staging (kept for provenance): $PRODUCT_BASE/<TUNE>/work/<Target>/*.xml
# Prints found-vs-expected job counts, missing (probe, genlist) combos, spline
# count, duplicate-key count, nknots set, genie_tune name and sha256.

set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO"

GENIEBASE=/exp/dune/app/users/liangliu/GENIE/GENIE_RC
PRODUCT_BASE=/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380
SAMPLES=""; PULL=1
while [ $# -gt 0 ]; do
  case "$1" in
    --sample)  SAMPLES=${2//,/ }; shift ;;
    --no-pull) PULL=0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

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
PROBES="numu numubar"

in_filter() { local v=$1 f=$2; [ -z "$f" ] || [[ " $f " == *" $v "* ]]; }

for row in "${ROWS[@]}"; do
  read -r sample tune target emax knots <<<"$row"
  in_filter "$sample" "$SAMPLES" || continue
  echo "================ $sample $tune $target (-e $emax -n $knots) ================"
  stage="$PRODUCT_BASE/$tune/work/$target"
  merged="$PRODUCT_BASE/$tune/gxspl-${target}-numu-numubar-k${knots}-e${emax}.xml"
  mkdir -p "$stage"

  # Expected (probe, genlist) combos for this row (IMD only when emax > 10 GeV).
  expected=()
  for probe in $PROBES; do
    for gl in $ALL_LISTS; do
      if [ "$gl" = IMD ] && [ "$emax" -le 10 ]; then continue; fi
      # Same physics-empty skips as submit_rc_v380_splines.sh (DFR on nuclei; Lambda for numu).
      case "$gl" in CCDFR|NCDFR) continue ;; esac
      if [ "$gl" = LambdaCCQE ] && [ "$probe" = numu ]; then continue; fi
      expected+=("$probe/$gl")
    done
  done

  # Done gridlogs of this campaign for this (tune, target).
  found=()
  for log in jobsub-agent/jobsub-runs/gmkspl_grid-*/*.gridlog; do
    line=$(jq -r --arg tune "$tune" --arg tgt "$target" \
      'select(.extra.tune==$tune and .extra.target==$tgt and .extra.installation=="genie_rc"
              and .status=="done" and ((.outputs.pnfs_output_dir // .pnfs_output_dir // "") | test("/rc_v380_splines/")))
       | [.jobid, .extra.probe, .extra.genlist] | @tsv' "$log" 2>/dev/null) || true
    [ -n "$line" ] || continue
    IFS=$'\t' read -r jobid probe gl <<<"$line"
    found+=("$probe/$gl")
    if [ "$PULL" = 1 ]; then
      pixi run python jobsub-agent/scripts/job.py pull "$jobid" --suffix .xml 2>&1 | grep -v "WARN Using local manifest" || true
    fi
    local_dir=$(jq -r '.local_output_dir // ""' "$log")
    n=0
    if [ -n "$local_dir" ] && [ -d "$local_dir" ]; then
      while IFS= read -r -d '' x; do
        cp -f "$x" "$stage/${probe}_${gl}_$(basename "$x")"; n=$((n + 1))
      done < <(find "$local_dir" -name '*.xml' -print0)
    fi
    echo "  $probe $gl  $jobid  xml=$n"
  done

  # Local fallback: combos produced on this pod by genie-agent's run_gmkspl.py with
  # --label rc_v380_splines (same genie_rc binaries; used for row E CCQE, whose SF-based
  # QE integration is too slow for a grid lifetime). Grid results take precedence.
  for e in "${expected[@]}"; do
    [[ " ${found[*]} " == *" $e "* ]] && continue
    probe=${e%%/*}; gl=${e##*/}
    for llog in genie-agent/genie-runs/${tune}-*/*.log; do
      x=$(jq -r --arg tune "$tune" --arg tgt "$target" --arg probe "$probe" --arg gl "$gl" \
        'select(.runtype=="gmkspl" and .inputs.label=="rc_v380_splines" and .inputs.tune==$tune
                and .inputs.genlist==$gl and (.inputs.targets|join(","))==$tgt
                and (.inputs.probes|join(","))==$probe and .returncode==0
                and (.outputs.spline_count // 0) > 0) | .outputs.primary_output' "$llog" 2>/dev/null) || true
      if [ -n "$x" ] && [ -f "$x" ]; then
        cp -f "$x" "$stage/${probe}_${gl}_local_$(basename "$x")"
        found+=("$e"); echo "  $probe $gl  LOCAL $(basename "$llog" .log)  xml=1"
        break
      fi
    done
  done

  # Coverage report.
  missing=()
  for e in "${expected[@]}"; do
    [[ " ${found[*]} " == *" $e "* ]] || missing+=("$e")
  done
  echo "  done jobs: ${#found[@]} / expected ${#expected[@]}"
  if [ ${#missing[@]} -gt 0 ]; then
    echo "  MISSING: ${missing[*]}"
    echo "  -> not merging $tune $target (re-run the wave with --go to resubmit)"
    continue
  fi

  # Merge with gspladd under the install's own env (clean shell, not inside pixi).
  env -i HOME="$HOME" USER="$USER" PATH=/usr/local/bin:/usr/bin:/bin \
    bash --noprofile --norc -c "source $GENIEBASE/setup_env.sh >/dev/null 2>&1 && gspladd -d '$stage' -o '$merged'" \
    > "$merged.gspladd.log" 2>&1 || { echo "  gspladd FAILED, see $merged.gspladd.log"; continue; }

  # Checks.
  nspl=$(grep -c '<spline ' "$merged" || true)
  ndup=$(grep -o 'spline name="[^"]*"' "$merged" | sort | uniq -d | wc -l)
  nknot=$(grep -o 'nknots="[0-9]*"' "$merged" | sort -u | tr '\n' ' ')
  tunes=$(grep -o 'genie_tune name="[^"]*"' "$merged" | sort -u | tr '\n' ' ')
  sha=$(sha256sum "$merged" | cut -d' ' -f1)
  echo "  merged: $merged"
  echo "  splines=$nspl duplicates=$ndup nknots={$nknot} tune={$tunes}"
  echo "  sha256=$sha"
done

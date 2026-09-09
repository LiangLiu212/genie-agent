#!/bin/bash
# Sample F (GDM18_00a_00_000, Ar40, DM beam) of the rc-v380 spline campaign: merge the
# per-process gmkspl_dm splines produced LOCALLY by genie-agent's run_gmkspl_dm.py
# (--label rc_v380_splines) into one product with gspladd, and run the same checks as
# merge_rc_v380_splines.sh (which is hard-wired to numu/numubar grid jobs).
# Campaign log: .claude/plans/rc-v380-spline-set.md.
#
# Spline keys carry NO DM mass / mediator ratio / coupling (Interaction::AsString gives
# "dm;tgt:...;proc:..."), so inputs are selected on the runlogs and the values are written
# into the product name:  gxspl-<T>-dm-m<mass>-z<z>-g<g>-k<knots>-e<Emax>.xml
#
#   ./merge_rc_v380_dm_splines.sh --mass <GeV> [--med-ratio 0.5] [--zp-coupling 1.0]
#        [--knots 100] [--emax 10] [--target Ar40] [--tune GDM18_00a_00_000]
#        [--label rc_v380_splines] [--lists "DMEL DMDIS DME DMRES"]
set -euo pipefail
cd "$(dirname "$0")/../.."          # repo root (genie-dev)

GENIEBASE=/exp/dune/app/users/liangliu/GENIE/GENIE_RC
PRODUCT_ROOT=/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380

TUNE=GDM18_00a_00_000; TARGET=Ar40; LABEL=rc_v380_splines
MASS=""; Z=0.5; G=1.0; KNOTS=100; EMAX=10
LISTS="DMEL DMDIS DME DMRES"
while [ $# -gt 0 ]; do
  case "$1" in
    --mass) MASS=$2; shift 2;;        --med-ratio) Z=$2; shift 2;;
    --zp-coupling) G=$2; shift 2;;    --knots) KNOTS=$2; shift 2;;
    --emax) EMAX=$2; shift 2;;        --target) TARGET=$2; shift 2;;
    --tune) TUNE=$2; shift 2;;        --label) LABEL=$2; shift 2;;
    --lists) LISTS=$2; shift 2;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
[ -n "$MASS" ] || { echo "--mass <GeV> is required (the DM mass the splines were built with)" >&2; exit 2; }

tag="${TARGET}-dm-m${MASS}-z${Z}-g${G}"
stage="$PRODUCT_ROOT/$TUNE/work/$tag"
merged="$PRODUCT_ROOT/$TUNE/gxspl-${tag}-k${KNOTS}-e${EMAX}.xml"
mkdir -p "$stage"
echo "== $TUNE $TARGET  m=$MASS z=$Z g=$G  knots=$KNOTS Emax=$EMAX  lists: $LISTS"

# One finished, non-empty run per list, matching every DM parameter (newest wins).
missing=(); expected_total=0
for gl in $LISTS; do
  best=""; best_t=""
  for llog in genie-agent/genie-runs/${TUNE}-*/*.log; do
    row=$(jq -r --arg tune "$TUNE" --arg tgt "$TARGET" --arg gl "$gl" --arg label "$LABEL" \
             --argjson m "$MASS" --argjson z "$Z" --argjson g "$G" --argjson k "$KNOTS" --argjson e "$EMAX" \
      'select(.runtype=="gmkspl_dm" and .inputs.label==$label and .inputs.tune_resolved==$tune
              and .inputs.genlist_resolved==$gl
              and ((.inputs.canonical_targets|join(","))==$tgt)
              and .inputs.dm_mass==$m and .inputs.med_ratio==$z and .inputs.zp_coupling==$g
              and .inputs.n_knots==$k and .inputs.max_energy==$e
              and .returncode==0 and (.outputs.spline_count // 0) > 0)
       | [(.finished // ""), .outputs.primary_output, .outputs.stem, .outputs.spline_count, .jobid] | @tsv' \
      "$llog" 2>/dev/null) || true
    [ -n "$row" ] || continue
    t=$(cut -f1 <<<"$row")
    if [ -z "$best" ] || [[ "$t" > "$best_t" ]]; then best=$row; best_t=$t; fi
  done
  if [ -z "$best" ]; then missing+=("$gl"); echo "  $gl  MISSING"; continue; fi
  xml=$(cut -f2 <<<"$best"); stem=$(cut -f3 <<<"$best"); n=$(cut -f4 <<<"$best"); jid=$(cut -f5 <<<"$best")
  [ -f "$xml" ] || { missing+=("$gl"); echo "  $gl  xml not on disk: $xml"; continue; }
  cp -f "$xml" "$stage/${gl}_${stem}.xml"
  expected_total=$((expected_total + n))
  echo "  $gl  $jid  splines=$n"
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "  MISSING lists: ${missing[*]} -> not merging (run run_gmkspl_dm.py --label $LABEL for them)"; exit 3
fi

# Merge with gspladd under the install's own env (clean shell, not inside pixi).
env -i HOME="$HOME" USER="$USER" PATH=/usr/local/bin:/usr/bin:/bin \
  bash --noprofile --norc -c "source $GENIEBASE/setup_env.sh >/dev/null 2>&1 && gspladd -d '$stage' -o '$merged'" \
  > "$merged.gspladd.log" 2>&1 || { echo "  gspladd FAILED, see $merged.gspladd.log"; exit 4; }

# Checks (same as the neutrino merge) + spline-count conservation.
nspl=$(grep -c '<spline ' "$merged" || true)
ndup=$(grep -o 'spline name="[^"]*"' "$merged" | sort | uniq -d | wc -l)
nknot=$(grep -o 'nknots="[0-9]*"' "$merged" | sort -u | tr '\n' ' ')
tunes=$(grep -o 'genie_tune name="[^"]*"' "$merged" | sort -u | tr '\n' ' ')
ntune=$(grep -c '<genie_tune ' "$merged" || true)
sha=$(sha256sum "$merged" | cut -d' ' -f1)
echo "  merged: $merged"
echo "  splines=$nspl (inputs sum $expected_total) duplicates=$ndup nknots={$nknot} tune_sections=$ntune tune={$tunes}"
echo "  sha256=$sha"
ok=1
[ "$nspl" = "$expected_total" ] || { echo "  CHECK FAILED: spline count != sum of inputs"; ok=0; }
[ "$ndup" = 0 ] || { echo "  CHECK FAILED: duplicate keys"; ok=0; }
[ "$ntune" = 1 ] || { echo "  CHECK FAILED: expected one genie_tune section"; ok=0; }
[ "$nknot" = "nknots=\"$KNOTS\" " ] || { echo "  CHECK FAILED: nknots != $KNOTS"; ok=0; }
[ $ok = 1 ] && echo "  ALL CHECKS OK"

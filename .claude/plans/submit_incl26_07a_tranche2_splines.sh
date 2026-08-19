#!/bin/bash
# Tranche-2 gmkspl grid submissions for the INCL26_07a_00_000 NUsmall spline set.
# Plan: .claude/plans/incl26_07a-xsec-spline-set.md (Stage 2). Drafted 2026-07-03.
#
# Tranche 1 (2026-07-01) built free-n, H1, C12, O16, Ar40, Fe56 (15 genlists,
# 250 knots, 0.01-1000 GeV, 6 nu flavors). This script submits the remaining
# 45 NUsmall isotopes for the same 15 genlists with identical settings.
#
# Chunk sizes are calibrated from tranche-1 wall times (PNFS mtime - submit time,
# so upper bounds that include queue wait) under two hard constraints:
#   * every job must fit comfortably inside --expected-lifetime: the tranche-1
#     6-target NCDIS job was evicted at exactly its 20 h lifetime and restarted
#     from scratch (NumJobStarts=2) -- gmkspl has no checkpointing, so an
#     over-lifetime job can loop forever;
#   * at most 6 targets per job: the worker output filename embeds the full
#     probe+target symbol AND PDG lists (tranche-1 6-target names were already
#     ~237 of the 255-char NAME_MAX; 45 targets crashes the adapter outright).
#
#   genlist      t1 wall (6 tgt)  chunk  jobs  est/job (upper bound)
#   CCQE          4.5-7.2 h/tgt      1     45   ~5-8 h   (per-target, per plan)
#   NCDIS         >47 h, evicted     1     45   ~3-8 h
#   CCMEC         38h41              2     23   ~13 h
#   CCDFR         33h22              2     23   ~11 h
#   CCDIS         16h15              4     12   ~11 h
#   CCCOHPION     12h25              5      9   ~10 h
#   NCDFR         12h42              5      9   ~11 h
#   CCRES         10h12              6      8   ~10 h
#   NCCOHPION      8h55              6      8   ~9 h
#   NCRES          7h21              6      8   ~7.5 h
#   NCEL           0h05              6      8   minutes
#   NCMEC          0h07              6      8   minutes
#   NuEElastic     0h04              6      8   minutes
#   IMD            0h06              6      8   minutes
#   LambdaCCQE     0h04              6      8   minutes
#                                        ----
#                                         230 submissions (~1-2 h to submit)
#
# Modes:
#   ./submit_incl26_07a_tranche2_splines.sh                  print all commands (no records written)
#   ./submit_incl26_07a_tranche2_splines.sh --go             submit for real
#   ./submit_incl26_07a_tranche2_splines.sh --redo-t1-ncdis  ALSO queue per-target NCDIS for the 6
#                                                            tranche-1 targets (use only after
#                                                            cancelling the looping tranche-1 NCDIS job)
#
# Track afterwards with the jobsub-jobs skill:
#   pixi run python jobsub-agent/scripts/job.py list --active
#   jq -r 'select(.extra.genlist=="CCQE")|[.jobid,.status]|@tsv' jobsub-agent/jobsub-runs/*/*.gridlog

set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
cd "$REPO"

GO=0
REDO_T1_NCDIS=0
for arg in "$@"; do
  case "$arg" in
    --go) GO=1 ;;
    --redo-t1-ncdis) REDO_T1_NCDIS=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

PROBES="numu,numubar,nue,nuebar,nutau,nutaubar"
TUNE="INCL26_07a_00_000"
TARBALL="genie_inclxx"
INSTALL="genie_inclxx"
KNOTS=250
EMAX=1000

# The 45 NUsmall isotopes not covered by tranche 1, in AR23 isotopes.cfg order
# (NUsmall = the 'reduced' rows of AR2320i00000-k250-e1000/data/isotopes.cfg;
# tranche 1 already built: free-n H1 C12 O16 Ar40 Fe56).
TARGETS45=(
  H2 He4 Be9 B11 N14 F19 Na23 Mg24 Al27 Si28
  P31 S32 Cl35 Cl36 Cl37 K39 Ca40 Ti48 V51 Cr52
  Mn55 Fe54 Fe57 Fe58 Ni58 Ni59 Ni60 Cu63 Cu64 Cu65
  Zn64 Zn65 Br80 Kr84 Nb93 Mo96 Ru101 Sn119 Xe131 Ba137
  Gd158 W183 W184 Au197 Pb207
)

# Tranche-1 targets, for the optional --redo-t1-ncdis band.
TARGETS_T1=(C12 O16 Ar40 Fe56 1000000010 H1)

NSUB=0

submit_chunks() {  # genlist chunk_size expected_lifetime_s target...
  local genlist=$1 chunk=$2 lifetime=$3; shift 3
  local -a tgts=("$@")
  local i n=${#tgts[@]}
  for ((i = 0; i < n; i += chunk)); do
    local csv
    csv=$(IFS=,; echo "${tgts[*]:i:chunk}")
    local -a cmd=(pixi run python jobsub-agent/adapters/genie/run_gmkspl_grid.py
      --probes "$PROBES" --targets "$csv" --tune "$TUNE" --genlist "$genlist"
      --tarball-label "$TARBALL" --installation "$INSTALL"
      -n "$KNOTS" -e "$EMAX" -N 1 --expected-lifetime "$lifetime")
    NSUB=$((NSUB + 1))
    if [ "$GO" = 1 ]; then
      # Resume guard: skip if a live/terminal-success record already exists for
      # this (genlist, target set, tune) — makes a partial campaign rerunnable.
      local label=${csv//,/-} existing
      existing=$(jq -r --arg gl "$genlist" --arg tgt "$label" --arg tune "$TUNE" \
        'select(.extra.genlist==$gl and .extra.target==$tgt and .extra.tune==$tune
                and (.status=="submitted" or .status=="running" or .status=="held"
                     or .status=="done" or .status=="partial"))|.jobid' \
        jobsub-agent/jobsub-runs/gmkspl_grid-*/*.gridlog 2>/dev/null | head -1) || true
      if [ -n "$existing" ]; then
        echo "[$NSUB/skip] $genlist <- $csv (already: $existing)"
        continue
      fi
      echo "[$NSUB] $genlist <- $csv"
      "${cmd[@]}"
      sleep 1   # stems are second-granular; keep them unique
    else
      printf '%q ' "${cmd[@]}"; echo
    fi
  done
}

# Heavy bands first so the long jobs enter the queue earliest.
submit_chunks CCQE       1 72000 "${TARGETS45[@]}"
submit_chunks NCDIS      1 72000 "${TARGETS45[@]}"
submit_chunks CCMEC      2 72000 "${TARGETS45[@]}"
submit_chunks CCDFR      2 72000 "${TARGETS45[@]}"
submit_chunks CCDIS      4 72000 "${TARGETS45[@]}"
submit_chunks CCCOHPION  5 72000 "${TARGETS45[@]}"
submit_chunks NCDFR      5 72000 "${TARGETS45[@]}"
submit_chunks CCRES      6 72000 "${TARGETS45[@]}"
submit_chunks NCCOHPION  6 72000 "${TARGETS45[@]}"
submit_chunks NCRES      6 72000 "${TARGETS45[@]}"
submit_chunks NCEL       6 14400 "${TARGETS45[@]}"
submit_chunks NCMEC      6 14400 "${TARGETS45[@]}"
submit_chunks NuEElastic 6 14400 "${TARGETS45[@]}"
submit_chunks IMD        6 14400 "${TARGETS45[@]}"
submit_chunks LambdaCCQE 6 14400 "${TARGETS45[@]}"

if [ "$REDO_T1_NCDIS" = 1 ]; then
  echo "# redo band: per-target NCDIS for the tranche-1 targets" >&2
  echo "# (cancel the looping tranche-1 NCDIS job first:" >&2
  echo "#  pixi run python jobsub-agent/scripts/job.py cancel gmkspl_grid-numu-numubar-nue-nuebar-nutau-nutaubar_C12-Ar40-O16-Fe56-1000000010-H1_20260701-141027-694b4a)" >&2
  submit_chunks NCDIS 1 72000 "${TARGETS_T1[@]}"
fi

if [ "$GO" = 1 ]; then
  echo "submitted $NSUB jobs"
else
  echo "# $NSUB submissions total; re-run with --go to submit" >&2
fi

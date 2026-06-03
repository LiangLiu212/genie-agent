#!/usr/bin/env bash
# EM-QES 10M-event production: 6 beam settings x 3 targets = 18 submits.
# Each submit: -n 500000 -N 20  => 10.0M events, ~1.1-1.3 h/process, 20 processes.
# Splines already on /pnfs (tunes 04-08, shared across targets). Run from repo root.
set -euo pipefail
cd /exp/dune/data/users/liangliu/genie-dev

DRYRUN="${1:-}"          # pass --dry-run to inspect without submitting
N=20
NEV=500000
COMMON="--tarball-label genie_dev --tune-tarball-label gem21_emq2lim --genlist EMQE"

SPLDIR=/pnfs/dune/scratch/users/liangliu/jobsub-agent/prd_paper/EM/genie_dev
SPL04="$SPLDIR/GEM21_11a_04_000/eminus_C12-Fe56-Au197_20260601-104756_spl/11_1000060120-1000260560-1000791970_GEM21_11a_04_000/0000/spl_grid_eminus_C12-Fe56-Au197_20260601-104756_11_1000060120-1000260560-1000791970_GEM21_11a_04_000_EMQE_e10.0gev_n30_p0000_c91653112.xml"
SPL05="$SPLDIR/GEM21_11a_05_000/eminus_C12-Fe56-Au197_20260601-123553_spl/11_1000060120-1000260560-1000791970_GEM21_11a_05_000/0000/spl_grid_eminus_C12-Fe56-Au197_20260601-123553_11_1000060120-1000260560-1000791970_GEM21_11a_05_000_EMQE_e10.0gev_n30_p0000_c28031685.xml"
SPL06="$SPLDIR/GEM21_11a_06_000/eminus_C12-Fe56-Au197_20260601-123555_spl/11_1000060120-1000260560-1000791970_GEM21_11a_06_000/0000/spl_grid_eminus_C12-Fe56-Au197_20260601-123555_11_1000060120-1000260560-1000791970_GEM21_11a_06_000_EMQE_e10.0gev_n30_p0000_c70236762.xml"
SPL07="$SPLDIR/GEM21_11a_07_000/eminus_C12-Fe56-Au197_20260601-123558_spl/11_1000060120-1000260560-1000791970_GEM21_11a_07_000/0000/spl_grid_eminus_C12-Fe56-Au197_20260601-123558_11_1000060120-1000260560-1000791970_GEM21_11a_07_000_EMQE_e10.0gev_n30_p0000_c91653305.xml"
SPL08="$SPLDIR/GEM21_11a_08_000/eminus_C12-Fe56-Au197_20260601-123600_spl/11_1000060120-1000260560-1000791970_GEM21_11a_08_000/0000/spl_grid_eminus_C12-Fe56-Au197_20260601-123600_11_1000060120-1000260560-1000791970_GEM21_11a_08_000_EMQE_e10.0gev_n30_p0000_c70236763.xml"

# 6 beam settings: tune  energy  spline
SETTINGS=(
  "GEM21_11a_04_000 2.445 $SPL04"
  "GEM21_11a_04_000 0.845 $SPL04"
  "GEM21_11a_05_000 2.445 $SPL05"
  "GEM21_11a_06_000 3.245 $SPL06"
  "GEM21_11a_07_000 1.645 $SPL07"
  "GEM21_11a_08_000 3.245 $SPL08"
)
TARGETS=(C12 Fe56 Au197)

for s in "${SETTINGS[@]}"; do
  read -r TUNE ENERGY SPL <<<"$s"
  for TGT in "${TARGETS[@]}"; do
    echo ">>> $TGT  $TUNE  E=$ENERGY  (n=$NEV N=$N)"
    pixi run python jobsub-agent/adapters/genie/run_gevgen_grid.py \
        --probe eminus --target "$TGT" -n "$NEV" -e "$ENERGY" \
        --cross-sections "$SPL" --tune "$TUNE" $COMMON -N "$N" $DRYRUN
  done
done

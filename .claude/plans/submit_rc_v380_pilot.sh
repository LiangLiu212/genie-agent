#!/bin/bash
# Stage-2 smoke / Stage-3 pilot for the rc-v380 spline set. Thin wrapper over the
# filters of submit_rc_v380_splines.sh (no duplicated submission logic), so the
# smoke and pilot jobs are ordinary matrix jobs that the wave's resume guard
# later recognises and skips.
#
#   --smoke : row A, numu Ar40 CCQE              (Pythia8 / ABI gate on a worker)
#   --pilot : row A, numu Ar40 CCDIS, Charm, NCDIS + row G, numu Fe56 CCDIS
#             (wall times size LIFE_LONG / LIFE_SHORT for the wave)
# Extra args (--go, --dry-run) are passed through.

set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

MODE=""; PASS=()
for a in "$@"; do
  case "$a" in
    --smoke|--pilot) MODE=$a ;;
    *) PASS+=("$a") ;;
  esac
done

case "$MODE" in
  --smoke)
    "$HERE/submit_rc_v380_splines.sh" --sample A --probes numu --lists CCQE "${PASS[@]}"
    ;;
  --pilot)
    "$HERE/submit_rc_v380_splines.sh" --sample A --probes numu --lists CCDIS,Charm,NCDIS "${PASS[@]}"
    "$HERE/submit_rc_v380_splines.sh" --sample G --probes numu --lists CCDIS "${PASS[@]}"
    ;;
  *)
    echo "usage: $0 --smoke|--pilot [--go] [--dry-run]" >&2; exit 2
    ;;
esac

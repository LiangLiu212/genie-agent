#!/bin/bash
# Stage-6 mirror of the rc-v380 merged spline products to persistent dCache.
# Products live on /exp/dune/data (EAF cannot write /pnfs/dune/persistent with a
# token), so the copy runs on a dunegpvm over ssh (needs a valid kinit ticket);
# sha256 is verified on both sides. Campaign log: .claude/plans/rc-v380-spline-set.md.
#   ./mirror_rc_v380_splines.sh            print what would be copied
#   ./mirror_rc_v380_splines.sh --go       copy + verify
set -euo pipefail
SRC=/exp/dune/data/users/liangliu/runarea/genie_xsec/rc-v380
DST=/pnfs/dune/persistent/users/liangliu/genie_xsec/rc-v380
GPVM=dunegpvm04.fnal.gov
GO=0; [ "${1:-}" = "--go" ] && GO=1
files=$(cd "$SRC" && ls */gxspl-*.xml)
echo "# $(echo "$files" | wc -l) files: $SRC -> $GPVM:$DST"
[ "$GO" = 1 ] || { echo "$files" | sed "s|^|  |"; echo "# re-run with --go (needs kinit)"; exit 0; }
klist -s || { echo "no Kerberos ticket: run kinit first" >&2; exit 3; }
ssh -o BatchMode=yes -o GSSAPIAuthentication=yes "$GPVM" "set -e; for f in $(echo $files | tr '\n' ' '); do mkdir -p $DST/\$(dirname \$f); cp -f $SRC/\$f $DST/\$f; done; cd $DST && sha256sum */gxspl-*.xml" > /tmp/rc_v380_mirror_persistent.sha 2>/tmp/rc_v380_mirror.err || { cat /tmp/rc_v380_mirror.err >&2; exit 4; }
(cd "$SRC" && sha256sum */gxspl-*.xml) > /tmp/rc_v380_mirror_local.sha
if diff <(sort /tmp/rc_v380_mirror_local.sha) <(sort /tmp/rc_v380_mirror_persistent.sha) >/dev/null; then
  echo "MIRROR OK: $(wc -l < /tmp/rc_v380_mirror_persistent.sha) files, sha256 identical on both sides"; cat /tmp/rc_v380_mirror_persistent.sha
else
  echo "MIRROR MISMATCH" >&2; diff <(sort /tmp/rc_v380_mirror_local.sha) <(sort /tmp/rc_v380_mirror_persistent.sha) >&2; exit 5
fi

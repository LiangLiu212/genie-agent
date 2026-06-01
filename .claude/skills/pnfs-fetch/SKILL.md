---
name: pnfs-fetch
description: Copy grid output files (gst/ghep ROOT, spline XML, logs) off /pnfs dCache to a local path for analysis, using ifdh from the larsoft spack env. Use when reading a /pnfs file stalls (NFS hang), when uproot/ROOT/cp/dd time out on a /pnfs path, or when you need grid job outputs locally to plot/analyze them. NOT for steering jobs (use jobsub-jobs) — this is the raw file-fetch escape hatch when scripts/job.py pull is unavailable (no ifdh on PATH).
---

# Fetching files off /pnfs (dCache)

On this host, `/pnfs/dune/scratch/...` is mounted over NFS but **direct reads
stall** — plain `cp`, `dd`, `cat` on a large file, and `uproot.open()` /
`xrdcp` against a hand-rolled door URL all hang. The reliable path is **`ifdh
cp`**, the same tool the grid workers use to stage outputs. `scripts/job.py
pull` wraps this but needs `ifdh` on PATH; when it isn't (bare login shell),
set it up yourself from the larsoft spack env.

## Setup (gives you `ifdh`)
Same recipe as the grid worker templates
(`jobsub-agent/adapters/genie/templates/*.sh`):
```bash
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh   # ~1 s -> `spack` on PATH
spack load --first ifdhc                                  # ~3 s -> `ifdh` on PATH
```
- Run this in a **normal** shell, not `env -i` — stripping the environment makes
  `setup-env.sh` / `spack load` silently hang/produce nothing.
- A valid bearer token must be present: `export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)`
  (refresh with `htgettoken -a htvaultprod.fnal.gov -i dune` if expired).

## Copy
```bash
ifdh cp /pnfs/.../file.gst.root /local/dir/file.gst.root   # single file
ifdh cp -D /pnfs/.../file.gst.root /local/dir/             # -D = dest is a dir
```
- `ifdh cp` (no `-D`) takes **src dst**; `-D` takes **src... destdir/**.
- `export IFDH_CP_MAXRETRIES=1` to fail fast instead of long retry loops.
- Locate files first with `find /pnfs/... -name '*.gst.root'` (the NFS *listing*
  works fine; only bulk *reads* stall), then loop `ifdh cp` over the list.

## Batch pattern (verified)
```bash
export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)
source /cvmfs/larsoft.opensciencegrid.org/setup-env.sh >/dev/null 2>&1
spack load --first ifdhc >/dev/null 2>&1
export IFDH_CP_MAXRETRIES=1
while read F; do
  ifdh cp "$F" "/tmp/$(basename "$F")" && echo "OK $(basename "$F")" || echo "FAIL $F"
done < filelist.txt
```
18 small (~0.3–0.6 MB) gst files copy in well under a minute this way.

## Notes
- The grid adapter marks a gevgen/gmkspl job `failed` if the **fetchlog** step
  hits a transient `landscape.fnal.gov` 500 and the fallback PNFS count returns
  0 — even when the output files are present. Verify with `find /pnfs/...` /
  `ifdh cp` before trusting a `failed` status (see jobsub-jobs).
- `ifdh` is at `…/spack-fnal-v1.1.0/…/ifdhc-<ver>/bin/ifdh` after the load;
  `xrdcp` exists too but the dCache door URL mapping is fiddly — prefer `ifdh`.

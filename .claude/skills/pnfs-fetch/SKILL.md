---
name: pnfs-fetch
description: Stream grid output ROOT files (gst/ghep) off /pnfs dCache over XRootD with uproot — no local copy — via the dCache door root://fndca1.fnal.gov:1094 and the /pnfs->/pnfs/fnal.gov/usr namespace mapping. Use when reading a /pnfs file stalls (NFS hang), when cp/dd/cat/uproot.open on a bare /pnfs path time out, or when you need to read grid job outputs (uproot/ROOT) for analysis/plotting. Needs xrootd+fsspec-xrootd in the pixi env and a valid BEARER_TOKEN_FILE. NOT for steering jobs (use jobsub-jobs).
---

# Reading files off /pnfs (dCache) — XRootD streaming

On this host `/pnfs/dune/scratch/...` is mounted over NFS but **direct data reads
stall**: plain `cp`, `dd`, `cat` on a large file and `uproot.open("/pnfs/...")`
all hang. The fix is **not to copy** — stream the file over **XRootD** with the
correct dCache door URL. (The old `ifdh cp` recipe is abandoned: streaming needs
no local stage, no larsoft/spack env, and no per-file copy.) Verified at the
~10M-event / multi-GB scale.

> Directory *listing* over NFS works fine — only bulk *reads* stall. So **list
> locally, read over XRootD**.

## The URL mapping (the part people get wrong)
The earlier "uproot/xrdcp hang on /pnfs" was a **wrong door URL**, not a real
limitation. Fermilab dCache maps the `/pnfs` namespace under `/pnfs/fnal.gov/usr`:

```
/pnfs/dune/scratch/users/...   ->   root://fndca1.fnal.gov:1094//pnfs/fnal.gov/usr/dune/scratch/users/...
```
i.e. insert `/fnal.gov/usr` after `/pnfs`, prefix the door, **double slash**
before the absolute path:
```python
def xrootd_url(p, door="fndca1.fnal.gov:1094"):
    return f"root://{door}/" + p.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)
```

## Setup
1. **pixi deps** (one-time; uproot opens `root://` only with the XRootD binding):
   ```bash
   pixi add xrootd fsspec-xrootd      # works on the py3.14 env
   ```
2. **Auth** — a valid bearer token for the dCache XRootD `ztn` plugin:
   ```bash
   export BEARER_TOKEN_FILE=/run/user/$(id -u)/bt_u$(id -u)   # or your session token
   # refresh if expired (token lives ~hours):
   htgettoken -i dune                  # -a htvaultprod.fnal.gov if needed
   ```

## Stream with uproot
```python
import uproot
url = xrootd_url("/pnfs/dune/scratch/users/$USER/.../file.gst.root")
t = uproot.open(url)["gst"]                 # opens over XRootD
print(t.num_entries)                        # streams the TTree metadata
q2 = t["Q2"].array(entry_stop=5)            # streams data on demand

# many files: list locally (NFS, fast) -> map to URLs -> stream
import glob
files = {xrootd_url(p): "gst"
         for p in sorted(glob.glob("/pnfs/.../<run>/*/*.gst.root"))}
total = sum(n for _, _, n in uproot.num_entries(files))      # entry count, all files
for chunk in uproot.iterate(files, expressions=["Q2"], step_size="100 MB", library="np"):
    ...                                     # memory-safe chunked stream
```

## CLI (listing / a real copy if you must)
```bash
xrdfs fndca1.fnal.gov:1094 ls  /pnfs/fnal.gov/usr/dune/scratch/users/$USER/...   # list over XRootD
xrdcp root://fndca1.fnal.gov:1094//pnfs/fnal.gov/usr/dune/.../f.root ./f.root     # copy (only if a tool can't take a URL)
```
Prefer streaming; only `xrdcp` to a local file when an analysis tool truly cannot
read a `root://` URL.

## Worked example
`results/prd-analyzer/` streams three 10M-event C12 samples this way instead of
pulling ~9 GB/model:
- `samples.py` — `xrootd_url()`, the dCache door, and per-model `gst_urls()`.
- `build_cache.py` — streams every gst over XRootD, selects, caches a tiny `.npz`.

## Notes
- The grid adapter can mark a gevgen/gmkspl job `failed` when the **fetchlog** step
  hits a transient `landscape.fnal.gov` 500 and the fallback PNFS count returns 0
  — even though the outputs are present. Verify with an NFS `find /pnfs/...` (or an
  `xrdfs ... ls`) before trusting a `failed` status (see jobsub-jobs).
- If `uproot.open("root://...")` raises about a missing source, the XRootD binding
  isn't installed — `pixi add xrootd fsspec-xrootd`.
- Auth errors (`[ERROR] ... not authorized`) ⇒ stale/absent token ⇒ `htgettoken -i dune`.

"""PNFS listing over XRootD — NFS-free (works with an expired Kerberos key).

Shared by the v0.2 builders (and usable by any template script): the local
/pnfs NFS mount needs a live krb ticket, but the dCache XRootD door only needs
a bearer token (BEARER_TOKEN_FILE, default /run/user/<uid>/bt_u<uid>;
refresh: htgettoken -a htvaultprod.fnal.gov -i dune).

    from pnfs_ls import xrootd_url, gst_urls
    urls = gst_urls("jobsub-agent/jobsub-runs/<run-dir>/<stem>.gridlog", 20)
"""
import json
from pathlib import Path

DOOR = "root://fndca1.fnal.gov:1094"


def xrootd_url(pnfs_path: str) -> str:
    """/pnfs/dune/... -> root://door//pnfs/fnal.gov/usr/dune/... (dCache ns)."""
    return f"{DOOR}/" + str(pnfs_path).replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def _dirlist(fs, path):
    st, ls = fs.dirlist(path)
    if not st.ok:
        raise RuntimeError(f"dirlist {path}: {st.message}")
    return ls


def list_outputs(pnfs_output_dir: str, suffix: str, max_files=None):
    """XRootD URLs of <pnfs_output_dir>/<proc>/*<suffix>, sorted, first N."""
    from XRootD import client
    base = str(pnfs_output_dir).replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)
    fs = client.FileSystem(DOOR)
    urls = []
    for sub in sorted(x.name for x in _dirlist(fs, base)
                      if x.name.strip("/").isdigit()):
        try:
            ls = _dirlist(fs, f"{base}/{sub}")
        except RuntimeError:
            continue
        urls += [f"{DOOR}/{base}/{sub}/{f.name}"
                 for f in ls if f.name.endswith(suffix)]
    urls = sorted(urls)
    return urls[:max_files] if max_files else urls


def gst_urls(gridlog_path, max_files=None):
    """The gridlog's gst outputs as XRootD URLs (first max_files, sorted)."""
    pnfs = json.loads(Path(gridlog_path).read_text())["pnfs_output_dir"]
    return list_outputs(pnfs, ".gst.root", max_files)


def ghep_urls(gridlog_path, max_files=None):
    """The gridlog's ghep outputs as XRootD URLs (first max_files, sorted)."""
    pnfs = json.loads(Path(gridlog_path).read_text())["pnfs_output_dir"]
    return list_outputs(pnfs, ".ghep.root", max_files)

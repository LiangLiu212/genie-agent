"""XRootD fallback I/O for /pnfs on hosts without ifdh (e.g. EAF pods).

Speaks the dCache door with the /pnfs -> /pnfs/fnal.gov/usr namespace mapping
(same convention as the pnfs-stream skill). Listings mimic `ifdh ls` output:
native /pnfs/... paths, directories marked with a trailing '/'.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from lib.submit_env import build_submit_env

XROOTD_DOOR = "root://fndca1.fnal.gov:1094"


def to_xrootd_path(path: str) -> str:
    return path.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def to_xrootd_url(path: str) -> str:
    return f"{XROOTD_DOOR}/{to_xrootd_path(path)}"


def xrdfs_ls(path: str) -> tuple[bool, list[str]]:
    """(ok, entries) for a native /pnfs path, ifdh-ls formatted."""
    try:
        p = subprocess.run(["xrdfs", XROOTD_DOOR, "ls", "-l", to_xrootd_path(path)],
                           capture_output=True, text=True, timeout=120,
                           env=build_submit_env())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, []
    if p.returncode != 0:
        return False, []
    out: list[str] = []
    for line in (p.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[-1].startswith("/"):
            continue
        native = parts[-1].replace("/pnfs/fnal.gov/usr/", "/pnfs/", 1)
        out.append(native + "/" if parts[0].startswith("d") else native)
    return True, out


def xrdcp_from_pnfs(src: str, dst: Path) -> tuple[bool, str]:
    """Copy a native /pnfs path to a local file. (ok, error_detail)."""
    try:
        p = subprocess.run(["xrdcp", "-f", to_xrootd_url(src), str(dst)],
                           capture_output=True, text=True, timeout=600,
                           env=build_submit_env())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)
    return (p.returncode == 0), (p.stderr or "")[-200:]

"""Pull grid outputs from PNFS scratch back to local disk via ifdh.

Generic: *which* files to copy (`suffix`) and *how* to name them locally
(`name_fn`) are parameters — not a GENIE `job_kind` switch (that was the
genie-mcp coupling). Walks `ifdh ls` of `pnfs_output_dir`'s per-process subdirs,
copies matching files into `local_output_dir`, and updates `processes_done` +
`status` on the record. All ifdh calls run under the scrubbed env; hosts without
ifdh (e.g. EAF) fall back to xrdfs/xrdcp via lib.pnfs_io.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Optional

from lib import pnfs_io, records
from lib.submit_env import build_submit_env


def _ifdh_ls(path: str) -> tuple[bool, list[str]]:
    try:
        p = subprocess.run(["ifdh", "ls", path], capture_output=True,
                           text=True, timeout=120, env=build_submit_env())
        if p.returncode == 0:
            return True, [l.strip() for l in (p.stdout or "").splitlines() if l.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return pnfs_io.xrdfs_ls(path)


def _ifdh_cp(src: str, dst: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(["ifdh", "cp", src, str(dst)], capture_output=True,
                           text=True, timeout=600, env=build_submit_env())
        if p.returncode == 0:
            return True, ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return pnfs_io.xrdcp_from_pnfs(src, dst)


def _default_name(process_str: str, basename: str) -> str:
    """Prefix with the process subdir so files from different processes don't
    collide in the flat local dir."""
    return f"{process_str}_{basename}" if process_str else basename


def pull(
    record_path: Path,
    cfg: dict,
    *,
    suffix: Optional[str] = None,
    name_fn: Optional[Callable[[str, str], str]] = None,
    overwrite: bool = False,
) -> dict:
    """Copy outputs from `pnfs_output_dir` into `local_output_dir`.

    `suffix`  — only copy files ending with it (None = every file).
    `name_fn` — (process_str, basename) -> local filename (default: prefix the
                process subdir name).
    """
    record = records.read_record(record_path)
    name_fn = name_fn or _default_name

    if record.get("outputs_pulled") and not overwrite:
        return {
            "status": "already_pulled", "job_id": record["jobid"],
            "local_output_dir": record.get("local_output_dir", ""),
            "n_pulled": record.get("processes_done", 0), "n_expected": record["n_jobs"],
            "message": "outputs already pulled; pass overwrite=True to re-copy",
        }

    pnfs_dir = record.get("pnfs_output_dir", "")
    if not pnfs_dir:
        return {"error": "record has no pnfs_output_dir", "job_id": record["jobid"]}

    local_dir = Path(record.get("local_output_dir")
                     or (Path(record_path).parent / f"{record['stem']}.outputs"))
    local_dir.mkdir(parents=True, exist_ok=True)

    ok, top = _ifdh_ls(pnfs_dir)
    if not ok:
        return {"error": f"ifdh ls failed for {pnfs_dir} (does it exist? is ifdh on PATH?)",
                "job_id": record["jobid"]}

    process_dirs = [p for p in top if p.endswith("/") and p.rstrip("/") != pnfs_dir.rstrip("/")]
    pulled: list[str] = []
    failures: list[str] = []

    for pdir in process_dirs:
        process_str = pdir.rstrip("/").rsplit("/", 1)[-1]
        ok2, files = _ifdh_ls(pdir)
        if not ok2:
            failures.append(f"ifdh ls failed: {pdir}")
            continue
        for fpath in files:
            if fpath.endswith("/"):
                continue
            basename = fpath.rsplit("/", 1)[-1]
            if suffix and not basename.endswith(suffix):
                continue
            local_path = local_dir / name_fn(process_str, basename)
            if local_path.exists() and not overwrite:
                pulled.append(str(local_path))
                continue
            cok, detail = _ifdh_cp(fpath, local_path)
            if cok:
                pulled.append(str(local_path))
            else:
                failures.append(f"ifdh cp {fpath}: {detail}")

    n_pulled = len(pulled)
    n_expected = record["n_jobs"]
    new_status = "done" if n_pulled == n_expected else ("partial" if n_pulled > 0 else "failed")
    updates = {"outputs_pulled": True, "processes_done": n_pulled,
               "local_output_dir": str(local_dir)}
    if record.get("status") != "cancelled":
        updates["status"] = new_status
    records.update_record(record_path, **updates)

    return {
        "job_id": record["jobid"], "n_pulled": n_pulled, "n_expected": n_expected,
        "local_output_dir": str(local_dir), "files": pulled, "failures": failures,
        "status": updates.get("status", record.get("status")),
        "message": (f"pulled {n_pulled}/{n_expected} file(s) into {local_dir}"
                    + (f"; {len(failures)} failure(s)" if failures else "")),
    }

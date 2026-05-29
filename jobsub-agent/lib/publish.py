"""Publish a tarball to RCDS/CVMFS and track it in a label->entry catalog.

RCDS assigns each upload to a random /cvmfs/fifeuserN.opensciencegrid.org/sw/dune/
<hash>/, so we recover the real path by running one **sentinel grid job**
(lib/templates/publish_only.sh) that echoes `PUBLISH_SENTINEL_CVMFS_DIR=<path>`,
then fetch its log and grep that out. The catalog (config/catalog.json) maps a
label to the published CVMFS path + a publish timestamp; `verify_cvmfs` flags
staleness (RCDS garbage-collects ~30d). Ported from genie-mcp grid_tarball, made
GENIE-agnostic (single `entries` namespace; any label).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from lib import monitor, records
from lib.submit import parse_cluster_id
from lib.submit_env import build_submit_env

_AGENT_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_PATH = _AGENT_ROOT / "config" / "catalog.json"
_PUBLISH_LOGS_DIR = _AGENT_ROOT / "jobsub-runs" / "_publish"
_DEFAULT_SENTINEL = _AGENT_ROOT / "lib" / "templates" / "publish_only.sh"

_RE_RCDS_HASH = re.compile(r"Publishing hash dune/([0-9a-f]+)")
_RE_SENTINEL_CVMFS = re.compile(r"PUBLISH_SENTINEL_CVMFS_DIR=(\S+)")
_CVMFS_RCDS_ROOTS = tuple(
    f"/cvmfs/fifeuser{i}.opensciencegrid.org/sw/dune" for i in (1, 2, 3, 4)
)
_GC_WARN_DAYS = 21
_GC_FAIL_DAYS = 28


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_rcds_hash(text: str) -> Optional[str]:
    m = _RE_RCDS_HASH.findall(text)
    return m[-1] if m else None


# ── catalog (label -> entry) ──────────────────────────────────────────────────

def load_catalog(path: Path = _CATALOG_PATH) -> dict:
    if not Path(path).exists():
        return {"entries": {}}
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return {"entries": {}}
    if not isinstance(data.get("entries"), dict):
        data["entries"] = {}
    return data


def save_catalog(catalog: dict, path: Path = _CATALOG_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".catalog.", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(catalog, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def lookup_catalog(label: str, path: Path = _CATALOG_PATH) -> Optional[dict]:
    return load_catalog(path)["entries"].get(label)


def add_to_catalog(entry: dict, *, overwrite: bool = False, path: Path = _CATALOG_PATH) -> dict:
    catalog = load_catalog(path)
    label = entry["label"]
    existing = catalog["entries"].get(label)
    if existing is not None and not overwrite:
        if existing.get("local_sha") == entry.get("local_sha"):
            return existing
        raise ValueError(
            f"label '{label}' already in catalog with sha {existing.get('local_sha')!r}; "
            f"pass overwrite=True to replace"
        )
    catalog["entries"][label] = entry
    save_catalog(catalog, path)
    return entry


# ── verify / staleness ──────────────────────────────────────────────────────

def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def verify_cvmfs(entry: dict) -> dict:
    """Best-effort existence + age check for a catalog entry's cvmfs_tar_file."""
    cvmfs_tar = entry.get("cvmfs_tar_file", "")
    published = _parse_iso(entry.get("published", ""))
    now = datetime.now(timezone.utc)
    age_days = (now - published).days if published else -1

    if cvmfs_tar and Path(cvmfs_tar).exists():
        status, reason = "exists", "stat ok"
    elif not any(Path(r).exists() for r in _CVMFS_RCDS_ROOTS):
        status, reason = "unknown", "no CVMFS fifeuserN repo mounted on this host"
    else:
        status, reason = "missing", f"path not present in CVMFS: {cvmfs_tar}"

    if age_days < 0:
        rec = "warn"
    elif age_days > _GC_FAIL_DAYS or status == "missing":
        rec = "republish"
    elif age_days > _GC_WARN_DAYS:
        rec = "warn"
    else:
        rec = "ok"

    result = {"status": status, "reason": reason, "age_days": age_days, "recommendation": rec}
    entry["last_verified"] = _now_iso()
    entry["last_verified_result"] = result
    return result


# ── publish via sentinel grid job ──────────────────────────────────────────────

def publish_to_cvmfs(
    cfg: dict,
    *,
    tarball_path: str,
    label: str,
    sentinel_script: Optional[str] = None,
    log_prefix: str = "",
    poll_timeout_s: int = 1800,
    poll_interval_s: int = 30,
) -> dict:
    """Upload `tarball_path` to RCDS by running one sentinel grid job; return
    {rcds_hash, cluster_id, cvmfs_dir, publish_log, fetched_dir, command_str}
    or {error, ...}."""
    sentinel = Path(sentinel_script or _DEFAULT_SENTINEL)
    if not sentinel.exists():
        return {"error": f"sentinel worker not found: {sentinel}"}
    if not os.access(sentinel, os.X_OK):
        return {"error": f"sentinel worker not executable: {sentinel}"}

    cmd = [cfg["jobsub_bin"], "-G", cfg["default_group"],
           "--role", cfg.get("default_role", "Analysis"), "-N", "1",
           "--tar_file_name", f"dropbox://{tarball_path}", f"file://{sentinel}"]

    _PUBLISH_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = _PUBLISH_LOGS_DIR / f"{log_prefix}{label}_{ts}.log"

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=900, env=build_submit_env())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        log_path.write_text(f"jobsub_submit failed: {e}\n")
        return {"error": f"jobsub_submit failed: {e}", "publish_log": str(log_path)}

    combined = (proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or "")
    log_path.write_text(combined)
    if proc.returncode != 0:
        return {"error": f"jobsub_submit exited {proc.returncode}",
                "publish_log": str(log_path), "command_str": " ".join(cmd)}

    rcds_hash = parse_rcds_hash(combined)
    if not rcds_hash:
        return {"error": "RCDS publish hash not found in jobsub_submit output",
                "publish_log": str(log_path), "command_str": " ".join(cmd)}
    try:
        cluster_id = parse_cluster_id(combined)
    except ValueError:
        return {"error": "cluster id not found in jobsub_submit output",
                "publish_log": str(log_path), "rcds_hash": rcds_hash}

    # Poll until the sentinel cluster leaves the queue.
    deadline = time.monotonic() + poll_timeout_s
    while True:
        q = monitor.query_jobsub_status(cluster_id, cfg)
        if q.get("empty"):
            break
        if time.monotonic() > deadline:
            return {"error": f"sentinel {cluster_id} did not leave queue in {poll_timeout_s}s",
                    "publish_log": str(log_path), "rcds_hash": rcds_hash, "cluster_id": cluster_id}
        time.sleep(poll_interval_s)

    # Fetch worker log + grep the real CVMFS dir.
    fetch_dir = _PUBLISH_LOGS_DIR / f"{log_prefix}{label}_{ts}_fetched"
    fetch_dir.mkdir(parents=True, exist_ok=True)
    fetch_cmd = [cfg["jobsub_fetchlog_bin"], "--jobid", cluster_id,
                 "-G", cfg["default_group"], "--unzipdir", str(fetch_dir)]
    try:
        subprocess.run(fetch_cmd, capture_output=True, text=True,
                       timeout=600, env=build_submit_env())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"error": f"jobsub_fetchlog failed: {e}", "publish_log": str(log_path),
                "rcds_hash": rcds_hash, "cluster_id": cluster_id}

    cvmfs_dir = None
    for f in sorted(fetch_dir.rglob("*")):
        if not f.is_file():
            continue
        m = _RE_SENTINEL_CVMFS.search(f.read_text(errors="replace"))
        if m:
            cvmfs_dir = m.group(1).rstrip("/")
            break
    if not cvmfs_dir:
        return {"error": f"PUBLISH_SENTINEL_CVMFS_DIR not found in fetched logs under {fetch_dir}",
                "publish_log": str(log_path), "rcds_hash": rcds_hash,
                "cluster_id": cluster_id, "fetched_dir": str(fetch_dir)}

    return {"rcds_hash": rcds_hash, "cluster_id": cluster_id, "cvmfs_dir": cvmfs_dir,
            "publish_log": str(log_path), "fetched_dir": str(fetch_dir), "command_str": " ".join(cmd)}


def publish_and_catalog(
    cfg: dict,
    *,
    tarball_path: str,
    label: str,
    local_sha: str = "",
    size_mb: Optional[float] = None,
    overwrite: bool = False,
    description: str = "",
    sentinel_script: Optional[str] = None,
    log_prefix: str = "",
    extra: Optional[dict] = None,
) -> dict:
    """Publish `tarball_path` then record the CVMFS path in the catalog under
    `label`. Returns the catalog entry, or {error}."""
    if not label or "/" in label or label.startswith("."):
        return {"error": f"invalid label: {label!r}"}

    pub = publish_to_cvmfs(cfg, tarball_path=tarball_path, label=label,
                           sentinel_script=sentinel_script, log_prefix=log_prefix)
    if "error" in pub:
        return pub

    entry = {
        "label": label, "local_path": tarball_path, "local_sha": local_sha,
        "size_mb": size_mb, "rcds_hash": pub["rcds_hash"], "cluster_id": pub.get("cluster_id", ""),
        "cvmfs_dir": pub["cvmfs_dir"], "cvmfs_tar_file": f"{pub['cvmfs_dir']}/{Path(tarball_path).name}",
        "published": _now_iso(), "last_verified": "", "last_verified_result": {},
        "description": description, "publish_log": pub["publish_log"],
        "fetched_dir": pub.get("fetched_dir", ""), **(extra or {}),
    }
    try:
        return add_to_catalog(entry, overwrite=overwrite)
    except ValueError as e:
        return {"error": str(e), "publish_log": pub["publish_log"]}


def label_from_job(cfg: dict, *, label: str, jobid: str,
                   description: str = "", overwrite: bool = False) -> dict:
    """Adopt an already-published tarball into the catalog by parsing the RCDS
    hash from an existing job's submit log (needs the CVMFS path visible here)."""
    if not label or "/" in label or label.startswith("."):
        return {"error": f"invalid label: {label!r}"}
    try:
        rec_path = records.find_record_for_jobid(jobid)
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}
    record = records.read_record(rec_path)
    submit_log = record.get("submit_log_file", "")
    if not submit_log or not Path(submit_log).exists():
        return {"error": f"submit log not found for job '{jobid}': {submit_log!r}"}
    rcds_hash = parse_rcds_hash(Path(submit_log).read_text())
    if not rcds_hash:
        return {"error": f"no 'Publishing hash dune/<hex>' line in submit log for '{jobid}'"}
    tarball_path = record.get("tarball_path", "")
    basename = Path(tarball_path).name if tarball_path else ""
    cvmfs_dir = cvmfs_tar = ""
    for root in _CVMFS_RCDS_ROOTS:
        cand = f"{root}/{rcds_hash}/{basename}"
        if basename and Path(cand).exists():
            cvmfs_dir, cvmfs_tar = f"{root}/{rcds_hash}", cand
            break
    if not cvmfs_dir:
        return {"error": f"could not locate fifeuser{{1..4}}/sw/dune/{rcds_hash}/{basename} "
                         f"on this host; re-publish via publish_and_catalog instead"}
    entry = {
        "label": label, "local_path": tarball_path, "local_sha": "",
        "rcds_hash": rcds_hash, "cvmfs_dir": cvmfs_dir, "cvmfs_tar_file": cvmfs_tar,
        "published": record.get("submitted", _now_iso()), "last_verified": "",
        "last_verified_result": {}, "description": description, "adopted_from_job": jobid,
    }
    try:
        return add_to_catalog(entry, overwrite=overwrite)
    except ValueError as e:
        return {"error": str(e)}

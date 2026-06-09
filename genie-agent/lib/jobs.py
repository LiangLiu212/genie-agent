"""Background-job plumbing for genie-agent runners.

A "job" is one invocation of a GENIE binary (gmkspl, gevgen, ...). Each job
gets:

  - a jobid:    <runtype>-<stem>-<6hex>   (decodable; no registry file)
  - a log file: <run_dir>/<stem>.log      (mutable JSON; status lives here)
  - artefacts:  <run_dir>/<stem>.{stdout,stderr,xml,...}

The launcher writes the initial log, forks a detached supervisor (setsid), and
returns immediately with the jobid. The supervisor execs the GENIE binary,
forwards SIGTERM (for cancel), and updates the log on completion. The status
CLI reads + reconciles the log; the cancel CLI sends signals.

Status fields start as null and transition to true/false; see schema in
`make_initial_log`.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from lib.paths import RUNS_ROOT, sha256_short


_AGENT_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha() -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(_AGENT_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return None


def _git_dirty() -> Optional[bool]:
    """True if tracked files differ from git_sha, False if clean, None on error.

    Untracked files are excluded (--untracked-files=no): the workspace
    routinely carries untracked plan/notes files, and what matters for replay
    is whether the code identified by git_sha is what actually ran.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(_AGENT_ROOT), "status", "--porcelain",
             "--untracked-files=no"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if out.returncode == 0:
            return bool(out.stdout.strip())
    except Exception:
        pass
    return None


def make_jobid(runtype: str, stem: str) -> str:
    return f"{runtype}-{stem}-{secrets.token_hex(3)}"


def parse_jobid(jobid: str) -> tuple[str, str, str]:
    """Return (runtype, stem, hex6). Raises ValueError on malformed input."""
    parts = jobid.split("-")
    if len(parts) < 3:
        raise ValueError(f"malformed jobid: {jobid!r}")
    runtype = parts[0]
    hex6    = parts[-1]
    stem    = "-".join(parts[1:-1])
    if not stem:
        raise ValueError(f"malformed jobid (empty stem): {jobid!r}")
    return runtype, stem, hex6


def find_log_for_jobid(jobid: str) -> Path:
    """Resolve a jobid to its <stem>.log path by globbing genie-runs/*/."""
    runtype, stem, _ = parse_jobid(jobid)
    matches = list(RUNS_ROOT.glob(f"*/{stem}.log"))
    matches = [m for m in matches if _log_jobid(m) == jobid]
    if not matches:
        raise FileNotFoundError(f"no log file for jobid {jobid}")
    if len(matches) > 1:
        raise RuntimeError(f"multiple logs for jobid {jobid}: {matches}")
    return matches[0]


def _log_jobid(log_path: Path) -> Optional[str]:
    try:
        return json.loads(log_path.read_text()).get("jobid")
    except Exception:
        return None


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def update_log(log_path: Path, **fields: Any) -> dict:
    record = json.loads(log_path.read_text())
    record.update(fields)
    atomic_write_json(log_path, record)
    return record


def make_initial_log(
    *,
    jobid: str,
    runtype: str,
    script: Path,
    command: list[str],
    description: str,
    inputs: dict,
    outputs: dict,
    cwd: Path,
) -> dict:
    return {
        "jobid":         jobid,
        "runtype":       runtype,
        "script":        str(script.relative_to(_AGENT_ROOT))
                         if script.is_absolute() and script.is_relative_to(_AGENT_ROOT)
                         else str(script),
        "script_path":   str(script),
        "script_sha256": sha256_short(script),
        "git_sha":       _git_sha(),
        "git_dirty":     _git_dirty(),
        "cwd":           str(cwd),
        "command":       command,
        "description":   description,
        "inputs":        inputs,
        "outputs":       outputs,
        "timestamp":     _utc_now_iso(),
        "started":       None,
        "finished":      None,
        "duration_s":    None,
        "pid":           None,
        "running":       None,
        "failed":        None,
        "canceled":      None,
        "returncode":    None,
    }


def launch_background(
    *,
    runtype: str,
    script: Path,
    command: list[str],
    env: dict[str, str],
    cwd: Path,
    stem: str,
    description: str,
    inputs: dict,
    outputs: dict,
) -> str:
    """Write initial log, spawn detached supervisor, return jobid."""
    jobid    = make_jobid(runtype, stem)
    log_path = cwd / f"{stem}.log"

    record = make_initial_log(
        jobid=jobid, runtype=runtype, script=script,
        command=command, description=description,
        inputs=inputs, outputs=outputs, cwd=cwd,
    )
    atomic_write_json(log_path, record)

    env_json = log_path.with_suffix(".env.json")
    env_json.write_text(json.dumps(env, indent=2) + "\n")

    subprocess.Popen(
        [sys.executable, str(script), "--supervise",
         "--log-path", str(log_path), "--env-path", str(env_json)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    return jobid


def run_foreground(
    *,
    runtype: str,
    script: Path,
    command: list[str],
    env: dict[str, str],
    cwd: Path,
    stem: str,
    description: str,
    inputs: dict,
    outputs: dict,
) -> int:
    """Same schema as launch_background, but blocks the caller."""
    jobid    = make_jobid(runtype, stem)
    log_path = cwd / f"{stem}.log"

    record = make_initial_log(
        jobid=jobid, runtype=runtype, script=script,
        command=command, description=description,
        inputs=inputs, outputs=outputs, cwd=cwd,
    )
    atomic_write_json(log_path, record)

    sys.stdout.write(f"jobid: {jobid}\nlog:   {log_path}\n")
    sys.stdout.flush()

    return _supervise_impl(log_path=log_path, env=env)


def supervise(*, log_path: Path, env_path: Path) -> int:
    """Entry point used by the detached child via `--supervise --log-path …`."""
    env = json.loads(env_path.read_text())
    try:
        return _supervise_impl(log_path=log_path, env=env)
    finally:
        try:
            env_path.unlink()
        except FileNotFoundError:
            pass


def _supervise_impl(*, log_path: Path, env: dict[str, str]) -> int:
    record = json.loads(log_path.read_text())
    command   = record["command"]
    outputs   = record.get("outputs", {})
    stdout_log = outputs.get("stdout_log")
    stderr_log = outputs.get("stderr_log")
    cwd       = record.get("cwd") or str(log_path.parent)

    out_fh = open(stdout_log, "wb") if stdout_log else subprocess.DEVNULL
    err_fh = open(stderr_log, "wb") if stderr_log else subprocess.DEVNULL

    started_iso = _utc_now_iso()
    started_mono = time.monotonic()

    try:
        child = subprocess.Popen(
            command, env=env, cwd=cwd,
            stdout=out_fh, stderr=err_fh,
            start_new_session=False,
        )
    except Exception as exc:
        update_log(
            log_path,
            running=False, failed=True, canceled=False,
            returncode=-1,
            started=started_iso,
            finished=_utc_now_iso(),
            duration_s=round(time.monotonic() - started_mono, 3),
            error=f"failed to spawn child: {exc!r}",
        )
        return 1

    update_log(log_path, running=True, pid=child.pid, started=started_iso)

    canceled = {"flag": False}

    def _on_sigterm(signum, frame):
        canceled["flag"] = True
        try:
            child.terminate()
        except ProcessLookupError:
            pass

    signal.signal(signal.SIGTERM, _on_sigterm)
    signal.signal(signal.SIGINT,  _on_sigterm)

    try:
        rc = child.wait()
    except KeyboardInterrupt:
        canceled["flag"] = True
        child.terminate()
        try:
            rc = child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            rc = child.wait()

    if canceled["flag"] and child.poll() is None:
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        rc = child.returncode

    if out_fh not in (None, subprocess.DEVNULL):
        out_fh.close()
    if err_fh not in (None, subprocess.DEVNULL):
        err_fh.close()

    finished_iso = _utc_now_iso()
    duration_s   = round(time.monotonic() - started_mono, 3)
    primary_output = outputs.get("primary_output")

    update_log(
        log_path,
        running=False,
        failed=(rc != 0) and not canceled["flag"],
        canceled=canceled["flag"] or None,
        returncode=rc,
        finished=finished_iso,
        duration_s=duration_s,
        output_sha256=sha256_short(primary_output) if primary_output else None,
    )
    return rc


def reconcile_log(log_path: Path) -> dict:
    """If the log says running=true but the pid is dead, mark it as lost."""
    record = json.loads(log_path.read_text())
    if record.get("running") is True:
        pid = record.get("pid")
        if pid and not _pid_alive(int(pid)):
            record = update_log(
                log_path,
                running=False,
                failed=True,
                returncode=record.get("returncode") or -1,
                finished=_utc_now_iso(),
                error="supervisor lost (pid not alive)",
            )
    return record


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def cancel_job(log_path: Path, sigterm_timeout: float = 2.0) -> dict:
    """Send SIGTERM (then SIGKILL) to the job's process group."""
    record = json.loads(log_path.read_text())
    pid = record.get("pid")
    if pid and _pid_alive(int(pid)):
        try:
            pgid = os.getpgid(int(pid))
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        deadline = time.monotonic() + sigterm_timeout
        while time.monotonic() < deadline:
            if not _pid_alive(int(pid)):
                break
            time.sleep(0.1)
        if _pid_alive(int(pid)):
            try:
                pgid = os.getpgid(int(pid))
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    record = json.loads(log_path.read_text())
    if record.get("running") is True:
        record = update_log(
            log_path,
            running=False,
            canceled=True,
            finished=_utc_now_iso(),
            returncode=record.get("returncode") if record.get("returncode") is not None else -15,
        )
    return record

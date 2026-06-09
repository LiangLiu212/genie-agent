"""Per-run directory + filename helpers.

Layout:
    genie-runs/<tune>-YYYY-MM-DD/<probe>_<target>_<YYYYMMDD-HHMMSS>.{xml,log,stdout,stderr,...}

All artefacts for a run share a stem and live in the same per-day folder, so
`ls genie-runs/G18_02a_00_000-2026-05-28/` reveals everything about a run and
`jq genie-runs/*/*.log` is the discovery story.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Iterable

_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = _ROOT / "genie-runs"


def new_run_dir(tune: str, when: datetime | None = None) -> Path:
    """Return (and create) `genie-runs/<tune>-YYYY-MM-DD/` for today."""
    when = when or datetime.now()
    run_dir = RUNS_ROOT / f"{tune}-{when.strftime('%Y-%m-%d')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_stem(probes: Iterable[str], targets: Iterable[str],
             when: datetime | None = None) -> str:
    """Return `<probe(s)>_<target(s)>_<YYYYMMDD-HHMMSS>-<3hex>` filename stem.

    The trailing 3-hex token keeps two same-probe/target/tune runs launched in
    the same second from sharing a stem and silently clobbering each other's
    log/artefacts. Nothing parses the stem back (gntpc reads the sibling .log;
    jobids embed the stem verbatim), so the suffix is safe to add.
    """
    when = when or datetime.now()
    probe_label  = "-".join(probes)
    target_label = "-".join(targets)
    ts = when.strftime("%Y%m%d-%H%M%S")
    return f"{probe_label}_{target_label}_{ts}-{secrets.token_hex(2)[:3]}"


def sha256_short(path: str | Path, n: int = 16) -> str | None:
    """First `n` hex chars of sha256(path). Returns None if path is unreadable."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:n]
    except Exception:
        return None

"""Load config/jobsub.json — the jobsub_lite binary paths + grid defaults.

Flat config (no installations registry; unlike genie-agent these settings are
host-wide, not per-GENIE-build). Precedence for the config file path:
explicit `path=` arg → `$JOBSUB_AGENT_CONFIG` env → `config/jobsub.json`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG_PATH = _ROOT / "config" / "jobsub.json"

_REQUIRED_KEYS = (
    "jobsub_bin",
    "jobsub_q_bin",
    "jobsub_fetchlog_bin",
    "default_group",
)


def config_path(path: str | Path | None = None) -> Path:
    return Path(path or os.environ.get("JOBSUB_AGENT_CONFIG") or _DEFAULT_CONFIG_PATH)


def load_config(path: str | Path | None = None) -> dict:
    cfg_path = config_path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"jobsub config not found: {cfg_path} "
            f"(copy/edit one there, or set $JOBSUB_AGENT_CONFIG)"
        )
    cfg = json.loads(cfg_path.read_text())

    missing = [k for k in _REQUIRED_KEYS if not cfg.get(k)]
    if missing:
        raise KeyError(f"{cfg_path} is missing required key(s): {', '.join(missing)}")

    # jobsub_rm is derived from jobsub_q's dir if absent, to avoid a stale path.
    cfg.setdefault("jobsub_rm_bin", str(Path(cfg["jobsub_q_bin"]).parent / "jobsub_rm"))
    cfg["config_path"] = str(cfg_path)
    return cfg

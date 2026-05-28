"""Per-installation GENIE spack env: snapshot to JSON, load at runtime.

genie-agent runs under pixi; GENIE binaries need the spack env from each
installation's `setup_env.sh`. To keep pixi vars (PIXI_*, CONDA_*, PYTHONHOME,
PYTHONPATH, ...) out of the child env, we snapshot the spack env in a
parent-stripped shell (`env -i` + `bash --noprofile --norc`) and persist the
result to `config/env/<installation_name>.json`. At runtime, `load_genie_env`
reads that JSON and passes it as `env=` to subprocess.

Refresh the snapshot with `scripts/refresh_genie_env.py`.
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[1]
_ENV_DIR = _ROOT / "config" / "env"

_DENY_PREFIXES = ("PIXI_", "CONDA_", "MAMBA_", "_CE_", "VIRTUAL_ENV", "BASH_FUNC_")
_DENY_EXACT    = {"PYTHONHOME", "PYTHONPATH"}
_BOOTSTRAP     = {"HOME", "USER", "TERM", "PWD", "SHLVL", "_", "OLDPWD"}

_CACHE: dict[str, dict[str, str]] = {}


def env_file_for(installation_name: str) -> Path:
    return _ENV_DIR / f"{installation_name}.json"


def snapshot_setup_script(setup_script: str, timeout: int = 120) -> dict[str, str]:
    """Source setup_script in a parent-env-stripped bash and return its env dict.

    The shell starts from `env -i` with only HOME/USER/TERM bootstrapped, runs
    without dotfiles, and dumps NUL-separated KEY=VALUE records via `env -0`.
    Denylisted keys (pixi/conda residue, bash-function exports) and the
    bootstrap vars themselves are stripped before returning.
    """
    setup = Path(setup_script).expanduser().resolve()
    if not setup.is_file():
        raise FileNotFoundError(f"genie_setup_script not found: {setup}")

    cmd = [
        "env", "-i",
        f"HOME={os.environ['HOME']}",
        f"USER={os.environ.get('USER', '')}",
        f"TERM={os.environ.get('TERM', 'dumb')}",
        "bash", "--noprofile", "--norc", "-c",
        f"source {shlex.quote(str(setup))} && env -0",
    ]

    result = subprocess.run(cmd, capture_output=True, check=False, timeout=timeout)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(
            f"sourcing {setup} exited {result.returncode}; stderr: {stderr}"
        )

    env = _parse_env0(result.stdout)
    env = _scrub(env)

    if "GENIE" not in env:
        raise RuntimeError(
            f"$GENIE not set after sourcing {setup}; refusing snapshot"
        )

    return env


def load_genie_env(cfg: dict) -> dict[str, str]:
    """Return the env dict for cfg's installation.

    Precedence:
      1. config/env/<installation_name>.json (preferred — fast, inspectable).
      2. Live snapshot of cfg['genie_setup_script'] (fallback, with warning;
         does not write the cache file — user runs refresh_genie_env.py).
    """
    name = cfg["installation_name"]
    if name in _CACHE:
        return _CACHE[name]

    setup_script = cfg.get("genie_setup_script")
    env_file = env_file_for(name)

    if env_file.is_file():
        if setup_script and Path(setup_script).is_file():
            if env_file.stat().st_mtime < Path(setup_script).stat().st_mtime:
                logger.warning(
                    "%s is older than %s — consider running "
                    "scripts/refresh_genie_env.py --installation %s",
                    env_file, setup_script, name,
                )
        env = json.loads(env_file.read_text())
        _CACHE[name] = env
        return env

    if not setup_script:
        raise RuntimeError(
            f"no cached env at {env_file} and no genie_setup_script in cfg"
        )

    logger.warning(
        "no cached env at %s — taking a live snapshot of %s. "
        "Run scripts/refresh_genie_env.py --installation %s to cache it.",
        env_file, setup_script, name,
    )
    env = snapshot_setup_script(setup_script)
    _CACHE[name] = env
    return env


def write_env_file(installation_name: str, env: dict[str, str]) -> Path:
    """Atomically write env to config/env/<installation_name>.json."""
    _ENV_DIR.mkdir(parents=True, exist_ok=True)
    dest = env_file_for(installation_name)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(json.dumps(env, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, dest)
    return dest


def reset_env_cache() -> None:
    _CACHE.clear()


def _parse_env0(blob: bytes) -> dict[str, str]:
    env: dict[str, str] = {}
    text = blob.decode("utf-8", errors="replace")
    for record in text.split("\0"):
        if not record:
            continue
        eq = record.find("=")
        if eq <= 0:
            continue
        env[record[:eq]] = record[eq + 1:]
    return env


def _scrub(env: dict[str, str]) -> dict[str, str]:
    return {
        k: v for k, v in env.items()
        if k not in _BOOTSTRAP
        and k not in _DENY_EXACT
        and not k.startswith(_DENY_PREFIXES)
    }

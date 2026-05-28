#!/usr/bin/env python3
"""Snapshot a GENIE installation's spack env to config/env/<installation>.json.

Run once per installation, or after editing the installation's setup_env.sh:

    pixi run python scripts/refresh_genie_env.py --installation genie_rc
    pixi run python scripts/refresh_genie_env.py --all
    pixi run python scripts/refresh_genie_env.py             # active install

The snapshot runs in a parent-env-stripped bash so pixi/conda vars from the
caller cannot leak into the cached env.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AGENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_ROOT))

from lib.config import load_config                                    # noqa: E402
from lib.genie_env import snapshot_setup_script, write_env_file       # noqa: E402


def _snapshot_one(name: str) -> int:
    cfg = load_config(name)
    setup = cfg.get("genie_setup_script")
    if not setup:
        sys.stderr.write(f"error: installation '{name}' has no genie_setup_script\n")
        return 2

    print(f"snapshotting {name} from {setup} ...")
    try:
        env = snapshot_setup_script(setup)
    except Exception as e:
        sys.stderr.write(f"error: {name}: {e}\n")
        return 1

    dest = write_env_file(name, env)
    print(
        f"  -> {dest} ({len(env)} vars, "
        f"GENIE={env.get('GENIE','?')}, "
        f"XSECSPLINEDIR={env.get('XSECSPLINEDIR','?')})"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--installation", help="Installation name to snapshot")
    group.add_argument("--all", action="store_true",
                       help="Snapshot every installation in genie_env.json")
    args = parser.parse_args()

    cfg_path = _AGENT_ROOT / "config" / "genie_env.json"
    root_cfg = json.loads(cfg_path.read_text())
    installations = list(root_cfg.get("installations", {}).keys())

    if args.all:
        targets = installations
    elif args.installation:
        targets = [args.installation]
    else:
        targets = [root_cfg.get("active_installation")]
        if not targets[0]:
            sys.stderr.write("error: no --installation, --all, or active_installation set\n")
            return 2

    rc = 0
    for name in targets:
        rc |= _snapshot_one(name)
    return rc


if __name__ == "__main__":
    sys.exit(main())

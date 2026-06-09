"""Load config/genie_env.json and merge the active installation over global defaults."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "config" / "genie_env.json"


def load_config(installation: str | None = None) -> dict:
    cfg = json.loads(_CONFIG_PATH.read_text())

    name = (
        installation
        or os.environ.get("GENIE_AGENT_INSTALLATION")
        or cfg.get("active_installation")
    )
    if name is None:
        raise KeyError("no active_installation set in config/genie_env.json")
    if name not in cfg.get("installations", {}):
        known = ", ".join(sorted(cfg.get("installations", {}).keys()))
        raise KeyError(f"installation '{name}' not found; known: {known}")

    merged = {k: v for k, v in cfg.items() if k != "installations"}
    merged.update(cfg["installations"][name])
    merged["installation_name"] = name

    # Registry entries may carry "status": "out_of_date" (+ optional "_note");
    # the install still works, but every selection of it should say so.
    if merged.get("status") == "out_of_date":
        note = merged.get("_note", "")
        sys.stderr.write(
            f"warning: installation '{name}' is marked out_of_date"
            f"{' — ' + note if note else ''}\n"
        )
    return merged

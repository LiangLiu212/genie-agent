"""Shared helpers for the GENIE grid adapters.

No cross-import into genie-agent: the tune regex + GEM/EM rules are restated
here (trivial), and genie-agent's `config/genie_env.json` is read as **plain
JSON** (not a code import) only to supply default tune/genlist and the local
install path (for a best-effort tune-family warning + tarball build_dir).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from lib import publish

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GENIE_AGENT_CONFIG = _REPO_ROOT / "genie-agent" / "config" / "genie_env.json"

# <PREFIX><YY>_<NN><x>_<PP>_<FFF>  e.g. G18_02a_00_000, GEM21_11a_00_000
TUNE_RE = re.compile(r"^[A-Z]+\d{2}_\d{2}[a-z]_\d{2}_[0-9a-z]+$")
EM_LISTS = frozenset({"EM", "EMQE", "EMMEC", "EMRES", "EMDIS", "EMQE+EMMEC"})
_BARE_NUCLEONS = frozenset({2112, 2212})


# ── genie-agent config (plain JSON read) ──────────────────────────────────────

def genie_agent_config() -> dict:
    try:
        return json.loads(_GENIE_AGENT_CONFIG.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def default_tune() -> Optional[str]:
    return genie_agent_config().get("default_tune")


def default_genlist() -> Optional[str]:
    return genie_agent_config().get("default_generator_list")


def local_genie_install() -> Optional[dict]:
    cfg = genie_agent_config()
    name = cfg.get("active_installation")
    out = dict(cfg.get("installations", {}).get(name, {})) if name else {}
    if out:
        out["installation_name"] = name
    return out or None


def resolve_installation(flag_value: Optional[str]) -> str:
    """Return active_installation, rejecting any disagreeing override.

    The grid PNFS layout bakes the installation name into the output path, and
    the worker tarball (selected by --tarball-label) is the real source of the
    GENIE binaries. Letting --installation or GENIE_AGENT_INSTALLATION silently
    shadow active_installation produces a misleading PNFS folder, so on
    mismatch we raise loudly instead.
    """
    cfg = genie_agent_config()
    active = cfg.get("active_installation")
    if not active:
        raise SystemExit("error: no active_installation in genie-agent/config/genie_env.json")
    env_value = os.environ.get("GENIE_AGENT_INSTALLATION")
    for src, val in (("--installation", flag_value), ("GENIE_AGENT_INSTALLATION", env_value)):
        if val and val != active:
            raise SystemExit(
                f"error: {src}={val!r} disagrees with active_installation={active!r} "
                f"in genie-agent/config/genie_env.json. The grid adapter uses "
                f"active_installation for the PNFS layout; edit the config (or pass "
                f"--config) instead of overriding via flag/env."
            )
    return active


def tune_family_present_locally(tune: str) -> Optional[bool]:
    """True/False if the tune family dir exists in the local install config;
    None if there's no local install info to check against."""
    inst = local_genie_install()
    bin_dir = inst.get("genie_bin_dir") if inst else None
    if not bin_dir:
        return None
    base = "_".join(tune.split("_")[:2])
    return (Path(bin_dir).parent / "config" / base).is_dir()


# ── catalog resolution ──────────────────────────────────────────────────────

def resolve_tarball(label: str) -> dict:
    """Look up + verify a published tarball label. Returns {cvmfs_dir, entry,
    warn} or {error}."""
    entry = publish.lookup_catalog(label)
    if entry is None:
        return {"error": (f"tarball label '{label}' not in catalog; publish it first: "
                          f"scripts/tarball.py publish --label {label} --tarball <x.tar>")}
    check = publish.verify_cvmfs(entry)
    catalog = publish.load_catalog()
    catalog["entries"][label] = entry
    publish.save_catalog(catalog)
    if check["status"] == "missing" or check["recommendation"] == "republish":
        return {"error": (f"tarball '{label}' likely expired on CVMFS ({check['reason']}, "
                          f"age {check['age_days']}d); republish with overwrite=True")}
    warn = (f"tarball '{label}' is {check['age_days']}d old (RCDS GC ~30d); consider republishing"
            if check["recommendation"] == "warn" else None)
    return {"cvmfs_dir": entry["cvmfs_dir"], "entry": entry, "warn": warn}


# ── validation ──────────────────────────────────────────────────────────────

def validate_common(*, is_lepton: bool, is_neutrino: bool, tune: str,
                     genlist: str, n_jobs: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if genlist == "Default":
        errors.append("generator_list='Default' is broken (PYTHIA6 charm); use CC/CCQE/RES/EM/...")
    if n_jobs <= 0:
        errors.append(f"n_jobs (-N) must be > 0, got {n_jobs}")

    if not TUNE_RE.match(tune):
        errors.append(f"Invalid tune '{tune}': expected 4-part form, e.g. G18_02a_00_000")
    else:
        is_gem = re.match(r"^([A-Z]+)", tune).group(1) == "GEM"
        if is_lepton and not is_gem:
            errors.append(f"Charged-lepton probe requires a GEM21_* tune, got '{tune}'")
        if is_neutrino and is_gem:
            errors.append("GEM tunes are electron-scattering only; use G18_*/AR23_*/... for neutrinos")
        if is_lepton and genlist not in EM_LISTS:
            errors.append(f"Charged-lepton probe requires generator_list in {sorted(EM_LISTS)}, got '{genlist}'")
        if is_neutrino and genlist in EM_LISTS:
            errors.append(f"generator_list='{genlist}' is charged-lepton only; use CCQE/RES/... for neutrinos")
        if tune_family_present_locally(tune) is False:
            warnings.append(f"tune family for '{tune}' not found in the local install config "
                            "(ok if it lives only in the tarball / tune-overlay)")
    return errors, warnings


def validate_target(pdg: int) -> list[str]:
    if pdg not in _BARE_NUCLEONS and not (1_000_000_000 <= pdg <= 1_999_999_999):
        return [f"PDG {pdg} does not look like a valid nuclear target"]
    return []


def validate_cross_sections(cross_sections: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    p = Path(cross_sections)
    if not p.is_absolute():
        errors.append(f"cross_sections must be an absolute path, got '{cross_sections}'")
    elif cross_sections.startswith("/pnfs/"):
        pass  # grid-accessible; real existence is checked by ifdh on the worker
    elif not p.exists():
        errors.append(f"cross_sections file not found: {cross_sections}")
    else:
        warnings.append("cross_sections is a local path; the grid file-transfer host cannot read "
                        "/exp/dune/data. Stage to /pnfs scratch and pass the /pnfs path, else it is "
                        "uploaded via -f file:// (slow for large splines).")
    return errors, warnings

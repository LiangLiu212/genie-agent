"""Validation rules for gmkspl/gevgen inputs.

Ported from genie-mcp/genie_mcp/tools/gmkspl_tool.py:_validate_gmkspl_inputs.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .pdg import CHARGED_LEPTON_PDGS, NEUTRINO_PDGS

# Tune format: <PREFIX><YY>_<NN><x>_<PP>_<FFF>  e.g. G18_02a_00_000, GEM21_11a_00_000
TUNE_RE = re.compile(r"^[A-Z]+\d{2}_\d{2}[a-z]_\d{2}_[0-9a-z]+$")

_EM_LISTS = frozenset({"EM", "EMQE", "EMMEC"})


def validate_gmkspl_inputs(
    nu_pdgs: list[int],
    tgt_pdgs: list[int],
    tune: str,
    generator_list: str,
    max_energy: Optional[float],
    n_knots: Optional[int],
    genie_bin_dir: str,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). errors block launch; warnings are advisory."""
    errors: list[str] = []
    warnings: list[str] = []

    if not nu_pdgs:
        errors.append("probes must not be empty")
        return errors, warnings

    is_lepton   = any(p in CHARGED_LEPTON_PDGS for p in nu_pdgs)
    is_neutrino = any(p in NEUTRINO_PDGS for p in nu_pdgs)

    if is_lepton and is_neutrino:
        errors.append("Cannot mix neutrino and charged-lepton probes in one job")

    if not tgt_pdgs:
        errors.append("targets must not be empty")
    else:
        _BARE_NUCLEONS = {2112, 2212}
        for pdg in tgt_pdgs:
            if pdg not in _BARE_NUCLEONS and not (1000000000 <= pdg <= 1999999999):
                errors.append(f"PDG {pdg} does not look like a valid nuclear target")

    if not TUNE_RE.match(tune):
        errors.append(f"Invalid tune '{tune}': expected 4-part form, e.g. G18_02a_00_000")
    else:
        tune_base = "_".join(tune.split("_")[:2])
        config_dir = Path(genie_bin_dir).parent / "config" / tune_base
        if not config_dir.is_dir():
            errors.append(f"Tune config dir not found: {config_dir}")

        tune_prefix = re.match(r"^([A-Z]+)", tune).group(1)
        is_gem_tune = tune_prefix == "GEM"

        if is_lepton and not is_gem_tune:
            errors.append(
                f"Charged-lepton probe requires a GEM21_* tune (e.g. GEM21_11a_00_000), got '{tune}'"
            )
        if is_neutrino and is_gem_tune:
            errors.append(
                f"GEM tunes are for electron scattering only; "
                f"use G18_*, G21_*, AR23_*, etc. for neutrinos"
            )

    if is_lepton and generator_list not in _EM_LISTS:
        errors.append(
            f"Charged-lepton probe requires generator_list in {sorted(_EM_LISTS)}, "
            f"got '{generator_list}'"
        )
    if is_neutrino and generator_list in _EM_LISTS:
        errors.append(
            f"generator_list='{generator_list}' is for charged-lepton probes only; "
            "use 'CCQE', 'CCMEC', 'RES', etc. for neutrinos"
        )

    if n_knots is not None and (n_knots < 30 or n_knots > 1000):
        warnings.append(f"n_knots={n_knots} is outside recommended range [30, 1000]")

    if max_energy is not None:
        if max_energy < 0:
            errors.append(f"max_energy must be >= 0, got {max_energy}")
        elif max_energy > 1000:
            warnings.append(
                f"max_energy={max_energy} GeV exceeds 1000 GeV; spline generation may be very slow"
            )

    return errors, warnings

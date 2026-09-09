"""Validation rules for gmkspl/gevgen inputs.

Ported from genie-mcp/genie_mcp/tools/gmkspl_tool.py:_validate_gmkspl_inputs.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .paths import sha256_short
from .pdg import CHARGED_LEPTON_PDGS, DARK_MATTER_PDGS, NEUTRINO_PDGS

# Tune format: <PREFIX><YY>_<NN><x>_<PP>_<FFF>  e.g. G18_02a_00_000, GEM21_11a_00_000
TUNE_RE = re.compile(r"^[A-Z]+\d{2}_\d{2}[a-z]_\d{2}_[0-9a-z]+$")

_EM_LISTS = frozenset({"EM", "EMQE", "EMMEC", "EMRES", "EMDIS", "EMQE+EMMEC"})


def _tune_family_dir(
    tune_base: str,
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]],
) -> Optional[Path]:
    """Find the tune family dir <base>/ on GXMLPATH then $GENIE/config.

    Mirrors GENIE's XML resolution order: each --gxmlpath dir is searched
    before the installed config tree. Returns the first match, or None.
    """
    for d in (gxmlpath_dirs or []):
        cand = Path(d) / tune_base
        if cand.is_dir():
            return cand
    install_cfg = Path(genie_bin_dir).parent / "config" / tune_base
    return install_cfg if install_cfg.is_dir() else None


def tune_xml_hashes(
    tune: str,
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]] = None,
) -> dict[str, str]:
    """Hash every XML in the resolved tune family dir: {relpath: sha256_short}.

    The family dir (e.g. GEM26_22a/ for tune GEM26_22a_05_000) holds the bytes
    that actually set the physics — CommonParam / ModelConfiguration /
    EventGenerator plus every PP-variant subdir — resolved with the same
    GXMLPATH-then-$GENIE/config order GENIE uses. Recording their hashes in
    the runlog makes a run replayable even after the tune files are edited.
    Returns {} if the family dir cannot be resolved (validation reports that
    separately).
    """
    tune_base = "_".join(tune.split("_")[:2])
    family = _tune_family_dir(tune_base, genie_bin_dir, gxmlpath_dirs)
    if family is None:
        return {}
    return {
        p.relative_to(family).as_posix(): sha256_short(p)
        for p in sorted(family.rglob("*.xml"))
    }


def validate_gmkspl_inputs(
    nu_pdgs: list[int],
    tgt_pdgs: list[int],
    tune: str,
    generator_list: str,
    max_energy: Optional[float],
    n_knots: Optional[int],
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]] = None,
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
    if any(p in DARK_MATTER_PDGS for p in nu_pdgs):
        errors.append(
            "dark-matter probe: use scripts/run_gmkspl_dm.py (gmkspl_dm takes "
            "-m/-z/-g and no -p); gmkspl cannot run it"
        )

    if not tgt_pdgs:
        errors.append("targets must not be empty")
    else:
        _BARE_NUCLEONS = {2112, 2212}
        for pdg in tgt_pdgs:
            if pdg not in _BARE_NUCLEONS and not (1000000000 <= pdg <= 1999999999):
                errors.append(f"PDG {pdg} does not look like a valid nuclear target")
        # Advisory only: gmkspl on a free/single-nucleon target can write an
        # EMPTY spline list and still exit 0 (e.g. H1 has no bound neutron).
        # outputs.spline_count is the always-correct detector behind this warn.
        _FREE_TARGETS = {2112, 2212, 1000010010}
        free = sorted(p for p in set(tgt_pdgs) if p in _FREE_TARGETS)
        if free:
            warnings.append(
                f"free/single-nucleon target(s) {free} may yield an empty "
                "spline list for nuclear channels despite returncode 0; "
                "check outputs.spline_count"
            )

    if not TUNE_RE.match(tune):
        errors.append(f"Invalid tune '{tune}': expected 4-part form, e.g. G18_02a_00_000")
    else:
        tune_base = "_".join(tune.split("_")[:2])
        if _tune_family_dir(tune_base, genie_bin_dir, gxmlpath_dirs) is None:
            errors.append(
                f"Tune family '{tune_base}' not found in $GENIE/config "
                f"or any --gxmlpath dir ({gxmlpath_dirs or 'none given'})"
            )

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


_BARE_NUCLEONS = frozenset({2112, 2212})


def validate_gevgen_inputs(
    nu_pdg: int,
    tgt_pdg: int,
    n_events: int,
    energy: float,
    cross_sections: str,
    tune: str,
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]] = None,
) -> tuple[list[str], list[str]]:
    """Validate mono-energetic gevgen inputs. Returns (errors, warnings).

    Flux / energy-range mode is intentionally not handled here.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if nu_pdg in DARK_MATTER_PDGS:
        errors.append(
            "dark-matter probe: use scripts/run_gevgen_dm.py (gevgen_dm takes "
            "-m/-z/-g and no -p); gevgen cannot run it"
        )
    elif nu_pdg not in NEUTRINO_PDGS:
        warnings.append(
            f"probe PDG {nu_pdg} is not a neutrino; gevgen expects a neutrino probe"
        )

    if tgt_pdg not in _BARE_NUCLEONS and not (1_000_000_000 <= tgt_pdg <= 1_999_999_999):
        errors.append(f"PDG {tgt_pdg} does not look like a valid nuclear target")

    if n_events is None or n_events <= 0:
        errors.append(f"n_events must be > 0, got {n_events}")

    if energy is None or energy <= 0:
        errors.append(f"energy must be > 0 GeV for mono-energetic mode, got {energy}")

    if not cross_sections:
        errors.append("--cross-sections is required (path to spline XML)")
    elif not Path(cross_sections).exists():
        errors.append(f"cross_sections file not found: {cross_sections}")

    if not TUNE_RE.match(tune):
        errors.append(f"Invalid tune '{tune}': expected 4-part form, e.g. G18_02a_00_000")
    else:
        tune_base = "_".join(tune.split("_")[:2])
        if _tune_family_dir(tune_base, genie_bin_dir, gxmlpath_dirs) is None:
            errors.append(
                f"Tune family '{tune_base}' not found in $GENIE/config "
                f"or any --gxmlpath dir ({gxmlpath_dirs or 'none given'})"
            )

    return errors, warnings


# ---- boosted dark matter (gmkspl_dm / gevgen_dm) ---------------------------
# Generator lists a GDM* tune resolves: the family's TuneGeneratorList.xml
# (Default = DMEL+DMDIS+DME+DMRES, NonRes) plus the named DM lists in
# $GENIE/config/EventGeneratorListAssembler.xml.
_DM_LISTS = frozenset({"Default", "NonRes", "DM", "DMEL", "DMDIS", "DME", "DMRES",
                       "DMHAD", "DMNORES"})


def _validate_dm_common(
    tune: str,
    generator_list: str,
    dm_mass: Optional[float],
    med_ratio: Optional[float],
    zp_coupling: Optional[float],
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]],
) -> tuple[list[str], list[str]]:
    """Rules shared by the two DM runners: model parameters, tune, list."""
    errors: list[str] = []
    warnings: list[str] = []

    if dm_mass is None or dm_mass <= 0:
        errors.append(f"--mass (DM mass) must be > 0 GeV, got {dm_mass}")
    if med_ratio is None or med_ratio <= 0:
        errors.append(f"--med-ratio (mediator/DM mass ratio) must be > 0, got {med_ratio}")
    if zp_coupling is None or zp_coupling <= 0:
        errors.append(f"--zp-coupling must be > 0, got {zp_coupling}")

    if not TUNE_RE.match(tune):
        errors.append(f"Invalid tune '{tune}': expected 4-part form, e.g. GDM18_00a_00_000")
    else:
        tune_base = "_".join(tune.split("_")[:2])
        if _tune_family_dir(tune_base, genie_bin_dir, gxmlpath_dirs) is None:
            errors.append(
                f"Tune family '{tune_base}' not found in $GENIE/config "
                f"or any --gxmlpath dir ({gxmlpath_dirs or 'none given'})"
            )
        tune_prefix = re.match(r"^([A-Z]+)", tune).group(1)
        if tune_prefix != "GDM":
            errors.append(
                f"DM runs need a GDM* tune (e.g. GDM18_00a_00_000); '{tune}' "
                "resolves no DM generators"
            )

    if generator_list not in _DM_LISTS:
        errors.append(
            f"generator_list='{generator_list}' is not a DM list; "
            f"use one of {sorted(_DM_LISTS)}"
        )

    return errors, warnings


def validate_gmkspl_dm_inputs(
    tgt_pdgs: list[int],
    tune: str,
    generator_list: str,
    dm_mass: Optional[float],
    med_ratio: Optional[float],
    zp_coupling: Optional[float],
    max_energy: Optional[float],
    n_knots: Optional[int],
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]] = None,
) -> tuple[list[str], list[str]]:
    """Validate gmkspl_dm inputs. Returns (errors, warnings).

    The probe is implicit (kPdgDarkMatter = 2000010000). Spline keys do not
    carry the mass / mediator ratio / coupling, so those are recorded in the
    runlog only; one XML per (mass, z, g).
    """
    errors, warnings = _validate_dm_common(
        tune, generator_list, dm_mass, med_ratio, zp_coupling,
        genie_bin_dir, gxmlpath_dirs,
    )

    if not tgt_pdgs:
        errors.append("targets must not be empty")
    else:
        for pdg in tgt_pdgs:
            if pdg not in _BARE_NUCLEONS and not (1_000_000_000 <= pdg <= 1_999_999_999):
                errors.append(f"PDG {pdg} does not look like a valid nuclear target")
        _FREE_TARGETS = {2112, 2212, 1000010010}
        free = sorted(p for p in set(tgt_pdgs) if p in _FREE_TARGETS)
        if free:
            warnings.append(
                f"free/single-nucleon target(s) {free} may yield an empty "
                "spline list for nuclear channels despite returncode 0; "
                "check outputs.spline_count"
            )

    if n_knots is not None and (n_knots < 30 or n_knots > 1000):
        warnings.append(f"n_knots={n_knots} is outside recommended range [30, 1000]")

    if max_energy is not None:
        if max_energy < 0:
            errors.append(f"max_energy must be >= 0, got {max_energy}")
        elif dm_mass is not None and max_energy <= dm_mass:
            errors.append(
                f"max_energy={max_energy} GeV must exceed the DM mass {dm_mass} GeV "
                "(the spline energy is the DM total energy)"
            )
        elif max_energy > 1000:
            warnings.append(
                f"max_energy={max_energy} GeV exceeds 1000 GeV; spline generation may be very slow"
            )

    return errors, warnings


def validate_gevgen_dm_inputs(
    tgt_pdg: int,
    n_events: Optional[int],
    energy_min: Optional[float],
    energy_max: Optional[float],
    flux: Optional[str],
    dm_mass: Optional[float],
    med_ratio: Optional[float],
    zp_coupling: Optional[float],
    cross_sections: str,
    tune: str,
    generator_list: str,
    genie_bin_dir: str,
    gxmlpath_dirs: Optional[list[str]] = None,
) -> tuple[list[str], list[str]]:
    """Validate gevgen_dm inputs. Returns (errors, warnings).

    `energy_max is None` means fixed-energy mode. In range mode gevgen_dm
    needs a flux (`-f`); given a range without one it silently generates at
    fixed E = emin, so that combination is rejected here.
    """
    errors, warnings = _validate_dm_common(
        tune, generator_list, dm_mass, med_ratio, zp_coupling,
        genie_bin_dir, gxmlpath_dirs,
    )

    if tgt_pdg not in _BARE_NUCLEONS and not (1_000_000_000 <= tgt_pdg <= 1_999_999_999):
        errors.append(f"PDG {tgt_pdg} does not look like a valid nuclear target")

    if n_events is None or n_events <= 0:
        errors.append(f"n_events must be > 0, got {n_events}")

    if energy_min is None or energy_min <= 0:
        errors.append(f"energy must be > 0 GeV, got {energy_min}")
    elif energy_max is None:
        # fixed energy: gevgen_dm takes p = sqrt(E^2 - m^2)
        if dm_mass is not None and energy_min <= dm_mass:
            errors.append(
                f"fixed DM energy {energy_min} GeV must exceed the DM mass {dm_mass} GeV"
            )
        if flux:
            errors.append(
                "--flux needs an energy range (-e emin,emax); with a single "
                "energy gevgen_dm has no spectrum to sample"
            )
    else:
        if energy_max <= energy_min:
            errors.append(f"energy range must have emax > emin, got {energy_min},{energy_max}")
        if dm_mass is not None and energy_max <= dm_mass:
            errors.append(
                f"energy range upper edge {energy_max} GeV must exceed the DM mass {dm_mass} GeV"
            )
        elif dm_mass is not None and energy_min < dm_mass:
            warnings.append(
                f"energy range starts below the DM mass ({energy_min} < {dm_mass} GeV); "
                "flux bins below the mass are unphysical and only waste throws"
            )
        if not flux:
            errors.append(
                "energy range given without --flux: gevgen_dm would silently run "
                "at fixed E = emin; pass --flux 1 for a flat spectrum, a TF1 "
                "expression, a 2-column file, or file.root,hist"
            )

    if not cross_sections:
        errors.append("--cross-sections is required (path to spline XML)")
    elif not Path(cross_sections).exists():
        errors.append(f"cross_sections file not found: {cross_sections}")

    return errors, warnings

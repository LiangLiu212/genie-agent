"""PDG resolution backed by the shared `shared/pdg.json` snapshot.

The data (probe/nucleon names+codes, the element->Z table) is generated once by
`shared/build_pdg.py` from GENIE's PDG table + the PDG API, and read here at
runtime with no `pdg` dependency. jobsub-agent reads the *same* file via its own
thin loader, so both agents resolve PDGs identically.

Public API (unchanged for callers):
  resolve_pdg(value)       -> int PDG code from alias / int / numeric string /
                              "<Sym><A>" nucleus (e.g. "Ar40").
  canonical_probe(value)   -> filename-safe probe alias (numu, eminus, ...).
  canonical_target(value)  -> filename-safe nucleus alias (Ar40), proton/neutron,
                              else str(code).
  CHARGED_LEPTON_PDGS, NEUTRINO_PDGS -> frozensets of int codes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PDG_JSON = _REPO_ROOT / "shared" / "pdg.json"

_data = json.loads(_PDG_JSON.read_text())

_PROBES:   dict[str, dict] = _data["probes"]
_NUCLEONS: dict[str, dict] = _data["nucleons"]
ELEMENTS:  dict[str, int]  = _data["elements"]          # symbol -> Z
_Z_TO_SYMBOL: dict[int, str] = {z: s for s, z in ELEMENTS.items()}

# alias (lowercased) -> code, across probes + nucleons
ALIAS_TO_PDG: dict[str, int] = {}
# code -> canonical filename-safe alias (probes + nucleons)
_CODE_TO_CANONICAL: dict[int, str] = {}
for _entry in (*_PROBES.values(), *_NUCLEONS.values()):
    _code = _entry["code"]
    _CODE_TO_CANONICAL[_code] = _entry["canonical"]
    for _a in _entry["aliases"]:
        ALIAS_TO_PDG[_a.lower()] = _code

CHARGED_LEPTON_PDGS = frozenset(
    e["code"] for e in _PROBES.values() if e["kind"] == "charged_lepton"
)
NEUTRINO_PDGS = frozenset(
    e["code"] for e in _PROBES.values() if e["kind"] == "neutrino"
)

_NUCLEUS_RE = re.compile(r"^([A-Z][a-z]?)(\d+)$")   # e.g. "Ar40", "C12", "H1"
_NUCLEUS_CODE_MIN = 1_000_000_000


def _nucleus_code(symbol: str, mass_number: int) -> int:
    return _NUCLEUS_CODE_MIN + ELEMENTS[symbol] * 10_000 + mass_number * 10


def resolve_pdg(value: str | int) -> int:
    """Resolve a PDG integer from an alias, int, numeric string, or nucleus name."""
    if isinstance(value, int):
        return value
    v = str(value).strip()
    if v.lower() in ALIAS_TO_PDG:
        return ALIAS_TO_PDG[v.lower()]
    m = _NUCLEUS_RE.match(v)
    if m and m.group(1) in ELEMENTS:
        return _nucleus_code(m.group(1), int(m.group(2)))
    try:
        return int(v)
    except ValueError:
        known = ", ".join(sorted(ALIAS_TO_PDG))
        raise ValueError(
            f"Unknown PDG alias '{v}'. Known particle aliases: {known}. "
            f"Nuclei use '<Symbol><A>' (e.g. 'Ar40', 'C12')."
        )


def canonical_probe(value: str | int) -> str:
    """Filename-safe alias for a probe (neutrino / charged lepton / nucleon).

    Falls back to str(code) when no canonical alias exists.
    """
    code = resolve_pdg(value)
    return _CODE_TO_CANONICAL.get(code, str(code))


def canonical_target(value: str | int) -> str:
    """Filename-safe alias for a target: 'Ar40' for nuclei, proton/neutron for
    free nucleons, else str(code)."""
    code = resolve_pdg(value)
    if code in _CODE_TO_CANONICAL:
        return _CODE_TO_CANONICAL[code]
    if code >= _NUCLEUS_CODE_MIN:
        z = (code // 10_000) % 1_000
        a = (code // 10) % 1_000
        sym = _Z_TO_SYMBOL.get(z)
        if sym:
            return f"{sym}{a}"
    return str(code)

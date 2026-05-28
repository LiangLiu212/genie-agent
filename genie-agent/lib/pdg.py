"""PDG alias tables for nuclei, neutrinos, and charged leptons.

`resolve_pdg(value)` returns the integer PDG code from an alias string,
integer, or numeric string.

`canonical_probe(value)` returns the filename-safe alias for a probe
(eminus/eplus/muminus/muplus/tauminus/tauplus + nue/nuebar/numu/numubar/
nutau/nutaubar). Used when building directory paths so filenames never
contain '+' or '-'.
"""
from __future__ import annotations


NUCLEUS_PDG: dict[str, int] = {
    # Hydrogen / light
    "H1":    1000010010,
    "H2":    1000010020,
    "H3":    1000010030,
    "He3":   1000020030,
    "He4":   1000020040,
    # p-shell
    "Li6":   1000030060,
    "Li7":   1000030070,
    "Be9":   1000040090,
    "B10":   1000050100,
    "B11":   1000050110,
    "C12":   1000060120,
    "C13":   1000060130,
    "N14":   1000070140,
    "O16":   1000080160,
    "O18":   1000080180,
    # sd-shell
    "Ne20":  1000100200,
    "Na23":  1000110230,
    "Mg24":  1000120240,
    "Al27":  1000130270,
    "Si28":  1000140280,
    "Si29":  1000140290,
    "Si30":  1000140300,
    "P31":   1000150310,
    "S32":   1000160320,
    "Cl35":  1000170350,
    "Cl37":  1000170370,
    "Ar36":  1000180360,
    "Ar38":  1000180380,
    "Ar40":  1000180400,
    "K39":   1000190390,
    "Ca40":  1000200400,
    "Ca44":  1000200440,
    "Ca48":  1000200480,
    # fp-shell
    "Ti48":  1000220480,
    "Cr52":  1000240520,
    "Fe54":  1000260540,
    "Fe56":  1000260560,
    "Fe58":  1000260580,
    "Ni58":  1000280580,
    "Ni60":  1000280600,
    "Cu63":  1000290630,
    "Cu65":  1000290650,
    "Zn64":  1000300640,
    # medium-heavy
    "Ge76":  1000320760,
    "Se82":  1000340820,
    "Kr83":  1000360830,
    "Kr86":  1000360860,
    "Sr88":  1000380880,
    "Zr90":  1000400900,
    "Mo98":  1000420980,
    "Ag108": 1000471080,
    "Cd114": 1000481140,
    "In115": 1000491150,
    "Sn120": 1000501200,
    "Te130": 1000521300,
    "I127":  1000531270,
    "Xe131": 1000541310,
    "Cs133": 1000551330,
    "Ba138": 1000561380,
    # heavy
    "La139": 1000571390,
    "Ce140": 1000581400,
    "Nd142": 1000601420,
    "Sm152": 1000621520,
    "Gd158": 1000641580,
    "W184":  1000741840,
    "Au197": 1000791970,
    "Hg202": 1000802020,
    "Pb204": 1000822040,
    "Pb206": 1000822060,
    "Pb207": 1000822070,
    "Pb208": 1000822080,
    "Bi209": 1000832090,
    "U235":  1000922350,
    "U238":  1000922380,
}

# Canonical neutrino aliases (filename-safe).
NEUTRINO_PDG: dict[str, int] = {
    "nue":      12,
    "nuebar":  -12,
    "numu":     14,
    "numubar": -14,
    "nutau":    16,
    "nutaubar":-16,
}

# Canonical charged-lepton aliases (filename-safe; no '+' or '-').
LEPTON_PDG: dict[str, int] = {
    "eminus":     11,
    "eplus":     -11,
    "muminus":    13,
    "muplus":    -13,
    "tauminus":   15,
    "tauplus":   -15,
}

# Legacy aliases — accepted on input, normalised to canonical on output.
_LEGACY_LEPTON_ALIASES: dict[str, int] = {
    "e-":       11,   "e+":      -11,
    "mu-":      13,   "mu+":     -13,
    "tau-":     15,   "tau+":    -15,
    "electron": 11,   "positron": -11,
    "muon":     13,   "antimuon": -13,
    "tau":      15,   "antitau":  -15,
}

ALL_PDG_ALIASES: dict[str, int] = {
    **NUCLEUS_PDG,
    **NEUTRINO_PDG,
    **LEPTON_PDG,
    **_LEGACY_LEPTON_ALIASES,
}

# Reverse maps for canonical_probe / canonical_target.
_PDG_TO_NEUTRINO: dict[int, str] = {v: k for k, v in NEUTRINO_PDG.items()}
_PDG_TO_LEPTON:   dict[int, str] = {v: k for k, v in LEPTON_PDG.items()}
_PDG_TO_NUCLEUS:  dict[int, str] = {v: k for k, v in NUCLEUS_PDG.items()}

CHARGED_LEPTON_PDGS = frozenset({11, -11, 13, -13, 15, -15})
NEUTRINO_PDGS       = frozenset({12, -12, 14, -14, 16, -16})


def resolve_pdg(value: str | int) -> int:
    """Resolve a PDG integer from an alias string, integer, or numeric string."""
    if isinstance(value, int):
        return value
    v = str(value).strip()
    if v in ALL_PDG_ALIASES:
        return ALL_PDG_ALIASES[v]
    try:
        return int(v)
    except ValueError:
        known = ", ".join(sorted(ALL_PDG_ALIASES.keys()))
        raise ValueError(f"Unknown PDG alias '{v}'. Known: {known}")


def canonical_probe(value: str | int) -> str:
    """Return the filename-safe alias for a probe (neutrino or charged lepton).

    Falls back to str(pdg) if no canonical alias exists.
    """
    pdg = resolve_pdg(value)
    if pdg in _PDG_TO_NEUTRINO:
        return _PDG_TO_NEUTRINO[pdg]
    if pdg in _PDG_TO_LEPTON:
        return _PDG_TO_LEPTON[pdg]
    return str(pdg)


def canonical_target(value: str | int) -> str:
    """Return the filename-safe alias for a nuclear target (e.g. 'Ar40')."""
    pdg = resolve_pdg(value)
    if pdg in _PDG_TO_NUCLEUS:
        return _PDG_TO_NUCLEUS[pdg]
    return str(pdg)

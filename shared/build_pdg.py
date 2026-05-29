#!/usr/bin/env python3
"""Generate shared/pdg.json by combining GENIE's PDG table with the PDG API.

This is a **build-time** snapshot tool (same spirit as
scripts/refresh_genie_env.py): run it once, commit the JSON, and the agents
read the JSON at runtime with no `pdg` dependency.

Sources combined:
  1. GENIE's `genie_pdg_table*.txt` — authoritative *names + codes* GENIE
     itself uses (`nu_mu`, `mu-`, `proton`, ...). We pull the GENIE name for
     each probe/nucleon code and assert the code is present.
  2. The PDG Python API (`pdg.connect()`) — validates each code and supplies
     the canonical particle name + mass. Neutrinos have no mass (null).
  3. Nuclear formula — neither source enumerates ions, so nuclei are resolved
     at runtime from the embedded element->Z table via
     code = 1000000000 + Z*10000 + A*10.

Scope (per design): probes (charged leptons + neutrinos) + free nucleons +
nuclei. Run:

    pixi run python shared/build_pdg.py            # default table + output
    pixi run python shared/build_pdg.py --table <file> --output <file>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent
_DEFAULT_TABLE = (
    "/exp/dune/app/users/liangliu/GENIEINCLXX/GENIE_RC/Generator/"
    "data/evgen/catalogues/pdg/genie_pdg_table_mk_single_pion.txt"
)
_DEFAULT_OUTPUT = _SHARED_DIR / "pdg.json"

# Our filename-safe canonical aliases, by |code| and sign.
_NEUTRINO_FLAVOUR = {12: "nue", 14: "numu", 16: "nutau"}          # code>0
_NEUTRINO_FLAVOUR_BAR = {12: "nuebar", 14: "numubar", 16: "nutaubar"}
_LEPTON_FLAVOUR = {11: "e", 13: "mu", 15: "tau"}                   # +minus/+plus

# Extra human aliases accepted on input (genie_name + canonical are added
# automatically). Keyed by signed code.
_LEGACY_ALIASES = {
    11: ["electron"], -11: ["positron"],
    13: ["muon"],     -13: ["antimuon"],
    15: ["tau", "tauon"], -15: ["antitau"],
    2212: ["p", "p+"], -2212: ["pbar"],
    2112: ["n", "n0"], -2112: ["nbar"],
}

# Standard element symbol -> Z (1..118), for nuclear-code formula.
_ELEMENTS = {
    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
    "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
    "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22,
    "V": 23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29,
    "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34, "Br": 35, "Kr": 36,
    "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Tc": 43,
    "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50,
    "Sb": 51, "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57,
    "Ce": 58, "Pr": 59, "Nd": 60, "Pm": 61, "Sm": 62, "Eu": 63, "Gd": 64,
    "Tb": 65, "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69, "Yb": 70, "Lu": 71,
    "Hf": 72, "Ta": 73, "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78,
    "Au": 79, "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83, "Po": 84, "At": 85,
    "Rn": 86, "Fr": 87, "Ra": 88, "Ac": 89, "Th": 90, "Pa": 91, "U": 92,
    "Np": 93, "Pu": 94, "Am": 95, "Cm": 96, "Bk": 97, "Cf": 98, "Es": 99,
    "Fm": 100, "Md": 101, "No": 102, "Lr": 103, "Rf": 104, "Db": 105,
    "Sg": 106, "Bh": 107, "Hs": 108, "Mt": 109, "Ds": 110, "Rg": 111,
    "Cn": 112, "Nh": 113, "Fl": 114, "Mc": 115, "Lv": 116, "Ts": 117,
    "Og": 118,
}

_PROBE_CODES = [11, -11, 13, -13, 15, -15, 12, -12, 14, -14, 16, -16]
_NUCLEON_CODES = [2212, -2212, 2112, -2112]


def parse_genie_table(path: Path) -> dict[int, str]:
    """Return {code: genie_name} for every named row in the GENIE PDG table.

    Definition rows look like `<i> <NAME> <KF> <AP> <class> ...`; antiparticle
    rows like `<i> <name> <-KF> <ref> 0`. Both carry name in field[1] and the
    signed code in field[2].
    """
    out: dict[int, str] = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        f = line.split()
        if len(f) < 3:
            continue
        if not (f[0].lstrip("-").isdigit() and f[2].lstrip("-").isdigit()):
            continue
        code = int(f[2])
        out.setdefault(code, f[1])  # keep first (definition) name
    return out


def canonical_alias(code: int) -> str:
    a = abs(code)
    if a in _NEUTRINO_FLAVOUR:
        return _NEUTRINO_FLAVOUR[a] if code > 0 else _NEUTRINO_FLAVOUR_BAR[a]
    if a in _LEPTON_FLAVOUR:
        return f"{_LEPTON_FLAVOUR[a]}minus" if code > 0 else f"{_LEPTON_FLAVOUR[a]}plus"
    if code == 2212:  return "proton"
    if code == -2212: return "antiproton"
    if code == 2112:  return "neutron"
    if code == -2112: return "antineutron"
    raise ValueError(f"no canonical alias rule for code {code}")


def build_entry(code: int, kind: str, genie_names: dict[int, str], api, warnings: list[str]) -> dict:
    genie_name = genie_names.get(code)
    if genie_name is None:
        warnings.append(f"code {code} not found in GENIE table")
    canon = canonical_alias(code)

    pdg_name, mass_gev = None, None
    if api is not None:
        try:
            p = api.get_particle_by_mcid(code)
            pdg_name = p.name
            try:
                mass_gev = p.mass
            except Exception:
                mass_gev = None  # neutrinos: no best mass
        except Exception as e:
            warnings.append(f"PDG API has no entry for code {code}: {e}")

    aliases: list[str] = []
    for a in [genie_name, canon, *(_LEGACY_ALIASES.get(code, [])), str(code)]:
        if a and a not in aliases:
            aliases.append(a)

    return {
        "code": code,
        "kind": kind,
        "genie_name": genie_name,
        "canonical": canon,
        "aliases": aliases,
        "pdg_name": pdg_name,
        "mass_gev": mass_gev,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--table", default=_DEFAULT_TABLE, help="GENIE pdg table path")
    ap.add_argument("--output", default=str(_DEFAULT_OUTPUT), help="output JSON path")
    args = ap.parse_args()

    table_path = Path(args.table)
    if not table_path.exists():
        sys.stderr.write(f"error: GENIE table not found: {table_path}\n")
        return 2
    genie_names = parse_genie_table(table_path)

    pdg_version = None
    api = None
    try:
        import pdg
        api = pdg.connect()
        pdg_version = getattr(pdg, "__version__", "?")
    except Exception as e:
        sys.stderr.write(
            f"warning: `pdg` API unavailable ({e}); "
            f"emitting names/codes from the GENIE table without enrichment\n"
        )

    warnings: list[str] = []
    probes = {}
    for code in _PROBE_CODES:
        kind = "neutrino" if abs(code) in _NEUTRINO_FLAVOUR else "charged_lepton"
        e = build_entry(code, kind, genie_names, api, warnings)
        probes[e["canonical"]] = e

    nucleons = {}
    for code in _NUCLEON_CODES:
        e = build_entry(code, "nucleon", genie_names, api, warnings)
        nucleons[e["canonical"]] = e

    doc = {
        "_comment": (
            "Generated by shared/build_pdg.py — DO NOT hand-edit. Combines GENIE's "
            "PDG table (names+codes) with the PDG API (validation, canonical name, "
            "mass). Nuclei are resolved at runtime by formula "
            "1000000000+Z*10000+A*10 from 'elements'. Read by genie-agent and "
            "jobsub-agent via their own thin pdg.py loaders."
        ),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": {
            "genie_pdg_table": str(table_path),
            "pdg_api_version": pdg_version,
        },
        "probes": probes,
        "nucleons": nucleons,
        "elements": _ELEMENTS,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2) + "\n")

    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    print(f"wrote {out_path}  ({len(probes)} probes, {len(nucleons)} nucleons, "
          f"{len(_ELEMENTS)} elements; pdg_api={pdg_version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

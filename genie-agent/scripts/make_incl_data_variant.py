#!/usr/bin/env python3
"""
make_incl_data_variant.py: copy the INCL++ data directory and rewrite one mass-excess row so
that INCL's *real* proton separation energy of a target takes a chosen value (S_p scan).

INCL reads <inclxx-data-dir>/walletlifetime.dat (rows "A Z excess[MeV]", atomic mass excess)
and forms M(A,Z) = A*amu + excess - Z*m_e (G4INCLNuclearMassTable.cc:132). With the
separation-energy scheme `real` (NucleusGenINCL param inclxx-separation-energies = real) the
proton separation energy of the target (A, Z) is

    S_p = m_p + M(A-1, Z-1) - M(A, Z) = (m_p + m_e - amu) + excess(A-1, Z-1) - excess(A, Z)

so rewriting the daughter row (B11 for C12) sets S_p; S_n (C11 row) is left untouched.
The copy keeps every other file of the directory (table_radius_hfb.dat, antinucleon tables)
because INCL reads them from the same path. Default source: <INCLXX_DATA_DIR>/data of the
genie_inclxx installation (from genie-agent/config/env/genie_inclxx.json); the copy is written
next to it as data-<name>, to be referenced as ${INCLXX_DATA_DIR}/data-<name> in a tune-local
NucleusGenINCL.xml.

    pixi run python genie-agent/scripts/make_incl_data_variant.py --name Sp10 --sp 10.0
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT = HERE.parent

# INCL's own constants (utils/src/G4INCLParticleTable.cc:66-67, utils/src/G4INCLNuclearMassTable.cc:26-27)
M_P = 938.27203
M_N = 939.56536
AMU = 931.494061
M_E = 0.5109988


def read_rows(path):
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"unexpected line in {path}: {line!r}")
        rows.append((int(parts[0]), int(parts[1]), float(parts[2]), line))
    return rows


def excess_of(rows, A, Z):
    for a, z, ex, _ in rows:
        if a == A and z == Z:
            return ex
    raise KeyError(f"no row for A={A} Z={Z}")


def separation_energies(rows, A, Z):
    ex = excess_of(rows, A, Z)
    return ((M_P + M_E - AMU) + excess_of(rows, A - 1, Z - 1) - ex,
            (M_N - AMU) + excess_of(rows, A - 1, Z) - ex)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--name", required=True, help="suffix of the copy: data-<name>")
    ap.add_argument("--sp", type=float, required=True, help="target proton separation energy [MeV]")
    ap.add_argument("--A", type=int, default=12)
    ap.add_argument("--Z", type=int, default=6)
    ap.add_argument("--src", type=Path, default=None, help="INCL data dir (default <INCLXX_DATA_DIR>/data)")
    ap.add_argument("--dst-root", type=Path, default=None, help="parent of the copy (default <INCLXX_DATA_DIR>)")
    ap.add_argument("--installation", default="genie_inclxx")
    ap.add_argument("--force", action="store_true", help="overwrite an existing copy")
    args = ap.parse_args(argv)

    if args.src is None or args.dst_root is None:
        env = json.loads((AGENT / "config" / "env" / f"{args.installation}.json").read_text())
        root = Path(env["INCLXX_DATA_DIR"])
        args.src = args.src or root / "data"
        args.dst_root = args.dst_root or root
    dst = args.dst_root / f"data-{args.name}"
    if dst.exists():
        if not args.force:
            sys.exit(f"{dst} exists; use --force to overwrite")
        shutil.rmtree(dst)
    shutil.copytree(args.src, dst)

    table = dst / "walletlifetime.dat"
    rows = read_rows(table)
    sp0, sn0 = separation_energies(rows, args.A, args.Z)
    A, Z = args.A - 1, args.Z - 1
    new_excess = args.sp - (M_P + M_E - AMU) + excess_of(rows, args.A, args.Z)
    out, changed = [], 0
    for a, z, ex, line in rows:
        if a == A and z == Z:
            newline = f"{a:3d}{z:5d}{new_excess:14.4f}"
            print(f"row A={A} Z={Z}: {line!r} -> {newline!r}")
            out.append(newline); changed += 1
        else:
            out.append(line)
    assert changed == 1, changed
    table.write_text("\n".join(out) + "\n")
    sp1, sn1 = separation_energies(read_rows(table), args.A, args.Z)
    print(f"{args.src} -> {dst}")
    print(f"target (A={args.A}, Z={args.Z}): S_p {sp0:.4f} -> {sp1:.4f} MeV (requested {args.sp}), S_n {sn0:.4f} -> {sn1:.4f} MeV")
    print(f"inclxx-data-dir value: ${{INCLXX_DATA_DIR}}/data-{args.name}")


if __name__ == "__main__":
    main()

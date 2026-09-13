#!/usr/bin/env python3
"""
spline_knot_diff.py: compare the knots of two GENIE cross-section spline XML files.

For every <spline name=...> present in both files it prints the number of knots and the
maximum relative difference of xsec over knots at the same energy; energies must match.
Exit status 0 when every common spline agrees within --rtol, 1 otherwise or when the two
files hold different spline sets. Used for the p_F / S_p scan equivalence check
(GEM26_44b_12/14/15_000 must reproduce the 2026-09-04 locframe-on spline knot by knot).

    pixi run python genie-agent/scripts/spline_knot_diff.py a.xml b.xml [--rtol 1e-9]
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET


def load(path):
    root = ET.parse(path).getroot()
    tunes = [t.get("name") for t in root.iter("genie_tune")]
    splines = {}
    for s in root.iter("spline"):
        knots = [(float(k.find("E").text), float(k.find("xsec").text)) for k in s.iter("knot")]
        splines[s.get("name")] = knots
    return tunes, splines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--rtol", type=float, default=1e-9)
    args = ap.parse_args(argv)
    ta, sa = load(args.a); tb, sb = load(args.b)
    print(f"A: {args.a}\n   tune {ta}, {len(sa)} splines\nB: {args.b}\n   tune {tb}, {len(sb)} splines")
    ok = set(sa) == set(sb)
    if not ok:
        print("spline sets differ:", sorted(set(sa) ^ set(sb)))
    worst = 0.0
    for name in sorted(set(sa) & set(sb)):
        ka, kb = sa[name], sb[name]
        if len(ka) != len(kb) or any(abs(ea - eb) > 1e-9 * max(abs(ea), 1.0) for (ea, _), (eb, _) in zip(ka, kb)):
            print(f"  {name}: knot energies differ ({len(ka)} vs {len(kb)} knots)"); ok = False; continue
        rel = max((abs(xa - xb) / abs(xb) if xb else abs(xa - xb)) for (_, xa), (_, xb) in zip(ka, kb))
        worst = max(worst, rel)
        flag = "" if rel <= args.rtol else "   <-- differs"
        print(f"  {name}: {len(ka)} knots, max |dxsec/xsec| = {rel:.3e}{flag}")
        ok = ok and rel <= args.rtol
    print(f"overall max relative difference {worst:.3e}; {'EQUAL' if ok else 'DIFFERENT'} within rtol {args.rtol:g}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

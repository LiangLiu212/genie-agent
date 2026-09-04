"""Write a dump_hitnuc-style CSV whose momentum is the pre-FSI proton's
p_p' - q (stage-3 missing momentum) instead of the record nucleon.

Under the INCL-scheme vertex (2026-09-04) the record holds INCL's global ball
nucleon in every local-energy setting; the nucleon the scattering actually
used (local-energy frame when on) is only visible as |p_p' - q| of the primary
proton, up to INCL's energy-conservation rescaling. This script pairs each
event of a gst file with the dump_hitnuc row of the same GHEP (same order, same
event count) and writes
    pdg,px,py,pz,E,w,scat,r,q2
with (px,py,pz) = p_p' - q [GeV], E = m_p - (omega - T_p') [GeV] (the stage-3
E_m written as a nucleon energy, so m_p - E is E_m), w and r copied, scat = 1
for QEL, q2 = the record Q2 -- ready for make_struck_pr.py --csv.

Usage: pixi run python results/template/make_stage3_csv.py OUT.csv \
           --gst a.gst.root b.gst.root ... --dump a.csv b.csv ...
(gst and dump lists in the same chunk order; only pdg==2212 hit nucleons with
a primary proton are kept). Requires the same installation's gst (branches
Ev,pxv,pyv,pzv,El,pxl,pyl,pzl,hitnuc,qel,Q2,pdgi,Ei,pxi,pyi,pzi).
"""
import argparse
from pathlib import Path

import awkward as ak
import numpy as np
import uproot

M_P = 0.938272


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--gst", nargs="+", required=True)
    ap.add_argument("--dump", nargs="+", required=True)
    args = ap.parse_args()
    assert len(args.gst) == len(args.dump), "one dump csv per gst file"
    rows = []
    for gst, dump in zip(args.gst, args.dump):
        t = uproot.open(gst)["gst"]
        a = t.arrays(["Ev", "pxv", "pyv", "pzv", "El", "pxl", "pyl", "pzl",
                      "hitnuc", "qel", "Q2", "pdgi", "Ei", "pxi", "pyi", "pzi"],
                     library="ak")
        d = np.genfromtxt(dump, delimiter=",", names=True)
        n = len(a["Ev"])
        assert len(d) == n, f"{gst}: {n} events vs {len(d)} dump rows"
        isp = a.pdgi == 2212
        lead = ak.argmax(ak.where(isp, a.Ei, -1.0), axis=1, keepdims=True)
        g = lambda b: ak.to_numpy(ak.fill_none(ak.firsts(b[lead]), np.nan))
        Ep, pxp, pyp, pzp = g(a.Ei), g(a.pxi), g(a.pyi), g(a.pzi)
        nz = lambda b: ak.to_numpy(a[b])
        qx, qy, qz = nz("pxv") - nz("pxl"), nz("pyv") - nz("pyl"), nz("pzv") - nz("pzl")
        om = nz("Ev") - nz("El")
        keep = (nz("hitnuc") == 2212) & np.isfinite(Ep)
        E3 = M_P - (om - (Ep - M_P))          # nucleon-energy form of stage-3 E_m
        scat = np.where(nz("qel") == 1, 1, 0)
        rows.append(np.column_stack([
            np.full(keep.sum(), 2212), (pxp - qx)[keep], (pyp - qy)[keep], (pzp - qz)[keep],
            E3[keep], d["w"][keep], scat[keep], d["r"][keep], nz("Q2")[keep]]))
        print(f"{Path(gst).name}: {n} events, kept {keep.sum()}")
    allrows = np.vstack(rows)
    np.savetxt(args.out, allrows, delimiter=",", header="pdg,px,py,pz,E,w,scat,r,q2",
               comments="", fmt=["%d", "%.6f", "%.6f", "%.6f", "%.6f", "%.6f", "%d", "%.4f", "%.5f"])
    print(f"wrote {args.out} ({len(allrows):,} rows)")


if __name__ == "__main__":
    main()

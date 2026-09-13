#!/usr/bin/env python3
"""
make_incl_scan_readout.py: the numbers behind the p_F / S_p scan of the real GENIE-INCL chain.

For each scan tune (GEM26_44b_11..15_000, sub-tunes of genie-agent/tunes/GEM26_44b, 2026-09-12)
and the baseline GEM26_44b_05_000_lfon, reads the v1.0 ladder cache
results/prd-analyzer-v1.0/cache/ladder_c12/<tune>.npz (built by
make_emiss_ladder_q2cut.py --target C12 --tune <id> --no-q2cut --proton-sel 1p --build-only)
and prints per stage (2 = record hit nucleon, 3 = pre-FSI proton, 4 = post-FSI single proton)
the mean and quantiles of E_m = omega - T_p' (recoil term restored, as plotted) and |p_m|,
next to INCL's expected windows for the tune (S_p, V0_p = T_F + S_p, p_F), and the histdiag
comparison of every variant against the centre tune GEM26_44b_12_000 (rigid shift for S_p,
stretch for T_F). Output: results/incl-pf-sp-scan/scan_readout.txt (and stdout).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "results" / "template"))
import histdiag as hd                                    # noqa: E402
import make_emiss_ladder_q2cut as em                     # noqa: E402

CACHE = REPO / "results/prd-analyzer-v1.0/cache/ladder_c12"
OUT = REPO / "results/incl-pf-sp-scan"
# tune: (label, S_p, V0_p, p_F, T_F) [MeV, MeV/c]; INCL nucleon mass 938.2796
TUNES = {
    "GEM26_44b_05_000_lfon": ("baseline S=6.83 (INCL)",  6.83,  45.00, 270.34, 38.17),
    "GEM26_44b_11_000":      ("pF239 realS",            15.957, 45.96, 239.16, 30.00),
    "GEM26_44b_12_000":      ("pF270 realS (centre)",   15.957, 54.13, 270.34, 38.17),
    "GEM26_44b_13_000":      ("pF297 realS",            15.957, 61.96, 297.38, 46.00),
    "GEM26_44b_14_000":      ("Sp10 pF270",             10.00,  48.17, 270.34, 38.17),
    "GEM26_44b_15_000":      ("Sp22 pF270",             22.00,  60.17, 270.34, 38.17),
}
CENTRE = "GEM26_44b_12_000"
E_EDGES = np.arange(-20.5, 100.5 + 1e-9, 1.0)
P_EDGES = np.arange(0.0, 400.0 + 1e-9, 5.0)


def load(tune):
    c = dict(np.load(CACHE / f"{tune}.npz"))
    m_rec = em._m_rec_c12()
    for s in (2, 3, 4):
        c[f"E{s}r"] = c[f"E{s}"] + c[f"p{s}"] ** 2 / (2.0 * m_rec * 1000.0)
    return c


def q(a, qs=(0.01, 0.05, 0.5, 0.95, 0.99)):
    a = a[np.isfinite(a)]
    return np.quantile(a, qs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    data = {t: load(t) for t in TUNES if (CACHE / f"{t}.npz").exists()}
    say("# p_F / S_p scan readout (v1.0 ladder caches, 1p selection, no Q2 window)")
    say("# E_m = omega - T_p' [MeV] (recoil restored); stages: 2 record hit nucleon, 3 pre-FSI proton, 4 post-FSI 1p")
    for t, c in data.items():
        lab, Sp, V0, pF, TF = TUNES[t]
        n = int(c["n_sel"][0])
        say(f"\n== {t}  {lab}: expected S_p {Sp}, V0_p {V0}, p_F {pF}, T_F {TF}; n_sel = {n}")
        for s in (2, 3, 4):
            E, P = c[f"E{s}r"], c[f"p{s}"]
            qe, qp = q(E), q(P)
            say(f"  stage {s}: E_m mean {np.nanmean(E):7.2f}  q1/5/50/95/99 = {qe[0]:6.2f} {qe[1]:6.2f} {qe[2]:6.2f} {qe[3]:6.2f} {qe[4]:6.2f}"
                f" | |p_m| mean {np.nanmean(P):6.1f}  q1/50/99 = {qp[0]:5.1f} {qp[2]:5.1f} {qp[4]:5.1f}  max {np.nanmax(P):6.1f}")
    with open(OUT / "scan_readout.txt", "w") as fh:
        fh.write("\n".join(lines) + "\n")
        if CENTRE in data:
            for t, c in data.items():
                if t == CENTRE:
                    continue
                for s, edges, key in ((3, E_EDGES, "E3r"), (4, E_EDGES, "E4r"), (3, P_EDGES, "p3"), (4, P_EDGES, "p4")):
                    a, _ = np.histogram(c[key][np.isfinite(c[key])], edges)
                    b, _ = np.histogram(data[CENTRE][key][np.isfinite(data[CENTRE][key])], edges)
                    name = f"{'E_m' if key[0] == 'E' else '|p_m|'} stage {s}"
                    hd.compare1d(a, b, edges, labels=(TUNES[t][0], TUNES[CENTRE][0]), xname=name, table=False, quiet=True, save=fh)
    print(f"\nwrote {OUT / 'scan_readout.txt'}")


if __name__ == "__main__":
    main()

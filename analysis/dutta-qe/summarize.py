"""Stage 3: strength integrals and survival table -> out/summary.md + stdout.

Per target, the windowed strengths of every ladder stage, both projections:

  E_m rows  (p_m < 300, E in [0, 80)):        I1(table), I2, I3, I4, I4/I3
  |p_m| rows (E window as the data, p < 320):  I1(table), I(data), I2-I4

All numbers on the occupancy scale (area = nucleon count), directly
comparable to the committed study numbers in results/prd-analyzer-v0.3/.

Usage:
  pixi run python analysis/dutta-qe/summarize.py
"""
import numpy as np

from config import (EM_BINW, EM_EDGES, OUT_DIR, PM_DATA_BINW, PM_EDGES,
                    PM_MAX_EM, PM_SUM, TARGETS, TUNES)
from dutta import load_em, load_folded_pm
from events import in_windows, load_cache, occ_hist, strength
from sftable import f_restricted, load_table, n_windowed, rebin


def target_tables(target):
    cfg = TARGETS[target]
    Z = cfg["Z"]
    stem, table = load_table(target)
    fE = rebin(table["E"], f_restricted(table, Z, PM_MAX_EM),
               table["dE"], EM_EDGES)
    nk = n_windowed(table, Z, cfg["e_windows_pm"])
    I1_E = fE.sum() * EM_BINW
    I1_P = strength(nk, table["k_edges"], PM_SUM)

    dem, dsf, dstat, _ = load_em(target)
    IdE = dsf.sum() * EM_BINW
    dIdE = np.sqrt((dstat ** 2).sum()) * EM_BINW
    dx, dy, _ = load_folded_pm(target)
    IdP = float((4.0 * np.pi * dx ** 2 * dy).sum() * PM_DATA_BINW)

    lines = [f"## {target}", "",
             f"- input table `{stem}`: I1(E panel, p<300) = {I1_E:.3f}, "
             f"I1(p panel, {cfg['pm_win_label']}) = {I1_P:.3f}",
             f"- data: {cfg['em_data_label']} strength = {IdE:.3f} ± {dIdE:.3f}; "
             f"{cfg['pm_data_label']} strength = {IdP:.3f} "
             f"(data/table = {IdP / I1_P:.2f})", "",
             "| tune | I2ᴱ | I3ᴱ | I4ᴱ | I4/I3 (E) | I2ᴾ | I3ᴾ | I4ᴾ | I4/I3 (p) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for tune in sorted(TUNES):
        c, n_sel = load_cache(target, tune)
        IE, IP = {}, {}
        for s in (2, 3, 4):
            winE = c[f"p{s}"] < PM_MAX_EM
            hE = occ_hist(np.where(winE, c[f"E{s}r"], np.nan),
                          EM_EDGES, n_sel, Z)
            IE[s] = hE.sum() * EM_BINW
            winP = in_windows(c[f"E{s}r"], cfg["e_windows_pm"])
            hP = occ_hist(np.where(winP, c[f"p{s}"], np.nan),
                          PM_EDGES, n_sel, Z)
            IP[s] = strength(hP, PM_EDGES, PM_SUM)
        lines.append(f"| {tune} | {IE[2]:.3f} | {IE[3]:.3f} | {IE[4]:.3f} "
                     f"| {IE[4] / max(IE[3], 1e-12):.3f} "
                     f"| {IP[2]:.3f} | {IP[3]:.3f} | {IP[4]:.3f} "
                     f"| {IP[4] / max(IP[3], 1e-12):.3f} |")
    lines.append("")
    return lines


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Dutta QE analysis — strength integrals (occupancy scale)", ""]
    for target in TARGETS:
        lines += target_tables(target)
    text = "\n".join(lines)
    (OUT_DIR / "summary.md").write_text(text + "\n")
    print(text)
    print(f"\nwrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()

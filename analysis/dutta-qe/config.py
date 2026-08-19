"""All constants of the Dutta E91-013 vs GENIE analysis in one place.

Self-contained summary project of the study written up in
results/prd-analyzer-v0.3/ (selection, windows) and
results/normalization/README.md (data conventions). Values copied from the
study scripts are marked with their provenance.
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CACHE_DIR = HERE / "cache"
OUT_DIR = HERE / "out"
DUTTA_DIR = REPO / "data/Dipingkar-dutta-data-prc_figs"
GRIDLOG_ROOT = REPO / "jobsub-agent/jobsub-runs"
V03_CACHE = REPO / "results/prd-analyzer-v0.3/cache"

# ---- selection (the study's final v0.3 form) --------------------------------
# qel && hitnuc==2212 && |Q^2/1.28 - 1| <= 5%; post-FSI proton = the unique
# proton of exactly-one-proton (N_p = 1) events.
Q2_CENTER, Q2_FRAC = 1.28, 0.05

# ---- windows ----------------------------------------------------------------
EM_EDGES = np.arange(0.0, 85.0, 5.0)     # E_m axis: [0, 80), 5-MeV data bins
EM_BINW = 5.0
PM_MAX_EM = 300.0                        # p_m window for the E_m projections
PM_EDGES = np.arange(0.0, 821.0, 20.0)   # p_m axis: native 20-MeV/c table grid
PM_BINW = 20.0
PM_PLOT = 330.0                          # plotted |p_m| range (data reach 300)
PM_SUM = 320.0                           # strength sums (aligned data grid)
PM_DATA_BINW = 40.0                      # the fig 6/7 bin width

# ---- masses -----------------------------------------------------------------
# proton mass [GeV] from the repo-shared PDG table
_nuc = json.load(open(REPO / "shared/pdg.json"))["nucleons"]
M_P = next(v["mass_gev"] for v in _nuc.values() if v["code"] == 2212)

# recoil masses [GeV] (E_m estimator: T_rec = p_m^2 / 2 M_rec)
# B11: AME2020 atomic mass 11.0093054 u - 5 m_e (results/prd-analyzer-v0/acceptance.py)
# Mn55: install genie_pdg_table.txt (results/template/make_emiss_ladder_q2cut.py)
M_REC = {"C12": 10.2525481, "Fe56": 51.1616880}

# ---- tunes (full-EM t05 grid campaigns) -------------------------------------
# tune -> (has 2D SF input table, ground-state label, QEL generator)
TUNES = {
    "GEM26_11a_05_000": (False, "LocalFGM",     "QELKinematicsGenerator"),
    "GEM26_22a_05_000": (True,  "SpectralFunc", "QELKinematicsGenerator"),
    "GEM26_22b_05_000": (True,  "SpectralFunc", "QELEventGenerator"),
    "GEM21_11a_05_000": (False, "LocalFGM",     "QELEventGeneratorSuSA"),
}

# ---- per-target configuration ----------------------------------------------
# e_windows_pm: the E_m window(s) for the |p_m| projections, matched to the
# overlaid data (Fe56: fig 7, E_m < 80; C12: the fig 6 shell windows).
# stems: grid campaign runs (Fe56 2026-07-16, C12 2026-07-26, 2M events/tune).
TARGETS = {
    "C12": dict(
        Z=6,
        e_windows_pm=[(10.0, 25.0), (30.0, 50.0)],
        pm_win_label=r"$E_m+T_{rec}$ 10–25 $\cup$ 30–50 MeV",
        sf_table="pke12_tot.data",
        run_dir="gevgen_grid-2026-07-26",
        stems={"GEM26_11a_05_000": "eminus_C12_20260726-105638",
               "GEM26_22a_05_000": "eminus_C12_20260726-105642",
               "GEM26_22b_05_000": "eminus_C12_20260726-105646",
               "GEM21_11a_05_000": "eminus_C12_20260726-105650"},
        em_data_label="Dutta Fig. 9",
        pm_data_label="Dutta Fig. 6 p+s L+R",
    ),
    "Fe56": dict(
        Z=26,
        e_windows_pm=[(0.0, 80.0)],
        pm_win_label=r"$E_m+T_{rec}$ < 80 MeV",
        sf_table="pke56_tot.data",
        run_dir="gevgen_grid-2026-07-16",
        stems={"GEM26_11a_05_000": "eminus_Fe56_20260716-113802",
               "GEM26_22a_05_000": "eminus_Fe56_20260716-141800",
               "GEM26_22b_05_000": "eminus_Fe56_20260716-141807",
               "GEM21_11a_05_000": "eminus_Fe56_20260716-113817"},
        em_data_label="Dutta Fig. 11",
        pm_data_label="Dutta Fig. 7 L+R",
    ),
}


def sf_table_path(target):
    """The SpectralFunc input table of the active GENIE installation.

    Resolved through genie-agent's installation registry (the same table
    GEM26_22a/22b read at run time via SpectralFunc.xml).
    """
    cfg = json.load(open(REPO / "genie-agent/config/genie_env.json"))
    inst = cfg["installations"][cfg["active_installation"]]
    genie = Path(inst["genie_bin_dir"]).parent
    return genie / "data/evgen/nucl/spectral_functions" / TARGETS[target]["sf_table"]

"""XRootD-streamed (e,e'p) samples for the prd-analyzer 5-model comparison.

Five quasi-elastic EM models on C12 at E_beam = 2.445 GeV, generation cut `_05`
(EM-MinQ2Limit = 1.18 GeV^2, so Q^2 >= 1.18 brackets the Q^2 = 1.28 spectrometer
setting). Each sample is ~10M events; instead of pre-pulling the grid output, we
**stream the gst files straight off dCache over XRootD** (root://).

    key             tune              config (ground state + QE-EM)        install        files
    LFG             GEM26_11a_05_000  LFG + Rosenbluth                     genie_inclxx   100 x 100k
    SF              GEM26_22a_05_000  SF  + Rosenbluth                     genie_inclxx   100 x 100k
    SuSAv2          GEM21_11a_05_000  LFG + SuSAv2 (HybridXSecAlgorithm)    genie_dev       20 x 500k
    UnifiedQEL2024  GEM26_33b_05_000  SF(ABS 2024) + UnifiedQEL            genie_inclxx   100 x 100k
    UnifiedQEL      GEM26_22b_05_000  SF  + UnifiedQEL (SF-consistent)     genie_inclxx   100 x 100k

The clean axes: LFG vs SF isolates the ground state (both Rosenbluth); LFG vs SuSAv2
isolates the QE-EM cross section (both Local Fermi Gas); SF vs UnifiedQEL isolates the
QE-EM cross-section model at fixed SF ground state (both Benhar spectral function);
UnifiedQEL vs UnifiedQEL2024 isolates the spectral function itself (old Benhar pke12_tot
vs the 2024 Ankowski-Benhar-Sakuda pke12_2024) at fixed SF-consistent cross section.

`UnifiedQEL` is "Variant 05" — the focus model (`HIGHLIGHT`), drawn on top and
emphasized in every plot.

The file *listing* is a local NFS metadata read of the /pnfs dir; the event DATA
is streamed over XRootD. dCache auth needs a valid bearer token: export
BEARER_TOKEN_FILE=<token> (refresh with `htgettoken -i dune`).

NB the SuSAv2 sample was generated with the `genie_dev` install, the two Rosenbluth
samples with `genie_inclxx` — a build difference to keep in mind for the comparison.
"""
import glob

DOOR = "fndca1.fnal.gov:1094"        # Fermilab dCache XRootD redirector
_PNFS_ROOT = "/pnfs/dune/scratch/users/liangliu/jobsub-agent/prd_paper/EM"

# key -> (legend label, color, /pnfs gevgen leaf dir with <proc>/<file>.gst.root)
SAMPLES = {
    "LFG": ("LFG + Rosenbluth", "C0",
            f"{_PNFS_ROOT}/genie_inclxx/GEM26_11a_05_000/"
            "eminus_C12_20260611-115623_gev/11_1000060120_GEM26_11a_05_000"),
    "SF": ("SF + Rosenbluth", "C1",
           f"{_PNFS_ROOT}/genie_inclxx/GEM26_22a_05_000/"
           "eminus_C12_20260611-115638_gev/11_1000060120_GEM26_22a_05_000"),
    "SuSAv2": ("LFG + SuSAv2", "C2",
               f"{_PNFS_ROOT}/genie_dev/GEM21_11a_05_000/"
               "eminus_C12_20260611-115749_gev/11_1000060120_GEM21_11a_05_000"),
    "UnifiedQEL2024": ("SF(2024) + UnifiedQEL", "C4",
                       f"{_PNFS_ROOT}/genie_inclxx/GEM26_33b_05_000/"
                       "eminus_C12_20260611-115653_gev/11_1000060120_GEM26_33b_05_000"),
    "UnifiedQEL": ("SF + UnifiedQEL", "C3",
                   f"{_PNFS_ROOT}/genie_inclxx/GEM26_22b_05_000/"
                   "eminus_C12_20260611-115708_gev/11_1000060120_GEM26_22b_05_000"),
}
# Canonical order; UnifiedQEL (Variant 05) is appended last so it is drawn on top in
# every overlay, with UnifiedQEL2024 (the new-SF sibling) right beside it. Plots
# additionally emphasize HIGHLIGHT (thicker line + high zorder).
MODELS = ["LFG", "SF", "SuSAv2", "UnifiedQEL2024", "UnifiedQEL"]
HIGHLIGHT = "UnifiedQEL"              # focus model: drawn on top, emphasized everywhere
CACHE_DIR = "results/prd-analyzer/cache"


def xrootd_url(pnfs_path, door=DOOR):
    """/pnfs/dune/...  ->  root://<door>//pnfs/fnal.gov/usr/dune/... (dCache namespace)."""
    return f"root://{door}/" + pnfs_path.replace("/pnfs/", "/pnfs/fnal.gov/usr/", 1)


def gst_urls(model, max_files=None):
    """XRootD URLs of a model's gst files: NFS-list the /pnfs dir, map each to root://."""
    files = sorted(glob.glob(SAMPLES[model][2] + "/*/*.gst.root"))
    if max_files:
        files = files[:max_files]
    return [xrootd_url(f) for f in files]


def label(model):
    return SAMPLES[model][0]


def color(model):
    return SAMPLES[model][1]


def lw(model, base=1.6, boost=1.0):
    """Line width: the HIGHLIGHT (Variant 05) gets a thicker line so it reads on top."""
    return base + boost if model == HIGHLIGHT else base


def zorder(model):
    """Draw order: the HIGHLIGHT renders above the other curves regardless of loop order."""
    return 6 if model == HIGHLIGHT else 3


def load_cache(model, cache_dir=CACHE_DIR):
    """Load the per-model cache built by build_cache.py (dict of numpy arrays)."""
    import numpy as np
    return dict(np.load(f"{cache_dir}/{model}.npz"))

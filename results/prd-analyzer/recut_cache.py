"""Derive this branch's cache/<model>.npz from the superset stage-1 caches — no streaming.

build_cache.py --superset streams each sample once with the loosest electron angular
window (theta_e +- build_cache.SUPERSET_THETA_E_HW; the El window is identical on all
branches) into cache/superset/<model>.npz. This script re-applies the CURRENT branch's
selection (selection.CUTS) to those cached columns:

  stage 1 : select_electron on the cached El/theta_e columns (a subset of the superset)
  stage 2 : select(...) recomputed from the cached has_p/Tp/theta_p columns

and writes the standard cache/<model>.npz schema the plot scripts read. Run it after
switching branches (each prd/electron/angle_cut_* branch has its own CUTS) instead of
re-streaming with build_cache.py.

    pixi run python results/prd-analyzer/recut_cache.py            # all models
    pixi run python results/prd-analyzer/recut_cache.py SF LFG     # just these
"""
import sys

sys.path.insert(0, "results/prd-analyzer")
import numpy as np
import samples as S
import selection as sel
from build_cache import SUPERSET_THETA_E_HW

ROW_KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss", "has_p", "qel"]


def recut(model):
    hw = sel.CUTS["theta_e"][1]
    if hw > SUPERSET_THETA_E_HW:
        raise SystemExit(
            f"branch theta_e half-width {hw} deg exceeds the superset's "
            f"{SUPERSET_THETA_E_HW} deg — widen SUPERSET_THETA_E_HW and rebuild "
            f"the superset caches with build_cache.py --superset")
    sup = dict(np.load(f"{S.CACHE_DIR}/superset/{model}.npz"))
    m1 = sel.select_electron(sup)
    out = {k: sup[k][m1] for k in ROW_KEYS}
    out["stage2"] = sel.select(out)
    out["ntot"] = sup["ntot"]
    path = f"{S.CACHE_DIR}/{model}.npz"
    np.savez_compressed(path, **out)
    ntot = int(out["ntot"][0])
    eff = 100.0 * len(out["El"]) / max(ntot, 1)
    print(f"[{model}] superset={len(sup['El'])} -> stage1={len(out['El'])} ({eff:.3f}%)  "
          f"stage2={int(out['stage2'].sum())}  ->  {path}", flush=True)


if __name__ == "__main__":
    models = [a for a in sys.argv[1:] if not a.startswith("-")] or S.MODELS
    for m in models:
        recut(m)

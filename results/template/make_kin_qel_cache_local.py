"""Build a kin_qel cache npz from LOCAL gst files — the local-sample twin of
make_kin_qel.py's build() (which streams grid samples over XRootD).

Written for GEM26_44b_05_000 (INCL++ GS+FSI), whose C12 t05 sample is generated
locally (EMQE-only tune — no full-EM grid campaign exists for it); works for any
tune/target. Output is byte-compatible with the campaign caches:

    results/prd-analyzer-v0.1/cache/kin_qel_<target>/<tune>.npz
    (KEYS qel-selected + has_p + ntot)

so the q2cut/empm plotting scripts pick it up once the tune is in their TUNES.
NB for counts panels: campaign caches carry ntot = 2M full-EM events/tune; a
local EMQE-only sample's ntot is not comparable — use the shape (density) panels.

Usage:
  pixi run python results/template/make_kin_qel_cache_local.py \
      --target C12 --tune GEM26_44b_05_000 <gst1.root> [gst2.root ...]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "results/prd-analyzer-v0")
from selection import load_events

REPO = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPO / "results/prd-analyzer-v0.1/cache"
KEYS = ["El", "theta_e", "Tp", "theta_p", "Q2", "E_miss", "p_miss", "n_p"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--tune", required=True)
    ap.add_argument("gst", nargs="+", help="local gst.root file(s)")
    args = ap.parse_args()

    parts, ntot = [], 0
    for path in args.gst:
        ev = load_events(path)
        m = ev["qel"].astype(bool)
        part = {k: ev[k][m] for k in KEYS}
        part["has_p"] = ev["has_p"][m]
        parts.append(part)
        ntot += len(ev["Q2"])
        print(f"{path}: {len(ev['Q2'])} events, {m.sum()} qel", flush=True)

    out = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    out["ntot"] = np.array([ntot])
    cache_dir = CACHE_ROOT / f"kin_qel_{args.target.lower()}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{args.tune}.npz"
    np.savez_compressed(path, **out)
    print(f"[{args.tune}] ntot={ntot}  selected(qel)={len(out['Q2'])} "
          f"({100.0 * len(out['Q2']) / max(ntot, 1):.2f}%)  ->  {path}")

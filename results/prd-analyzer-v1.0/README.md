[← Results home](../README.md)

# prd-analyzer v1.0 — full generated phase space (no Q² slice)

The [`../prd-analyzer-v0.3/`](../prd-analyzer-v0.3/README.md) analysis with
the Dutta Q² = 1.28 ± 5 % slice **dropped**: selection reduced to

    qel  &&  N_p(final state) = 1   (proton-side views)

on the same full-EM t05 campaigns (2M streamed events/tune). The t05
generation cut EM-MinQ2Limit = 1.18 GeV² remains the hard lower Q² edge of
the samples.

The notes:

- [`electron_c12_scattering.md`](electron_c12_scattering.md)
- [`electron_c12_scattering_genie_incl.md`](electron_c12_scattering_genie_incl.md) — the C12 note repeated for the INCL++ GS+FSI tune `GEM26_44b_05_000` (local 500k EMQE-only sample of 2026-09-01, overlaid on 22b)
- [`electron_fe56_scattering.md`](electron_fe56_scattering.md)

Machinery: [`make_kin_qel_v1.py`](../template/make_kin_qel_v1.py) (reads the
v0.1 kin_qel caches, no Q² mask, N_p = 1 on the proton panels), plus the
v0.2/v0.3 ladder scripts with the new `--no-q2cut` flag
(`make_emiss_ladder_q2cut.py`, `make_pmiss_ladder_q2cut.py` — stream/read
the uncut caches in `cache/ladder_<target>/` here; the INCL tune reads its
local gst chunks via `TGT["C12"]["local_gst"]`, its kinematics cache comes
from `make_kin_qel_cache_local.py`, and `--tunes/--tag` / `--grid-tunes/--tag`
select the overlay set and output stem). All outputs land here.

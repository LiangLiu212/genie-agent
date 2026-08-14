[← Results home](../README.md)

# prd-analyzer v1.0 — full generated phase space (no Q² slice)

The [`../prd-analyzer-v0.3/`](../prd-analyzer-v0.3/README.md) analysis with
the Dutta Q² = 1.28 ± 5 % slice **dropped**: selection reduced to

    qel  &&  N_p(final state) = 1   (proton-side views)

on the same full-EM t05 campaigns (2M streamed events/tune). The t05
generation cut EM-MinQ2Limit = 1.18 GeV² remains the hard lower Q² edge of
the samples. C12 focus.

The notes:

- [`electron_c12_scattering.md`](electron_c12_scattering.md)

Machinery: [`make_kin_qel_v1.py`](../template/make_kin_qel_v1.py) (reads the
v0.1 kin_qel caches, no Q² mask, N_p = 1 on the proton panels), plus the
v0.2/v0.3 ladder scripts with the new `--no-q2cut` flag
(`make_emiss_ladder_q2cut.py`, `make_pmiss_ladder_q2cut.py` — stream/read
the uncut caches in `cache/ladder_<target>/` here). All outputs land here.

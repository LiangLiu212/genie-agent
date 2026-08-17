# GEM21_11a — stock SuSAv2 EM tune (overlay copy)

Copy of the official GEM21_11a family (SuSAv2 QE via `genie::HybridXSecAlgorithm/SuSAv2-QEL`
with the `genie::QELEventGeneratorSuSA` chain), tracked here so PP override subdirs can be
added without touching `$GENIE/config`. Run with `--gxmlpath genie-agent/tunes`.

## EM-MinQ2Limit overrides (PP subdirs)

`_01..._03` = 0.02 / 0.20 / 0.50 GeV² (early cut scan);
`_04..._08` = 0.54 / 1.18 / 1.70 / 1.73 / 3.15 GeV² (spline-ladder campaign);
`_09_000` = **0.25 GeV²** (2026-08-17, inclusive (e,e′) comparison vs the QES-archive
12C 2.5 GeV/15° and 56Fe 2.7 GeV/15° settings — both sit entirely above 0.25).
Each subdir is a full CommonParam.xml copy differing only in that one value.

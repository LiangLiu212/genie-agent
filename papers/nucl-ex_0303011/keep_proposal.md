# Figure keep/drop proposal — nucl-ex/0303011

(e,e'p) quasi-elastic paper. Per the keep rubric, missing-energy / missing-momentum / spectral-function plots are usually *the* result and are kept; model-comparison plots from the discussion are dropped; raw selected-sample data/MC comparisons are kept.

20 figures total. Proposed: 14 keep, 4 drop, 2 flag.

- [#1] `fig1` — files: `fig1.ps` — **keep** — SIMC vs measured e-p elastic distributions (momentum, angle, out-of-plane, target length); validates the acceptance model / cut chain.
- [#2] `fig:radtest` (fig2) — files: `fig2.eps` — **keep** — hydrogen missing-energy data vs SIMC; demonstrates radiative-correction handling and is the system-response/calibration reference.
- [#3] `fig:carbonem` (fig3) — files: `fig3.eps` — **keep** — raw carbon missing-energy spectra; primary measured (e,e'p) observable.
- [#4] `fig:ironem` (fig4) — files: `fig4.eps` — **keep** — raw iron missing-energy spectra; primary measured observable.
- [#5] `fig:goldem` (fig5) — files: `fig5.eps` — **keep** — raw gold missing-energy spectra; primary measured observable.
- [#6] `fig:carbonpm` (fig6) — files: `fig6.eps` — **keep** — carbon missing-momentum (p/s-shell) distributions; headline spectral-function result.
- [#7] `fig:ironpm` (fig7) — files: `fig7.eps` — **keep** — iron missing-momentum distributions; headline spectral-function result.
- [#8] `fig:goldpm` (fig8) — files: `fig8.eps` — **keep** — gold missing-momentum distributions; headline spectral-function result.
- [#9] `fig:carbonsem` (fig9) — files: `fig9.eps` — **flag** — carbon missing-energy spectral function vs IPSM only; is the measured spectral function (keep-worthy as an (e,e'p) result) but the panel is purely a single-model comparison — human decides whether redundant with #3/#6.
- [#10] `fig:carbonspm` (fig10) — files: `fig10.eps` — **drop** — carbon momentum distribution compared to multiple model curves (IPSM, IPSM+mixing, DWIA Zhalov ± color transparency); discussion-section model comparison, absolute measurement already in #6.
- [#11] `fig:ironsem` (fig11) — files: `fig11.eps` — **drop** — iron missing-energy spectral function vs IPSM/Benhar/TIMORA; multi-model discussion comparison, raw spectrum in #4.
- [#12] `fig:ironspm` (fig12) — files: `fig12.eps` — **drop** — iron momentum distribution vs multiple models (IPSM, Zhalov ±CT, Benhar, TIMORA); discussion model comparison, measurement in #7.
- [#13] `fig:goldsem` (fig13) — files: `fig13.eps` — **flag** — gold missing-energy spectral function vs IPSM only; same ambiguity as #9 (measured spectral function vs single-model comparison).
- [#14] `fig:goldspm` (fig14) — files: `fig14.eps` — **drop** — gold momentum distribution vs IPSM/Benhar; discussion model comparison, measurement in #8.
- [#15] `fig:cral` (fig15) — files: `fig15.ps` — **keep** — normalized transparency vs angle relative to conjugate angle for C/Fe/Au; primary measured asymmetry result.
- [#16] `fig:transp` (fig16) — files: `fig16.eps` — **keep** — transparency vs Q² for all three nuclei with prior data; the headline transparency result.
- [#17] `fig:feslst` (fig17) — files: `fig17.eps` — **keep** — iron separated L/T spectral functions; headline L-T result (first for medium nuclei).
- [#18] `fig:auslst` (fig18) — files: `fig18.eps` — **keep** — gold separated L/T spectral functions at Q²=0.64; headline L-T result (first for heavy nuclei).
- [#19] `fig:caslst` (fig19) — files: `fig19.eps` — **keep** — carbon L/T spectral functions at Q²=0.64 comparing Rosenbluth vs polarization-transfer form factors; headline form-factor-dependence result (small effect demonstrated).
- [#20] `fig:ccslst` (fig20) — files: `fig20.eps` — **keep** — carbon L/T spectral functions at Q²=1.8 comparing form-factor choices; headline result showing the 60% longitudinal-strength change (text emphasizes this as a key finding).

# Keep proposal — arXiv 2503.15047 (MINERvA CCQE-like A-dependence TKI)

This paper has 13 measured variables, each with a near-identical figure set:
an absolute cross section per target (`xsec_five_square/*`, the headline), an
absolute-uncertainty + ratio-uncertainty summary (`xsec_errors_all5/*` +
`xsec_ratio_errors/*`), a multi-generator absolute comparison (`gencompare/*_5square`),
a multi-generator ratio-to-CH comparison (`gencompare/*_4square`), and a
ratio-to-MINERvA-tune comparison (`gencompare_ratio/mnvratio_*`). Generator-comparison
and ratio-to-tune plots are dropped per the rubric (discussion/model-comparison),
keeping the absolute measurements.

PNG renders use the source path flattened with `__` (e.g.
`figures/xsec_five_square__dpt_fine.png`).

## Body figures

- [#1] `fig:TKI` — files: `TKI_var.eps` — **keep** — schematic defining the TKI variables; needed to interpret every result.
- [#2] `fig:tkidelta_evntrate_sig` — files: `Event_rate_plots/event_rate_tki_dpt_fine_{tracker,water,iron,lead}.eps` — **keep** — selected-sample data/MC event rates, demonstrates the cut chain.
- [#3] `fig:tkidelta_sdbn_evntrate_untuned` — files: `Sidebands/Sidebands_dpt/Before/{ch,lead}_sideband_{michel,energy_clusters}_v5_before.eps` — **keep** — sideband samples used to constrain backgrounds (Michel/π⁰ sidebands).
- [#4] `fig:dpt_xsec` — files: `xsec_five_square/dpt_fine.eps` — **keep** — primary δP_T differential cross section per target, headline result.
- [#5] `figure:xsec_dpt_uncert` — files: `xsec_errors_all5/errors_dpt_fine.eps` — **keep** — uncertainty breakdown for the absolute δP_T cross section (the worked-example variable).
- [#6] `fig:xsec_dpt_uncert_rat` — files: `xsec_ratio_errors/ratio_errors_dpt_fine.eps` — **keep** — uncertainty breakdown for the δP_T ratio to CH (worked example).
- [#7] `Figure:Gencompare_dpt` — files: `gencompare/dpt_fine_5square.eps` — **drop** — multi-generator model comparison of the δP_T absolute cross section.
- [#8] `Figure:Gencompare_dpt_ratio` — files: `gencompare/dpt_fine_4square.eps` — **drop** — multi-generator comparison of the δP_T ratio to CH.

## §V "other observables" — absolute cross sections (KEEP, headline results)

- [#9] `figure:xsec_coplan` — `xsec_five_square/phi.eps` — **keep** — φ_T (acoplanarity) absolute cross section per target.
- [#10] `figure:xsec_alph` — `xsec_five_square/alpha.eps` — **keep** — δα_T absolute cross section per target.
- [#11] `figure:xsec_dptx` — `xsec_five_square/dptx.eps` — **keep** — δP_{Tx} absolute cross section per target.
- [#12] `figure:xsec_dpty` — `xsec_five_square/dpty.eps` — **keep** — δP_{Ty} absolute cross section per target.
- [#13] `figure:xsec_pl` — `xsec_five_square/pl.eps` — **keep** — δP_L absolute cross section per target.
- [#14] `figure:xsec_pn` — `xsec_five_square/pn.eps` — **keep** — P_n (struck-neutron momentum) absolute cross section per target.
- [#15] `figure:xsec_proton_p` — `xsec_five_square/proton_p.eps` — **keep** — proton momentum absolute cross section per target.
- [#16] `figure:xsec_proton_pt` — `xsec_five_square/proton_pt.eps` — **keep** — proton transverse-momentum absolute cross section per target.
- [#17] `figure:xsec_proton_theta` — `xsec_five_square/proton_theta.eps` — **keep** — proton angle absolute cross section per target.
- [#18] `figure:xsec_muon_p` — `xsec_five_square/muon_p.eps` — **keep** — muon momentum absolute cross section per target.
- [#19] `fig:ptmu_xsec` — `xsec_five_square/muon_pt.eps` — **keep** — muon transverse-momentum absolute cross section per target.
- [#20] `figure:xsec_muon_theta` — `xsec_five_square/muon_theta.eps` — **keep** — muon angle absolute cross section per target.

## §V — multi-generator absolute comparisons (DROP, model comparison)

- [#21] `fig:models_coplan` — `gencompare/phi_5square.eps` — **drop** — generator comparison of φ_T cross section.
- [#22] `fig:models_alphat` — `gencompare/alpha_5square.eps` — **drop** — generator comparison of δα_T cross section.
- [#23] `fig:models_dptx` — `gencompare/dptx_5square.eps` — **drop** — generator comparison of δP_{Tx} cross section.
- [#24] `fig:ratiomodels_dpty` — `gencompare/dpty_5square.eps` — **drop** — generator comparison of δP_{Ty} cross section (label swapped with ratio in source — see open_questions).
- [#25] `fig:models_pl` — `gencompare/pl_5square.eps` — **drop** — generator comparison of δP_L cross section.
- [#26] `fig:models_pn` — `gencompare/pn_5square.eps` — **drop** — generator comparison of P_n cross section.
- [#27] `fig:models_proton_p` — `gencompare/proton_p_5square.eps` — **drop** — generator comparison of proton-p cross section.
- [#28] `fig:models_proton_pt` — `gencompare/proton_pt_5square.eps` — **drop** — generator comparison of proton-p_T cross section.
- [#29] `fig:models_proton_theta` — `gencompare/proton_theta_5square.eps` — **drop** — generator comparison of proton-θ cross section.
- [#30] `fig:models_muon_p` — `gencompare/muon_p_5square.eps` — **drop** — generator comparison of muon-p cross section.
- [#31] (muon_pt comparison) — `gencompare/muon_pt_5square.eps` — **drop** — generator comparison of muon-p_T cross section.
- [#32] `fig:models_muon_theta` — `gencompare/muon_theta_5square.eps` — **drop** — generator comparison of muon-θ cross section.

## §V — multi-generator ratio-to-CH comparisons (DROP, model comparison)

- [#33] `Figure:Gencompare_phi_ratio` — `gencompare/phi_4square.eps` — **drop** — generator comparison of φ_T ratio to CH.
- [#34] `Figure:Gencompare_alpha_ratio` — `gencompare/alpha_4square.eps` — **drop** — generator comparison of δα_T ratio to CH.
- [#35] `Fig:ratios_dptx` — `gencompare/dptx_4square.eps` — **drop** — generator comparison of δP_{Tx} ratio to CH.
- [#36] `fig:models_dpty` — `gencompare/dpty_4square.eps` — **drop** — generator comparison of δP_{Ty} ratio to CH (label swapped — see open_questions).
- [#37] `Figure:Gencompare_pl_ratio` — `gencompare/pl_4square.eps` — **drop** — generator comparison of δP_L ratio to CH.
- [#38] `Figure:Gencompare_pn_ratio` — `gencompare/pn_4square.eps` — **drop** — generator comparison of P_n ratio to CH.
- [#39] `fig:models_proton_p` (ratio) — `gencompare/proton_p_4square.eps` — **drop** — generator comparison of proton-p ratio to CH.
- [#40] (proton_pt ratio) — `gencompare/proton_pt_4square.eps` — **drop** — generator comparison of proton-p_T ratio to CH.
- [#41] (proton_theta ratio) — `gencompare/proton_theta_4square.eps` — **drop** — generator comparison of proton-θ ratio to CH.
- [#42] (muon_p ratio) — `gencompare/muon_p_4square.eps` — **drop** — generator comparison of muon-p ratio to CH.
- [#43] (muon_pt ratio) — `gencompare/muon_pt_4square.eps` — **drop** — generator comparison of muon-p_T ratio to CH.
- [#44] (muon_theta ratio) — `gencompare/muon_theta_4square.eps` — **drop** — generator comparison of muon-θ ratio to CH.

## §V — uncertainty breakdowns for the other variables

Absolute-cross-section uncertainty summaries — **keep** (one per variable, these are the uncertainty composition for each headline result):

- [#45] `fig:xsec_err_coplan` (abs part) — `xsec_errors_all5/errors_phi.eps` — **keep**
- [#46] `fig:xsec_err_alpha` (abs) — `xsec_errors_all5/errors_alpha.eps` — **keep**
- [#47] `fig:xsec_err_dptx` (abs) — `xsec_errors_all5/errors_dptx.eps` — **keep**
- [#48] `fig:xsec_err_dpty` (abs) — `xsec_errors_all5/errors_dpty.eps` — **keep**
- [#49] `fig:xsec_err_pl` (abs) — `xsec_errors_all5/errors_pl.eps` — **keep**
- [#50] `fig:xsec_err_pn` (abs) — `xsec_errors_all5/errors_pn.eps` — **keep**
- [#51] `fig:xsec_err_muon_p` (abs) — `xsec_errors_all5/errors_muon_p.eps` — **keep**
- [#52] `fig:xsec_err_muon_pt` (abs) — `xsec_errors_all5/errors_muon_pt.eps` — **keep**
- [#53] `fig:xsec_err_muon_theta` (abs) — `xsec_errors_all5/errors_muon_theta.eps` — **keep**
- [#54] `fig:xsec_err_proton_p` (abs) — `xsec_errors_all5/errors_proton_p.eps` — **keep**
- [#55] `fig:xsec_err_proton_pt` (abs) — `xsec_errors_all5/errors_proton_pt.eps` — **keep**
- [#56] `fig:xsec_err_proton_theta` (abs) — `xsec_errors_all5/errors_proton_theta.eps` — **keep**

Ratio-to-CH uncertainty summaries — **flag** (the rubric drops 1D uncertainty plots when a 2D summary exists, but here the ratio uncertainties are a distinct measurement, not a redundant projection; recommend keeping one representative, e.g. dpt, and dropping the rest — needs human decision):

- [#57] `xsec_ratio_errors/ratio_errors_phi.eps` — **flag** — ratio-to-CH uncertainty breakdown; keep or drop alongside absolute?
- [#58] `xsec_ratio_errors/ratio_errors_alpha.eps` — **flag** — same question.
- [#59] `xsec_ratio_errors/ratio_errors_dptx.eps` — **flag** — same question.
- [#60] `xsec_ratio_errors/ratio_errors_dpty.eps` — **flag** — same question.
- [#61] `xsec_ratio_errors/ratio_errors_pl.eps` — **flag** — same question.
- [#62] `xsec_ratio_errors/ratio_errors_pn.eps` — **flag** — same question.
- [#63] `xsec_ratio_errors/ratio_errors_muon_p.eps` — **flag** — same question.
- [#64] `xsec_ratio_errors/ratio_errors_muon_pt.eps` — **flag** — same question.
- [#65] `xsec_ratio_errors/ratio_errors_muon_theta.eps` — **flag** — same question.
- [#66] `xsec_ratio_errors/ratio_errors_proton_p.eps` — **flag** — same question.
- [#67] `xsec_ratio_errors/ratio_errors_proton_pt.eps` — **flag** — same question.
- [#68] `xsec_ratio_errors/ratio_errors_proton_theta.eps` — **flag** — same question.

## Ratio-to-MINERvA-tune comparisons (Supplement, DROP — ratio-to-collaboration-tune)

- [#69] `fig:models_dpt_rat` — `gencompare_ratio/mnvratio_dpt_fine.eps` — **drop** — ratio of data/models to the MINERvA tune (δP_T).
- [#70] `fig:models_coplan_rat` — `gencompare_ratio/mnvratio_phi.eps` — **drop** — ratio to MINERvA tune (φ_T).
- [#71] `fig:models_alphat_rat` — `gencompare_ratio/mnvratio_alpha.eps` — **drop** — ratio to MINERvA tune (δα_T).
- [#72] `fig:models_dptx_rat` — `gencompare_ratio/mnvratio_dptx.eps` — **drop** — ratio to MINERvA tune (δP_{Tx}).
- [#73] `fig:models_dpty_rat` — `gencompare_ratio/mnvratio_dpty.eps` — **drop** — ratio to MINERvA tune (δP_{Ty}).
- [#74] `fig:models_pl_rat` — `gencompare_ratio/mnvratio_pl.eps` — **drop** — ratio to MINERvA tune (δP_L).
- [#75] `fig:models_pn_rat` — `gencompare_ratio/mnvratio_pn.eps` — **drop** — ratio to MINERvA tune (P_n).
- [#76] `fig:models_muon_p_rat` — `gencompare_ratio/mnvratio_muon_p.eps` — **drop** — ratio to MINERvA tune (p_μ).
- [#77] (muon_pt rat) — `gencompare_ratio/mnvratio_muon_pt.eps` — **drop** — ratio to MINERvA tune (p_{μT}).
- [#78] `fig:models_muon_theta_rat` — `gencompare_ratio/mnvratio_muon_theta.eps` — **drop** — ratio to MINERvA tune (θ_μ).
- [#79] `fig:models_proton_p_rat` — `gencompare_ratio/mnvratio_proton_p.eps` — **drop** — ratio to MINERvA tune (p_p).
- [#80] `fig:models_proton_pt_rat` — `gencompare_ratio/mnvratio_proton_pt.eps` — **drop** — ratio to MINERvA tune (p_{pT}).
- [#81] `fig:models_proton_theta_rat` — `gencompare_ratio/mnvratio_proton_theta.eps` — **drop** — ratio to MINERvA tune (θ_p).

## Supplement — analysis-chain figures (KEEP, demonstrate the extraction)

- [#82] `fig:tkidelta_sdbn_evntrate_tuned` — `Sidebands/After/{ch,lead}_sideband_{michel,energy_clusters}_v5.eps` — **keep** — sidebands after background tuning.
- [#83] `fig:tkidelta_evntrate_tuned` — `Supp_Events/{ch,h2o,iron,lead}_signal_after.eps` — **keep** — signal region after tuning, before subtraction.
- [#84] `fig:tkidelta_evntrate_backgroundsubtr` — `Supp_Events/background_subtracted_tki_dpt_fine_{tracker,water,iron,lead}.eps` — **keep** — background-subtracted signal.
- [#85] `fig:tkidelta_evntrate_unfolded` — `Supp_Events/unfolded_tki_dpt_fine_{tracker,water,iron,lead}.eps` — **keep** — unfolded event rates.
- [#86] `fig:tkidelta_efficiency` — `Event_rate_plots/TKIdelta/reco_eff/{tracker,lead}_v5.eps` — **keep** — selection efficiency vs δP_T (CH, Pb).
- [#87] `fig:fluxes` — `fluxes.eps` — **keep** — per-target flux ratio to scintillator (flux prediction).

## Summary

- Total figure environments: 87 (106 individual EPS panels rendered to PNG).
- Keep: 39 (incl. 12 ratio-uncertainty plots flagged below as borderline).
- Drop: 36 (model/generator comparisons + ratio-to-tune).
- Flag: 12 (ratio-to-CH uncertainty breakdowns #57–#68).

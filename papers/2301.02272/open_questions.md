# Open questions — arXiv 2301.02272

1. **No ancillary data released.** The arXiv source tarball contains no `anc/` directory and no `README`. The numerical cross sections / ratios (which other MINERvA papers typically release as data tables) are not in the source. Confirm whether numerical data exist elsewhere (HEPData / journal supplement) before relying on figure values.

2. **Bin edges not tabulated.** The double-differential measurement is in (P_T, P_∥) but the source gives no explicit P_T/P_∥ bin-edge tables. Only two values are stated in prose: the peak P_∥ bin is 4.5–5.5 GeV/c, and populated P_∥ spans 3.75–6.5 GeV/c. Full bin edges would need to be read off the figures or obtained from the collaboration.

3. **N_nucleons / fiducial target masses not stated** numerically in the source, though the cross section is explicitly normalized "by the number of target nucleons." These per-target nucleon counts are not in the text.

4. **No journal DOI in source.** The tex carries `\date{\today}` and no journal reference/DOI; this is the as-submitted preprint. Header DOI left as "(not stated)".

5. **Unfolding regularization unspecified.** D'Agostini iterative unfolding is named but the number of iterations and how it was chosen are not given in the paper text.

6. **M_A not stated.** The QE axial mass used in the GENIE 2.12.6 / MnvGENIEv1 tune is not quoted explicitly.

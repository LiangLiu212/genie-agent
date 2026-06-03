# Open questions — arXiv 2503.15047

1. **No journal DOI / reference in the source.** The tex compiles as a PRD
   manuscript (`revtex4-2`, `prd` option) but no `\doi`, journal volume, or
   published reference appears in `NuclTargTKI_PRD.tex` or `00README.json`.
   The header in `paper_2503.15047.md` marks the DOI as not stated. A human
   should fill in the published PRD reference if/when available.

2. **No `anc/README`.** The ancillary directory (`anc/`) has 420 `.txt` data
   files plus two ROOT files (`tki_release.root`, `tki_release_mnv.root`) but no
   README describing the file/column semantics or a contact author. Column
   meaning was inferred from the per-file header comments (X / Content / Error).
   The contact author is assumed to be the lead author (J. Kleykamp) but is not
   stated in `anc/`.

3. **Explicit bin edges not in the paper.** No binning tables are given in the
   tex; bin centers/edges live only in the ancillary `.txt` files. §6 of the
   summary reports the released δP_T (lead) bin centers as a representative
   example. If the wiki needs full bin-edge tables, they must be parsed from
   `anc/`.

4. **Signal vs reconstruction phase space mismatch (commented note).** A
   commented-out author note (line ~314 of `NuclTargTKI_PRD.tex`) states the
   reconstruction uses a wider proton fiducial (proton < 90°, 400 < p_p/MeV <
   1300) than the signal definition (proton < 70°, 500 < p_p/MeV < 1100) to
   avoid cutting on the efficiency edge. This is not in the published body text;
   confirm whether it should be reflected in the event-selection description.

5. **Table I header value Z=7, N=6 for "Tracker (CH)".** The statistics table
   lists Z=7, N=6 for the CH/tracker row, which is an effective scintillator
   value rather than pure carbon (Z=6). Reproduced verbatim; flag in case it is
   a typo in the source.

6. **Swapped 5square/4square labels for δP_{Ty}.** In `Result_dpty.tex` the
   absolute-comparison figure (`fig:models_dpty`) points to
   `gencompare/dpty_4square.eps` and the ratio figure (`fig:ratiomodels_dpty`)
   points to `gencompare/dpty_5square.eps` — the opposite convention from every
   other variable (5square = absolute, 4square = ratio). Likely a label/file
   swap in the source; the keep_proposal follows the file naming convention
   (5square = absolute comparison). Confirm intended mapping.

7. **Ratio-to-CH uncertainty plots (#57–#68) flagged.** These are distinct
   ratio-measurement uncertainty breakdowns, not redundant 1D projections of a
   2D summary, so the default "drop redundant 1D uncertainty" rule does not
   cleanly apply. Recommend keeping one representative (δP_T) and dropping the
   rest, but this is a physics/presentation judgment left to the human.

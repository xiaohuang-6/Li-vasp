# Second resubmission: COMMAT-D-26-03061R1

The editor's decision is dated 12 September 2026; the new deadline is
12 October 2026. The author reports that Reviewer 2 is satisfied. Reviewer 3's
5 September report identifies four outstanding presentation problems.
The decision and report were read from the two author-supplied attachments
under `8b8de223-8d9a-4591-9301-6bc36a381e0b` before editing.

## Revision scope

- The marked manuscript compares against R1 source commit
  `c3004e56d13996bebdbd74953c3d23a46f141665`, including its Results input.
  Blue is added text, red strikeout is deleted text, and black is unchanged text.
  A first-page legend states the convention and explains the different pagination.
- All response references use the clean PDF. LaTeX line labels supply the
  printed line/page pairs; the response is regenerated after manuscript changes.
- All four R1 SI figures and all eight R1 SI tables are included in the main
  manuscript. The `evidence_*.tex` files preserve their data. There is no separate
  R2 SI PDF. Supplementary Data still contains configurations, models, and code.
- The Abstract, Introduction, Results and Discussion, and Conclusion were edited
  for direct scientific prose, guided by <https://github.com/blader/humanizer>.
  Repeated significance statements and misleading comparisons were removed.
- The unchanged adsorption equation and explicit Li-group-relative displacement
  equation use LaTeX math. Figure colors retain scientific meanings in both PDFs.
- The equal-contribution text on the first page and the requested generative-AI
  declaration are retained. The numerical tables and model checkpoints are unchanged.
- No new scientific calculations or cluster GPU tasks were run for this revision.

Two factual clarifications accompany the language edits: 113 is not more than
ten times 20.1, and only nine of the sixteen DFT snapshots enter the reported
force comparison. Neither correction changes the underlying results.

## Build and verify

With Tectonic and latexdiff installed:

```bash
python review_revision/build_revision2.py
python review_revision/write_revision2_response.py
python review_revision/static_check_manuscript.py --submission-ready
python review_revision/verify_resubmission_science.py
python review_revision/check_revision2_pdfs.py
```

The PDF checker requires PyMuPDF and Pillow. It renders every page under
`tmp/pdfs/revision2/`, checks PDF characters, embedded font programs or glyph
streams, page bounds, red strikeout geometry, response line labels, all migrated
tables, and the flat editable source ZIP. Review the rendered pages in addition
to running the checks.

After committing the verified source:

```bash
python review_revision/build_reproducibility_archive.py --output resubmission/R2_Reproducibility.zip
python review_revision/build_resubmission_package.py --reproducibility-archive resubmission/R2_Reproducibility.zip
```

The transfer directory is `resubmission/COMMAT_R2_20260913/`. The four-file
ZIP is a download convenience; extract it and assign its four files to the
portal's separate item types. Only `Revised_Manuscript_Editable_Source.zip`
should be processed as the manuscript LaTeX ZIP. It has no subfolders.

The package includes a paste-ready TXT response. The PDF response is for review
or for a separate response upload if the portal offers one.

## Initial R2 verified outcome

| Requirement | Evidence |
| --- | --- |
| Reviewable revision | Standard latexdiff against the pinned R1; marked PDF has a first-page legend, blue additions, red strikeout deletions, and black unchanged text. |
| Accurate response locations | All 20 line-label endpoints resolve to actual printed numbers in the clean PDF; response text is generated from the final auxiliary file. |
| Correct rendering | All 20 clean pages, 24 marked pages, and 2 response pages were rendered and visually inspected. No missing-glyph placeholders, unresolved references, or overfull boxes were found. Fonts or Type 3 glyph streams are embedded. |
| Main-text figures and tables | All 12 former SI floats occur exactly once in the main TeX, with text references; all 8 numerical tables preserve the R1 data. The manuscript contains 6 figures and 8 tables. |
| Narrative and language | The 232-word Abstract and revised narrative connect dataset coverage, adsorption, path sampling, and environment-resolved force tests; the original scientific limits remain explicit. |
| Editable source | The 8-member source ZIP has no subfolders and was compiled after extraction. Its 20-page PDF matches the clean manuscript text page by page. |
| Scientific integrity | 151 manuscript/evidence checks and the 55-file curated-data integrity check pass. Dataset, numerical evidence, and checkpoint hashes are unchanged; only two data-package README hashes changed. |

These checks establish artifact consistency and reviewability, not a guarantee
of editorial acceptance. The authors should review the supplied clean and marked
copies before uploading them.

## Language and typography update, 13 September 2026

The author's Gemini review and subsequent instructions guide the v2 prose edit.
The revision removes repeated exclusion lists, organizes the split description
by evaluation purpose, and replaces the standalone limitations subsection with
`Implications for potential development`. The Abstract and Conclusion focus on
adsorption trends, family-resolved fine-tuning gains, and configuration-specific
training targets. The reported measurements and their definitions are retained.

Negative energies now use mathematical minus signs. Force and squared-length
units use siunitx, and supercell and k-mesh dimensions use complete math
expressions. Figure 4 has panel letters (a)-(e); Figure 6 uses the Si4 subscript
in its legends. Site/path raster companions are exported at 300 dpi; the
manuscript uses their vector PDFs. Internal si_ anchors remain stable for
provenance and do not appear in the typeset article.

The new output directory is `resubmission/COMMAT_R2_20260913_v2/`, with
20 clean pages, 25 marked pages, and a 2-page response. The marked comparison
still uses the submitted R1 baseline, not the intermediate R2 draft. Response
locations are regenerated from the final clean PDF. Numerical checks accept
equivalent TeX formatting while continuing to compare all reported values
against the original evidence. No scientific dataset or model was changed.

# Computational Materials Science Submission Checklist

Date checked: 2026-07-26

## Candidate Target

`Computational Materials Science` is the current best-fit 3+ impact-factor
candidate for the evidence-bounded version of this work.

- Publisher-reported 2025 metrics: Impact Factor 3.3; CiteScore 6.6.
- Indexing listed by the publisher: Science Citation Index Expanded.
- Scope fit: computational methods, two-dimensional materials,
  machine-learning-enhanced simulation, method validation, and reproducible
  data-driven workflows.
- Primary scope risk: the journal requires high novelty in application and
  interpretation, validation/transferability of non-first-principles methods,
  and FAIR-compatible data and code.

Authoritative pages:

- https://www.sciencedirect.com/journal/computational-materials-science
- https://www.sciencedirect.com/journal/computational-materials-science/publish/guide-for-authors

Acceptance cannot be guaranteed. The target is credible only if the submission
is positioned as a validation-first computational workflow, not as a completed
Li-diffusion or practical battery-anode study.

## Submission Artifacts

- [x] Manuscript title restores explicit machine-learning scope while retaining
  the validation-first DFT--MACE framing.
- [x] The abstract expands Message Passing Atomic Cluster Expansion (MACE) on
  the first manuscript page.
- [x] Abstract is below the journal's 250-word limit.
- [x] Seven English keywords are present.
- [x] Five highlights are present and each is at most 85 characters:
  `manuscript/highlights.txt`.
- [x] A data-derived, non-generative-AI graphical abstract is present at
  `manuscript/graphical_abstract.png` (3600 x 1440, 2.5:1, 300 dpi), with a
  separate caption and unambiguous force units in meV per angstrom.
- [x] Both MACE diagnostic panels use publication-facing family labels; the
  force panel displays meV per inverse angstrom and states that the original
  same-workflow split is not a transferability test. Both panels regenerate
  deterministically from the tracked curated MACE summary.
- [x] The manuscript includes the required declaration of generative-AI use in
  manuscript preparation.
- [x] Affiliations use lower-case superscript letters and full postal addresses
  as requested by the current Guide for Authors.
- [x] Author contributions use full author names, the Credit heading, and the
  Credit taxonomy.
- [x] The manuscript uses Elsevier's standard author-responsibility and
  no-known-competing-interest wording under the official `Declaration of
  competing interests` heading.
- [x] Accepted VASP/MACE/LAMMPS versions, model-training settings, and MD
  thermostat/equilibration/MSD details are documented and evidence-checked.
- [x] A 3.23 MB curated submission-data package contains both extxyz split
  definitions, numerical evidence tables, sanitized paths, and SHA256 hashes.
- [x] A concise initial-submission cover letter is present at
  `manuscript/cover_letter_computational_materials_science.txt`; it explicitly
  distinguishes the work from a conventional MD average-property study.
- [x] The release archive exports only the active manuscript source and active
  figures; superseded backups, administrative drafts, internal handoffs, and
  local GPU packs are not published as journal supplementary material.
- [x] Reserved Zenodo DOI `10.5281/zenodo.21609229` is cited and linked in the
  Data and Code Availability section.
- [x] Curated data are declared CC BY 4.0 and workflow code MIT.
- [x] The GitHub link is retained in the manuscript and archive metadata.
- [x] The cover-letter `DRAFT` banner is removed and the DOI route is stated.
- [ ] Publish the Zenodo record before pressing `Submit` so the DOI resolves.
- [ ] Upload the version-pinned code-and-data reproducibility archive as
  supplementary material for peer review.
- [ ] Upload the editable manuscript source (`.tex`, `.bib`, and active figure
  files); the PDF is a rendering for inspection, not an acceptable source file.
- [x] Corresponding author confirmed that the work received no funding; the
  manuscript now contains the author-confirmed no-funding statement.
- [x] Corresponding author provided the phone number requested by the journal
  submission system. Enter it directly in the private portal; the number is
  intentionally not committed to the repository or public data package.
- [ ] Authors must complete Elsevier's declarations tool and upload its
  generated competing-interest `.doc` or `.docx` file.

## FAIR Data Gate

The journal's current Guide for Authors assigns Option C to research data:
authors are required to deposit the research data in a relevant repository and
cite and link the dataset in the article. The Zenodo route and licenses are now
fixed, and the DOI is present in both the manuscript and bibliography. The
record itself must be published before pressing `Submit`; a reserved DOI that
still returns HTTP 404 is not yet public. The GitHub repository may remain
private until the author makes it public immediately after submission because
the public Zenodo record supplies the versioned data-and-code archive.

Do not upload licensed POTCAR files, WAVECAR/CHGCAR files, or unrestricted raw
VASP outputs. A private URL plus "available on request" does not satisfy the
Option C deposit-and-link instruction.

The release-ready payload is `submission_data/`; rebuild and validate it with
`python review_revision/build_fair_submission_data.py --check`. Its data license
is recorded in `submission_data/DATA_LICENSE.md`.

## Automated Gates

- Content/evidence gate:
  `python review_revision/static_check_manuscript.py`
- Public-archive integrity and claim gate:
  `python review_revision/build_fair_submission_data.py --check` and
  `python review_revision/verify_manuscript_numbers.py --curated-only`
- Version-pinned reproducibility ZIP gate:
  `python review_revision/build_reproducibility_archive.py --check <archive.zip>`;
  after extraction, `python review_revision/static_check_manuscript.py --archive-only`
- Full-workspace raw-provenance gate:
  `python review_revision/verify_manuscript_numbers.py`
- Final upload gate:
  `python review_revision/static_check_manuscript.py --submission-ready`

The final upload gate checks the DOI citation, licenses, GitHub link, funding
statement, and cover-letter state. A separate live check of the DOI must return
success before upload.

## Scientific Claim Gates

- [x] PBE-D3(BJ)/dipole adsorption anchors: 11/11 component jobs usable.
- [x] Initial high-displacement snapshot checks: 9/9 usable as stress tests.
- [ ] CI-NEB: no value meets the formal inclusion gate; no barrier enters the paper.
- [x] Seven converged extended-trajectory snapshot DFT checks spanning three
  trajectory/model contexts are reported as targeted out-of-domain evidence.

The unchecked scientific gates are optional strengthening calculations, not
dependencies of the current validation-first submission route.

# Computational Materials Science Submission Checklist

Date checked: 2026-07-26

## Candidate Target

`Computational Materials Science` is the current best-fit 3+ impact-factor
candidate for the evidence-bounded version of this work.

- Publisher-reported 2025 metrics: Impact Factor 3.3; CiteScore 6.6.
- Indexing listed by the publisher: Science Citation Index Expanded.
- Scope fit: computational methods, two-dimensional materials,
  machine-learning-enhanced simulation, method validation, and transferable
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

- [x] Manuscript title uses the validation-first DFT--MACE framing.
- [x] Abstract is below the journal's 250-word limit.
- [x] Seven English keywords are present.
- [x] Five highlights are present and each is at most 85 characters:
  `manuscript/highlights.txt`.
- [x] A data-derived, non-generative-AI graphical abstract is present at
  `manuscript/graphical_abstract.png` (3600 x 1440, 2.5:1, 300 dpi), with a
  separate caption.
- [x] The manuscript includes the required declaration of generative-AI use in
  manuscript preparation.
- [x] Author contributions use full author names, the standard CRediT heading,
  and the CRediT taxonomy.
- [x] The manuscript uses Elsevier's standard author-responsibility and
  no-known-competing-interest wording.
- [x] Accepted VASP/MACE/LAMMPS versions, model-training settings, and MD
  thermostat/equilibration/MSD details are documented and evidence-checked.
- [x] A 3.23 MB curated submission-data package contains both extxyz split
  definitions, numerical evidence tables, sanitized paths, and SHA256 hashes.
- [x] A concise initial-submission cover-letter draft is present at
  `manuscript/cover_letter_computational_materials_science.txt`.
- [ ] Create a public Option C research-data deposit and cite its URL or DOI in
  the Data and Code Availability section.
- [ ] Remove the `DRAFT` banner from the cover letter after the public data route
  and submission date are fixed.
- [ ] Upload the version-pinned code-and-data reproducibility archive as
  supplementary material for peer review.
- [ ] Corresponding author must confirm the funding statement.
- [ ] Corresponding author must provide the phone number requested by the
  journal submission system.
- [ ] Authors must complete Elsevier's declarations tool and upload its
  generated competing-interest `.doc` or `.docx` file.

## FAIR Data Gate

The journal's current Guide for Authors assigns Option C to research data:
authors are required to deposit the research data in a relevant repository and
cite and link the dataset in the article. The remote GitHub repository was
verified as `PRIVATE` on 2026-07-26, so the current draft does not yet satisfy
that upload gate. The version-pinned supplementary archive gives referees
inspectable code and curated evidence, but it does not replace the public
repository link required in the manuscript.

Before pressing `Submit`, choose one public-release route:

1. Make the curated GitHub repository public, create a versioned release, and
   cite its stable URL.
2. Deposit the curated code, extxyz splits, evidence tables, and model metadata
   in Zenodo or another public repository and cite its DOI. This is the stronger
   archival route.

Do not upload licensed POTCAR files, WAVECAR/CHGCAR files, or unrestricted raw
VASP outputs. A private URL plus "available on request" does not satisfy the
Option C deposit-and-link instruction.

The release-ready payload is `submission_data/`; rebuild and validate it with
`python review_revision/build_fair_submission_data.py --check`. Its data license
must be selected by the authors before public release.

## Automated Gates

- Content/evidence gate:
  `python review_revision/static_check_manuscript.py`
- Public-archive integrity and claim gate:
  `python review_revision/build_fair_submission_data.py --check` and
  `python review_revision/verify_manuscript_numbers.py --curated-only`
- Full-workspace raw-provenance gate:
  `python review_revision/verify_manuscript_numbers.py`
- Final upload gate:
  `python review_revision/static_check_manuscript.py --submission-ready`

The second command must pass before upload. It intentionally remains red until
the public data link is cited, the author-confirmed Funding section is present,
and the cover-letter `DRAFT` banner is removed.

## Scientific Claim Gates

- [x] PBE-D3/dipole adsorption anchors: 11/11 component jobs usable.
- [x] Initial high-displacement snapshot checks: 9/9 usable as stress tests.
- [ ] Fast CI-NEB: 0/5 formally converged; no barriers may enter the paper.
- [ ] Full CI-NEB: 0/10 formally converged with 1 fatal path.
- [ ] Production-trajectory snapshot DFT: 2/7 usable; no production-set
  validation claim may enter the paper.

The unchecked scientific gates are optional strengthening calculations, not
dependencies of the current validation-first submission route.

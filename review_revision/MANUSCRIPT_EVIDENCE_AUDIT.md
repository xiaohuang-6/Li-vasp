# Manuscript Evidence Audit

Date: 2026-07-26 05:15 EDT

Scope: `manuscript/li_mace_graphene_draft.tex` was checked against the current
worktree, `review_revision/check_reviewer_jobs.sh`, and current
`results/review_revision/*` outputs. The old Codex conversation was not used as
evidence.

## Verified Computational Claims

- Dataset size: 273 total MACE frames = 194 relaxation frames + 79
  fixed-geometry site/path single-point frames, from
  `data/mace_datasets/li_mace_dataset_report.json`.
- Original split: 211 train, 31 validation, 31 test frames; grouped split:
  263 train, 5 validation, 5 test frames. These counts were verified by reading
  the extxyz files with ASE.
- Original MACE evaluator values in Table `tab:mace_errors` match
  `results/review_revision/gpu_analysis/mace_eval_summary.csv`.
- Committee validation force RMSE values 96.4, 107.2, and 48.4 meV/A match
  `results/review_revision/gpu_analysis/committee_summary.csv`.
- Grouped-E0 training completed on the local RTX 5080 and produced model plus
  LAMMPS model. Grouped test force RMSE values in the manuscript are explicitly
  the first-stage grouped-E0 checkpoint metrics and match
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/logs/agent_grouped_e0_finetune.log`.
- PBE-D3(BJ)/dipole adsorption-energy values match
  `results/review_revision/adsorption_energy_analysis/adsorption_energies.csv`.
  All 11 component jobs are usable and have no fatal markers.
- Fixed-geometry path-span values match `results/two_day_rush/path_barriers.csv`.
  They remain endpoint/path-roughness descriptors, not migration barriers.
- 100 ps unwrapped MD completion and aggregate MSD values match
  `results/review_revision/gpu_analysis/REVIEWER_GPU_ANALYSIS.md` and related
  CSVs.
- 18-run 200--500 ps GPU production MD completion and aggregate values match
  `results/review_revision/gpu_analysis_20260725_0116/REVIEWER_GPU_ANALYSIS.md`
  and related CSVs.
- Initial-campaign snapshot DFT table values match
  `review_revision/SNAPSHOT_DFT_EVIDENCE.csv`; contact-distance values match
  the accepted 5080 snapshot-force evaluator CSV.
- Snapshot-force stress-test values match
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/SNAPSHOT_MACE_FORCE_VALIDATION.md`.
- Current scheduler/collector gates: no cluster GPU job is present; fast NEB is
  0/5 formally converged; full NEB is 0/10 formally converged with 1 fatal
  marker; production-trajectory snapshot DFT is 2/7 usable. The usable rows are
  `D_SiGraphene_seed20260427_step057000` (`MSDxy = 2687.8 A^2`,
  `E_DFT = -1899.724675 eV`) and
  `D_SiGraphene_seed20260427_step500000` (`MSDxy = 2436.1 A^2`,
  `E_DFT = -1903.110484 eV`). Both come from the same trajectory, so they are
  not enough for a production-trajectory validation claim.
- DFT labeling parameters and PAW dataset labels were checked against current
  `dft_outputs/*/{INCAR,KPOINTS,OUTCAR}` files. OUTCAR headers identify
  PAW_PBE C (08Apr2002), Li_sv (10Sep2004), and Si (05Jan2001). Adsorption
  single-point parameters were checked against
  `review_revision/prepare_adsorption_energy_jobs.py`.
- Software and run provenance was checked against the accepted runtime evidence:
  VASP 5.4.1 OUTCAR markers; MACE 0.3.15/0.3.16 logs and launch scripts;
  accepted architecture, precision, batch-size, learning-rate, epoch, and
  stage-two settings; the grouped-E0 263-configuration rank-3 fit and exact
  Li/C/Si baseline offsets; the accepted snapshot INCAR/KPOINTS and explicit
  absence of D3 and dipole corrections; and the LAMMPS 10 September 2025
  driver/input records for timestep, equilibration, thermostat, and
  unwrapped-coordinate MSD handling.
- Citation metadata was checked against Crossref for every DOI-bearing BibTeX
  entry. The MACE 2022 proceedings record was checked against the NeurIPS
  proceedings page and Crossref metadata, and the DOI was added to the BibTeX
  entry.
- `python review_revision/verify_manuscript_numbers.py` passed with 204 checks
  on 2026-07-26. The verifier revalidates title, keywords,
  author/affiliation text,
  dataset and split counts, MACE error values, first-stage grouped-E0 log
  metrics, D3(BJ)/dipole adsorption energies, 10 fixed-path descriptor rows, 18/18
  production-MD completion count, snapshot-DFT table values, snapshot-force
  stress-test values, PAW/E0/snapshot method provenance, software/run
  provenance, and production-snapshot DFT/NEB exclusion gates against the
  current logs, scripts, CSVs, and status files.
- `python review_revision/verify_manuscript_numbers.py --curated-only` passed
  with 155 checks using only the redistributable archive contents. It validates
  all 24 `MANIFEST.sha256` entries plus the curated dataset, MACE, adsorption,
  fixed-path, MD, snapshot-DFT, snapshot-force, and software-provenance claims.
  This narrower mode is explicitly not a raw-calculation reconstruction.

## Manuscript Edits From The Audit

- Reframed the title, abstract, introduction, implications, and conclusion
  around a validation-first AI-for-materials evidence hierarchy without adding
  kinetic or battery-performance claims.
- Kept the revised abstract at 236 words under the 250-word target-journal limit and
  added seven indexing keywords.
- Added five target-journal highlights, a data-derived 3600 x 1440 graphical
  abstract with a reproducible generator, the Elsevier 2.5:1 aspect ratio and
  300 dpi metadata, and a separate caption. The graphical abstract now labels
  the 285.2-to-20.1 meV/A comparison as an initial same-workflow metric, states
  that it is not a transferability claim, and withholds migration barriers
  without calling unconverged calculations barriers. Its generator reads the
  tracked curated CSVs in `submission_data/results/`, so it runs from a clean
  repository checkout without the untracked raw `results/` tree.
- Added the Elsevier-required declaration of generative-AI use in manuscript
  preparation, using the publisher's author-responsibility wording.
- Expanded the CRediT statement to full author names and replaced the abbreviated
  conflict statement with Elsevier's standard no-known-competing-interest
  wording.
- Added a compact path-sanitized `submission_data/` package containing the
  original and grouped extxyz splits, curated manuscript evidence tables, and a
  SHA256 manifest. Its integrity verifier and 155-check archive-contained
  manuscript verifier both pass without the ignored raw evidence workspace.
- Clarified the initial structure construction with a = 2.46 A, a 5 x 5
  graphene supercell, 30.0 A cell height, exact formulas, and a
  non-substitutional Si4 motif. Added the fixed-cell DFT settings, the
  deterministic grouped-split policy and one-configuration-per-family
  limitation, and the exact D3(BJ) interpretation of IVDW = 12.
- Added a PBE-D3(BJ)/dipole adsorption-energy table and method details.
- Added evidence-backed software versions, MACE architecture/training settings,
  and LAMMPS equilibration/thermostat/MSD details to the Methods and curated
  submission-data README.
- Added exact PAW dataset labels, grouped-E0 fit scope and baseline offsets, and
  the complete accepted snapshot single-point protocol to the Methods. The
  verifier now checks each statement directly against OUTCAR, input scripts, or
  the accepted local-5080 training log.
- Updated grouped-E0 text from future-tense to completed-but-diagnostic.
- Clarified that the 19.6, 10.9, 13.7, 42.9, and 9.2 meV/A grouped-E0
  family force RMSEs are first-stage checkpoint metrics from the 5080 log, not
  the later stage-two/SWA table.
- Updated high-displacement snapshot-force language to include the mixed
  grouped-E0 result: Si4-graphene improves, monovacancy remains poor.
- Reworded Data and Code Availability so the manuscript does not claim a
  nonexistent archive DOI, public access to the currently private repository,
  or inclusion of large `results/`, raw VASP/LAMMPS outputs, or licensed files.
  The manuscript now states that a version-pinned code-and-data archive is
  supplied as supplementary material for peer review and that a public release
  URL or DOI will be added and cited before submission.
- Added a concise initial-submission cover-letter draft that positions the work
  as a validation-first AI-for-science and battery-materials workflow without
  adding unsupported physical claims to the manuscript.
- Removed an unsupported external numeric barrier comparison and kept the
  literature point qualitative.
- Replaced the stale first-author affiliation with the user-confirmed
  University of Waterloo affiliation and avoided inventing an unverified
  department.
- Reworded the abstract and MD section to avoid kinetic language before
  converged CI-NEB or diffusion evidence is available.
- Replaced remaining qualitative wording in the model-system, adsorption,
  MD-diagnostic, and snapshot-contact sections with exact values from the
  current structure-generation script, adsorption collector, GPU MD summary,
  and accepted 5080 snapshot-force CSV.
- Extended `review_revision/static_check_manuscript.py` to reject the
  submission-risk phrases found during this pass, including `approximately`,
  `about `, `much more strongly`, and related qualitative shortcuts.

## PDF Build And Layout Check

- `manuscript/li_mace_graphene_draft.pdf` was compiled successfully on
  2026-07-26 after the validation-first revision with a temporary Tectonic
  binary.
- The final log contains no `Overfull`, `Underfull`, undefined-reference,
  error, or fatal entries after grepping
  `manuscript/li_mace_graphene_draft.log`. The only retained package warning is
  the harmless `inputenc` warning under the UTF-8 engine.
- All 16 rendered PDF pages were visually inspected, including the title page,
  main MACE diagnostics table, MD diagnostics, snapshot-DFT table, conclusion,
  data/code availability, generative-AI declaration, and compact two-page
  reference list. A cross-page sentence split on pages 6--7 was shortened and
  recompiled. Pages 14--15 were re-rendered after the final author-declaration
  wording changes and remained free of clipping or overlap.
- The graphical abstract was inspected at its native 3600 x 1440 resolution and
  at the 500 x 200 display size; the same-workflow qualifier, claim-gate wording,
  label proximity, and panel overflow were checked before acceptance.

## Still Not Independently Verified

- Author names and affiliations are not derivable from the computational
  evidence. The first-author name is user-confirmed as `Yuhan Sun`; the
  first-author institution is user-confirmed as University of Waterloo. The
  manuscript and `LICENSE` use `Yuhan Sun`, and the manuscript now lists
  `University of Waterloo, Waterloo, ON N2L 3G1, Canada` without an unverified
  department. Targeted history search found only the stale template name
  `Yuran Chai` and stale Wake Forest affiliation, and a public-web check did
  not find an authoritative page confirming `Yuhan Sun` with University of
  Waterloo.
- External literature summaries were checked for citation-key presence,
  overclaiming risk, and DOI metadata consistency. This corrected mismatched
  bibliography entries for Yildirim 2014, the silicon/graphene review article,
  Palumbo 2019, Batatia 2025, and Jacobs 2025. The manuscript no longer relies
  on a specific unverified external barrier number.
- No public archive DOI is minted in the current local evidence. The manuscript
  no longer lists a DOI as an existing record.

## Current Conclusion

The computational claims in the manuscript are tied to current local evidence
and bounded by explicit validation gates. The first-author name and University
of Waterloo institution reflect the user-confirmed submission metadata. The
remaining optional computational gates are NEB and production-snapshot DFT; the
current manuscript does not rely on them. For the current 3+ impact-factor
candidate target, the unresolved non-computational gate is FAIR access: the
remote GitHub repository is private and must be made public or replaced by a
public versioned archive/DOI before submission.

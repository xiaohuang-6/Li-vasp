# Reproducibility Archive Manifest

This file defines the full reproducibility package for the Li--MACE graphene
workflow. The Git repository tracks the license- and size-compatible subset:
source code, manuscript source, curated figures, input-generation scripts,
validation scripts, and small evidence tables. Larger processed outputs and raw
runtime files are excluded from Git and are available from the corresponding
author on reasonable request. The versioned archive is assigned Zenodo DOI
`10.5281/zenodo.21609229`.

## Archive Identifier

- Repository: `https://github.com/xiaohuang-6/Li-vasp`
- Release tag: `review-revision-20260725` or a later submission tag.
- DOI: `https://doi.org/10.5281/zenodo.21609229`.
- Data license: CC BY 4.0 for curated scientific data.
- Code license: MIT for workflow and analysis software.
- Repository visibility: retained at the URL above and scheduled to become
  public immediately after manuscript submission.

## Include

- Active manuscript source under `manuscript/`, including `references.bib`,
  only the figures used by the current manuscript or graphical abstract, and
  the generators that rebuild the graphical abstract and both MACE diagnostic
  panels from tracked curated data.
- The compact `submission_data/` package, including the 273-frame original and
  group-held-out extxyz splits, curated numerical evidence tables, package
  documentation, and `MANIFEST.sha256`.
- `review_revision/verify_manuscript_numbers.py`, whose `--curated-only` mode
  validates the manifest and manuscript claims using only files distributed in
  the archive. Its default mode remains the deeper raw-evidence audit.
- Structure-generation scripts and representative structure files needed to
  reproduce the small-cell VASP inputs and LAMMPS data files.
- VASP input-generation scripts, CPU Slurm templates, and job manifests.
- MACE setup, inspection, fine-tuning, conversion, and evaluation scripts.
- LAMMPS input scripts, Slurm launchers, and post-processing scripts.
- Processed CSV/JSON/Markdown evidence tables used in the manuscript, including:
  - train/validation/test split manifests and split-leakage audit reports;
  - MACE foundation/fine-tuned evaluation summaries;
  - MD completion and unwrapped-MSD diagnostics;
  - DFT snapshot evidence with OUTCAR hashes, energies, convergence markers, and
    force-readability status;
  - adsorption-energy and NEB collectors once the corresponding jobs complete.
- Model provenance metadata, including the exact foundation checkpoint name
  `mace-mpa-0-medium.model` and fine-tuned model run names.

The workflow and analysis software use the repository MIT license. Curated
scientific data use CC BY 4.0, as recorded in
`submission_data/DATA_LICENSE.md`.

## Exclude

- Licensed VASP POTCAR files.
- Foundation and fine-tuned model checkpoint binaries; the archive retains the
  exact checkpoint/run names, training settings, and accepted training log.
- Full raw OUTCAR files, WAVECAR, CHGCAR, CHG, vasprun.xml, and other large or
  license-sensitive VASP runtime outputs.
- Machine-local Conda environments, third-party source/build trees, CUDA
  libtorch archives, LAMMPS build products, and Slurm scratch logs.
- Superseded manuscript drafts and local backup copies; the archive exports only
  the active manuscript source.
- Submission-administration files, response-letter drafts, internal agent
  handoffs, local GPU transfer packs, disabled cluster-GPU guards, and historical
  figure variants that are not used by the active manuscript.
- Large raw trajectories unless the final archive size budget permits them; if
  excluded, the processed MSD traces and trajectory manifests are included.

The repository retains excluded project-history files where they remain useful
to maintainers. The journal reproducibility ZIP applies the `export-ignore`
rules in `.gitattributes`; build and verify it with
`review_revision/build_reproducibility_archive.py`. After extraction, run
`python review_revision/static_check_manuscript.py --archive-only` for the
content gate that intentionally omits separately uploaded cover-letter and
highlight checks. Future GPU calculations are not part of that ZIP: they must be
distributed separately as bounded local RTX 5080 run packs that complete in less
than 24 hours.

## Traceability Policy

For raw files that cannot be redistributed, the archive contains enough metadata
to audit the reported numbers: path, file size, modification time, SHA256 hash,
parsed final energy, convergence markers, and force-readability checks. The
nine initial-campaign high-displacement snapshot checks are documented in
`review_revision/SNAPSHOT_DFT_EVIDENCE.md` and
`review_revision/SNAPSHOT_DFT_EVIDENCE.csv`. Seven additional converged checks
from extended trajectories are exported in
`submission_data/results/extended_snapshot_dft_evidence.csv`; together these
provide 16 traceable DFT snapshot checks.

The archive-level verifier does not reconstruct excluded raw calculations. It
checks the integrity of the curated files and consistency between those files
and the manuscript. The default full-evidence verifier additionally checks raw
OUTCAR markers, input scripts, runtime logs, and live collector/status gates.
The active MACE dataset-count and same-workflow force-RMSE panels regenerate
from `submission_data/results/mace_eval_summary.csv`; their publication-facing
labels, force unit, and transferability limitation do not depend on the ignored
raw-results tree.

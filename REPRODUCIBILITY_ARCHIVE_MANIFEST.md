# Reproducibility Archive Manifest

This file defines the full reproducibility package for the Li--MACE graphene
workflow. The Git repository tracks the license- and size-compatible subset:
source code, manuscript source, curated figures, input-generation scripts,
validation scripts, and small evidence tables. Larger processed outputs and raw
runtime files are excluded from Git and are available from the corresponding
author on reasonable request. The manuscript does not claim an archive DOI.

## Archive Identifier

- Repository: `https://github.com/xiaohuang-6/Li-vasp`
- Release tag: `review-revision-20260725` or a later submission tag.
- DOI: no DOI is claimed in the current manuscript.
- License: MIT for workflow scripts, analysis scripts, and manuscript source.

## Include

- Manuscript source under `manuscript/`, including `references.bib` and curated
  figures.
- The compact `submission_data/` package, including the 273-frame original and
  group-held-out extxyz splits, curated numerical evidence tables, package
  documentation, and `MANIFEST.sha256`.
- `review_revision/verify_manuscript_numbers.py`, whose `--curated-only` mode
  validates the manifest and manuscript claims using only files distributed in
  the archive. Its default mode remains the deeper raw-evidence audit.
- Structure-generation scripts and representative structure files needed to
  reproduce the small-cell VASP inputs and LAMMPS data files.
- VASP input-generation scripts, Slurm submission templates, and job manifests.
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

The software and manuscript source use the repository MIT license. The authors
must select and declare a license for the curated scientific data before making
the submission package public.

## Exclude

- Licensed VASP POTCAR files.
- Full raw OUTCAR files, WAVECAR, CHGCAR, CHG, vasprun.xml, and other large or
  license-sensitive VASP runtime outputs.
- Machine-local Conda environments, third-party source/build trees, CUDA
  libtorch archives, LAMMPS build products, and Slurm scratch logs.
- Superseded manuscript drafts and local backup copies; the archive exports only
  the active manuscript source.
- Large raw trajectories unless the final archive size budget permits them; if
  excluded, the processed MSD traces and trajectory manifests are included.

## Traceability Policy

For raw files that cannot be redistributed, the archive contains enough metadata
to audit the reported numbers: path, file size, modification time, SHA256 hash,
parsed final energy, convergence markers, and force-readability checks. The
current nine initial-campaign high-displacement snapshot checks are documented
in `review_revision/SNAPSHOT_DFT_EVIDENCE.md` and
`review_revision/SNAPSHOT_DFT_EVIDENCE.csv`.

The archive-level verifier does not reconstruct excluded raw calculations. It
checks the integrity of the curated files and consistency between those files
and the manuscript. The default full-evidence verifier additionally checks raw
OUTCAR markers, input scripts, runtime logs, and live collector/status gates.

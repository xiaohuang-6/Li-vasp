# Reproducibility Archive Manifest

This file defines the full reproducibility package for the Li--MACE graphene
workflow. The Git repository tracks the license- and size-compatible subset:
source code, manuscript source, curated figures, input-generation scripts,
validation scripts, evidence tables, labeled extxyz data, and the five
author-trained MACE checkpoints used in the article. Larger processed outputs
and raw runtime files are excluded from Git and are available from the
corresponding author on reasonable request. The source-commit identifier is
fixed when the strengthened archive is built after all evidence checks pass.

## Archive Identifier

- Distribution: article-linked Supplementary Data supplied with the manuscript.
- Version identifier: the source commit is stored in the ZIP comment and is
  checked by `review_revision/build_reproducibility_archive.py`.
- File integrity: `submission_data/MANIFEST.sha256` covers every curated data
  and model file in the package.
- Data license: CC BY 4.0 for curated scientific data.
- Code license: MIT for workflow and analysis software.

## Include

- Active manuscript source under `manuscript/`, including all former SI tables
  and figures in the main article,
  including `references.bib`, only the figures used by the current article,
  or graphical abstract, and the generators that
  rebuild the scientific summary, path, MSD, and graphical-abstract figures.
- The compact `submission_data/` package, including the 273-frame original and
  group-held-out extxyz splits, curated numerical evidence tables, package
  documentation, and `MANIFEST.sha256`.
- `review_revision/verify_resubmission_science.py`, which validates the revised
  manuscript's central adsorption, interpolation, snapshot-force, structural,
  and scope claims against the evidence tables.
- Structure-generation scripts, initial VASP inputs, and the five converged
  DFT-relaxed structures used in the manuscript structure figure.
- VASP input-generation scripts, CPU Slurm templates, and job manifests.
- MACE setup, inspection, fine-tuning, conversion, and evaluation scripts.
- LAMMPS input scripts, Slurm launchers, and post-processing scripts.
- Processed CSV/JSON/Markdown evidence tables used in the manuscript, including:
  - train/validation/test split manifests and split-leakage audit reports;
  - MACE foundation/fine-tuned evaluation summaries;
  - family-balanced and high-displacement DFT extxyz frames with energies,
    forces, strict-SCF metadata, and source-output hashes;
  - MD completion and unwrapped-MSD diagnostics;
  - DFT snapshot evidence with OUTCAR hashes, energies, convergence markers, and
    force-readability status;
  - strict 273-frame training-label SCF audit, 15-site PBE-D3(BJ)/dipole
    adsorption evidence, the five-row relaxed-structure force/moment summary,
    and the 25-frame balanced force benchmark.
- The five author-trained MACE checkpoints used by the manuscript, with exact
  roles, byte sizes, and SHA256 hashes under `submission_data/models/`.
- Foundation-model provenance for `mace-mpa-0-medium.model`, including its
  official MIT-licensed release URL, byte size, and SHA256 hash.

The workflow and analysis software use the repository MIT license. Curated
scientific data use CC BY 4.0, as recorded in
`submission_data/DATA_LICENSE.md`.

## Exclude

- Licensed VASP POTCAR files.
- The public MACE-MPA-0 foundation checkpoint binary, which is not duplicated;
  the archive records its official release URL and exact hash.
- Full raw OUTCAR files, WAVECAR, CHGCAR, CHG, vasprun.xml, and other large or
  license-sensitive VASP runtime outputs.
- Machine-local Conda environments, third-party source/build trees, CUDA
  libtorch archives, LAMMPS build products, and Slurm scratch logs.
- Superseded manuscript drafts and local backup copies; the archive exports only
  the active manuscript source.
- Submission-administration files, response-letter drafts, internal handoffs,
  machine-specific accelerator transfer packs, deprecated launchers, and
  historical figure variants that are not used by the active manuscript.
- Large raw trajectories unless the final archive size budget permits them; if
  excluded, the processed MSD traces and trajectory manifests are included.

The repository retains excluded project-history files where they remain useful
to maintainers. The journal reproducibility ZIP applies the `export-ignore`
rules in `.gitattributes`; build and verify it with
`review_revision/build_reproducibility_archive.py`. After extraction, run
`python review_revision/static_check_manuscript.py --archive-only` for the
content gate that intentionally omits separately uploaded cover-letter and
highlight checks.

## Traceability Policy

For raw files that cannot be redistributed, the archive contains enough metadata
to audit the reported numbers: path, file size, modification time, SHA256 hash,
parsed final energy, convergence markers, and force-readability checks. The
nine initial-campaign high-displacement snapshot checks are documented in the
path-sanitized
`submission_data/results/initial_snapshot_dft_evidence.csv`. Seven additional
converged checks from extended trajectories are exported in
`submission_data/results/extended_snapshot_dft_evidence.csv`; together these
provide 16 traceable DFT snapshot checks.

The archive-level checks do not reconstruct excluded raw calculations. They
check the integrity of the curated package and the consistency of the revised
scientific claims with the distributed evidence. Maintainers with the full
evidence tree can pass that path through `--evidence-root` to repeat the deeper
claim audit. The scientific summary regenerates from the adsorption and
family-balanced and high-displacement force CSV files; its labels, units, and
transferability boundaries do not depend on the ignored raw-results tree.

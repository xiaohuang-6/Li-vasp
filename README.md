# Li-MACE Graphene Reproducibility Archive

This archive accompanies the study of dilute Li adsorption and
local-environment-dependent MACE transferability across pristine graphene,
monovacancy graphene, divacancy graphene, Stone-Wales graphene, and a local
Si4-graphene motif.

The article combines spin-polarized VASP calculations, fine-tuning from the
MACE-MPA-0 foundation model, and direct DFT force tests. The central distributed
evidence comprises:

- 273 DFT training labels with a strict final-electronic-iteration audit;
- five relaxed reference structures with final-force, magnetic-moment, and
  source-hash evidence, together with their final coordinates;
- 15 fixed-geometry PBE-D3(BJ)/dipole adsorption checks, with three
  prespecified Li placements in each structural family;
- 25 model-blind DFT perturbations balanced across the five families;
- nine strictly converged high-displacement DFT frames used for direct
  foundation-versus-fine-tuned force comparisons;
- seven additional converged DFT snapshot checks used as coverage evidence;
- only completed molecular-dynamics trajectories in the distributed trajectory
  tables.

The fixed-geometry adsorption checks are not exhaustive relaxed-site searches.
The interpolation-path descriptors are not migration barriers, and the
finite-window trajectories are not used to report diffusion coefficients.

## Archive Layout

- `manuscript/`: article source (including all former SI figures and tables), active figures, and
  figure-generation scripts.
- `submission_data/`: path-sanitized datasets, numerical evidence tables,
  author-trained checkpoints, licenses, and `MANIFEST.sha256`.
- `review_revision/`: preparation, collection, plotting, and independent
  consistency-check scripts used for the revision.
- `structures/`: representative structure files used to prepare the VASP
  calculations.
- `REPRODUCIBILITY_ARCHIVE_MANIFEST.md`: inclusion, exclusion, versioning, and
  traceability policy for this archive.

## Verify The Distributed Evidence

Run the following commands from the extracted archive root:

```bash
python review_revision/build_fair_submission_data.py --check
python review_revision/verify_resubmission_science.py --archive-only
python review_revision/static_check_manuscript.py --archive-only
```

These checks validate file hashes, expected row and frame counts, strict-SCF
fields, model checkpoint hashes, and numerical consistency between the curated
tables and manuscript. They do not recompute excluded VASP calculations.

The article PDFs can be rebuilt with:

```bash
bash manuscript/compile_manuscript.sh
```

A working LaTeX engine and the packages imported by the source files are
required.

The Git checkout also contains the second-resubmission instructions in
`review_revision/R2_REVISION_NOTES.md`. The R2 article includes all former SI
figures and tables. The marked PDF is generated against the submitted R1 source,
and response locations are generated from the clean PDF's line labels.
Submission-administration tools and notes are omitted from the journal data archive.

## Models And Data

`submission_data/models/` contains the five author-trained checkpoints used in
the article. The MACE-MPA-0 foundation checkpoint is not duplicated; its
official source, byte size, and SHA256 hash are recorded in
`submission_data/models/README.md`.

The curated scientific data are licensed under CC BY 4.0. Workflow and analysis
code are licensed under MIT. See `submission_data/DATA_LICENSE.md` and
`LICENSE`.

## Excluded Files

Licensed VASP POTCAR files and large runtime products such as raw OUTCAR,
WAVECAR, CHGCAR, trajectories, and machine-local environments are not
redistributed. The evidence tables retain source-output hashes, parsed values,
convergence fields, and provenance sufficient to audit every reported row.
Full exclusion and traceability details are given in
`REPRODUCIBILITY_ARCHIVE_MANIFEST.md`.

# Curated Submission Data

This directory contains the compact, redistributable evidence package for the
study of Li adsorption and local-environment-dependent MACE transferability on
graphene defects. It excludes
licensed VASP POTCAR files, raw OUTCAR/WAVECAR/CHGCAR files, and large
trajectories. The five author-trained MACE checkpoints used in the manuscript
are included under `models/`; the public MACE-MPA-0 foundation checkpoint is
fixed by source, byte size, and SHA256 rather than duplicated.

This curated snapshot is distributed with the article as Supplementary Data.
Its source commit is stored in the reproducibility ZIP metadata, and
`MANIFEST.sha256` records file-level integrity. Curated scientific data in this
directory are licensed under CC BY 4.0; workflow and analysis software are
licensed under MIT.

## Dataset Splits

`datasets/original_split/` contains the 211/31/31 train/validation/test split
used for the same-workflow baseline. Correlated fixed-path images cross this
split, so it must not be described as an independent transferability test.

`datasets/grouped_split/` contains the leakage-audited 263/5/5 split. Frames
from each relaxation trajectory or fixed interpolation path are assigned as a
group. All relaxation trajectories remain in training; sorted site/path groups
are assigned within each family by a deterministic 8:1:1
train/validation/test cycle. Validation and test therefore each contain one
configuration per family. These held-out sets define a leakage audit, not a
broad transferability benchmark.

Each extxyz frame includes cell, species, positions, DFT energy, DFT forces,
configuration family, and relative provenance labels. The 273 unique frames
comprise 194 ionic-relaxation frames and 79 fixed-geometry site/path frames.

## Curated Results

`results/` contains the numerical tables supporting the manuscript:

- foundation and fine-tuned MACE split metrics;
- three-seed committee metrics;
- a 273-row strict-SCF audit of every training label;
- a five-row relaxed-structure summary with ionic convergence, final maximum
  forces, magnetic moments, and source-output hashes;
- the five corresponding DFT-relaxed structures used in the manuscript
  structure figure;
- 15 PBE-D3(BJ)/dipole fixed-geometry adsorption checks spanning three
  prespecified sites in each of five families, with finite-energy/force and
  source-hash fields for the adsorbed, substrate, and isolated-Li calculations;
- a model-blind 25-configuration DFT perturbation benchmark, including DFT
  extxyz frames and two-model frame-level and summary errors;
- fixed-geometry site and path descriptors;
- 15-run initial 100 ps MD completion/displacement diagnostics;
- 18-run extended MD completion/displacement diagnostics (the retained CSV
  filenames use the historical `production_md` label);
- the 1818-row sampled MSD trace table used to regenerate the main manuscript's
  trajectory figure (transferred from the R1 Supporting Information);
- initial-campaign snapshot DFT hashes and convergence fields;
- nine-frame high-displacement DFT extxyz data with coordinates, energies,
  forces, SCF provenance, and source-output hashes;
- seven electronically converged extended-trajectory snapshot DFT checks
  spanning three trajectory/model contexts, with OUTCAR hashes;
- foundation and grouped-E0 snapshot-force stress-test values.

The fixed interpolation paths are configuration descriptors, not migration
barriers. The MD files do not establish diffusion coefficients. Snapshot checks
are out-of-domain stress tests, not validation of a transport mechanism.

## Model Checkpoints

`models/` contains the reference fine-tuned checkpoint, the three committee
checkpoints, and the corrected grouped-E0 checkpoint. Their roles, sizes, and
hashes are listed in `models/README.md`. The MACE-MPA-0 foundation model is
available from its official MIT-licensed release; the exact URL and hash are
recorded in that file.

## Software And Run Provenance

- DFT labels and multi-site adsorption checks used VASP 5.4.1. Archived OUTCAR headers
  identify the PAW_PBE datasets as C (08Apr2002), Li_sv (10Sep2004), and Si
  (05Jan2001).
- Initial structures used a = 2.46 A, a 5 x 5 graphene supercell, and a 30.0 A
  cell height (15.0 A vacuum on each side of the initial sheet). Their formulas
  are C50Li, C49Li, C48Li, C50Li, and C50LiSi4; the Si4 motif places four
  non-substitutional Si atoms above the intact C50 sheet.
- Adsorption checks used DFT-D3 with Becke-Johnson damping (IVDW = 12) and a
  slab dipole correction (LDIPOL = True, IDIPOL = 3). An ALGO = Normal
  PBE-D3(BJ) stage without the dipole correction preconditions the electronic
  state; the final stage restarts from its wavefunctions and charge density with
  ALGO = All and the dipole correction. Each stage is accepted only after
  normal termination with a final electronic iteration below NELM.
- The reference fine-tuning used MACE 0.3.15; committee and grouped-E0 revision
  runs used MACE 0.3.16. The accepted grouped-E0 training log is included under
  `logs/`.
- The local RTX 5080 revision environment used PyTorch 2.11.0+cu128, CUDA 12.8,
  and ASE 3.29.0.
- Extended MD diagnostics used LAMMPS 10 September 2025 with the MACE pair
  style.

The reference model used batch size 2, double precision, 300 epochs, an initial
learning rate of 5e-4, and stochastic weight averaging from epoch 225. The
committee and grouped-E0 runs used batch size 4, 300 epochs, an initial learning
rate of 1e-3, and the same epoch-225 transition; committee runs used single
precision and the grouped-E0 run used double precision. Extended MD used a
1 fs timestep, 10 ps equilibration, a 400 K Nose-Hoover NVT thermostat with a
0.1 ps damping time, and unwrapped-coordinate Li MSD with collective Li
center-of-mass drift removal.

The grouped-E0 estimator used foundation-model predictions on all 263 grouped
training configurations. Its accepted log records a full-rank 3/3 elemental fit
and final Li/C/Si baseline offsets of -3.271318, -1.246324, and -1.280346 eV;
these are model offsets rather than isolated-atom energies. The
high-displacement snapshot DFT tests used spin-polarized PAW-PBE,
ENCUT = 520 eV, EDIFF = 1e-6 eV, Gaussian smearing (ISMEAR = 0,
SIGMA = 0.05 eV), PREC = Accurate, LREAL = False, ISYM = 0, LASPH, ADDGRID,
IBRION = -1, NSW = 0, and Gamma-only 1 x 1 x 1 sampling. Five strict outputs
use ALGO = Normal and NELM = 160; four use a two-stage ALGO = All
precondition-and-restart protocol with TIME = 0.2 and NELM values of 180 and
240. They did not add an explicit dispersion or dipole correction.

## Rebuild And Verify

From the extracted Supplementary Data archive:

```bash
python review_revision/build_fair_submission_data.py --check
python review_revision/verify_resubmission_science.py --archive-only
```

`MANIFEST.sha256` records the hash of every package file. Exported CSV and log
paths are sanitized to remove machine-specific absolute prefixes. The
verifier resolves these curated reports, tables, and logs when the excluded
raw evidence tree is absent. It checks the manifest and manuscript claims; it
does not claim to recompute values from raw VASP or trajectory files.

Maintainers with the full evidence workspace can rebuild the package and run
the deeper provenance audit:

```bash
python review_revision/build_fair_submission_data.py
python review_revision/verify_resubmission_science.py --evidence-root /path/to/full/evidence
```

The full-evidence run rebuilds the curated package from the collector outputs
and repeats the cross-file convergence, row-count, source-hash, and numerical-
claim checks before export.

## Release Status

This package is the data-and-code snapshot distributed with the strengthened
resubmission for peer review and publication. The source-commit identifier in
the reproducibility ZIP and the file-level SHA256 manifest provide the immutable
version and integrity records for this Supplementary Data release.

# Curated Submission Data

This directory contains the compact, redistributable evidence package for the
validation-first DFT--MACE manuscript. It excludes licensed VASP POTCAR files,
raw OUTCAR/WAVECAR/CHGCAR files, large trajectories, and model checkpoints.

## Dataset Splits

`datasets/original_split/` contains the 211/31/31 train/validation/test split
used for the same-workflow baseline. Correlated fixed-path images cross this
split, so it must not be described as an independent transferability test.

`datasets/grouped_split/` contains the leakage-audited 263/5/5 split. Frames
from each relaxation trajectory or fixed interpolation path are assigned as a
group. The held-out sets are intentionally small and define a leakage audit,
not a broad transferability benchmark.

Each extxyz frame includes cell, species, positions, DFT energy, DFT forces,
configuration family, and relative provenance labels. The 273 unique frames
comprise 194 ionic-relaxation frames and 79 fixed-geometry site/path frames.

## Curated Results

`results/` contains the numerical tables supporting the manuscript:

- foundation and fine-tuned MACE split metrics;
- three-seed committee metrics;
- PBE-D3/dipole adsorption-energy anchors;
- fixed-geometry site and path descriptors;
- 18-run production MD completion/displacement diagnostics;
- initial-campaign snapshot DFT hashes and convergence fields;
- foundation and grouped-E0 snapshot-force stress-test values.

The fixed-path files do not contain converged migration barriers. The MD files
do not establish diffusion coefficients. Snapshot checks are out-of-domain
stress tests, not validation of a transport mechanism.

## Software And Run Provenance

- DFT labels and adsorption anchors used VASP 5.4.1. Archived OUTCAR headers
  identify the PAW_PBE datasets as C (08Apr2002), Li_sv (10Sep2004), and Si
  (05Jan2001).
- The reference fine-tuning used MACE 0.3.15; committee and grouped-E0 revision
  runs used MACE 0.3.16. The accepted grouped-E0 training log is included under
  `logs/`.
- The local RTX 5080 revision environment used PyTorch 2.11.0+cu128, CUDA 12.8,
  and ASE 3.29.0.
- Production MD used LAMMPS 10 September 2025 with the MACE pair style.

The reference model used batch size 2, double precision, 300 epochs, an initial
learning rate of 5e-4, and stochastic weight averaging from epoch 225. The
committee and grouped-E0 runs used batch size 4, 300 epochs, an initial learning
rate of 1e-3, and the same epoch-225 transition; committee runs used single
precision and the grouped-E0 run used double precision. Production MD used a
1 fs timestep, 10 ps equilibration, a 400 K Nose-Hoover NVT thermostat with a
0.1 ps damping time, and unwrapped-coordinate Li MSD with collective Li
center-of-mass drift removal.

The grouped-E0 estimator used foundation-model predictions on all 263 grouped
training configurations. Its accepted log records a full-rank 3/3 elemental fit
and final Li/C/Si baseline offsets of -3.271318, -1.246324, and -1.280346 eV;
these are model offsets rather than isolated-atom energies. The qualitative
snapshot DFT stress tests used spin-polarized PAW-PBE, ENCUT = 520 eV,
EDIFF = 1e-6 eV, Gaussian smearing (ISMEAR = 0, SIGMA = 0.05 eV),
PREC = Accurate, LREAL = False, ALGO = Normal, ISYM = 0, LASPH, ADDGRID,
IBRION = -1, NSW = 0, and Gamma-only 1 x 1 x 1 sampling. They did not add an
explicit dispersion or dipole correction.

## Rebuild And Verify

From the full evidence workspace:

```bash
python review_revision/build_fair_submission_data.py
python review_revision/build_fair_submission_data.py --check
```

`MANIFEST.sha256` records the hash of every package file. Exported CSV and log
paths are sanitized to remove machine-specific absolute prefixes.

## Release Gate

The repository MIT license covers workflow and analysis software. Before
public release, the authors must explicitly select and record a license for the
curated scientific data, then publish this directory through a public
versioned GitHub release, Zenodo DOI, or equivalent repository. Until that
author decision is made, this directory is release-ready but not a completed
FAIR deposit.

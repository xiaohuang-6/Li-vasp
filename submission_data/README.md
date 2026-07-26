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

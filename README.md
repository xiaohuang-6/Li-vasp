# Li-MACE Graphene Anode Workflow

This repository contains a reproducible computational workflow for studying
local lithium energetics and machine-learning molecular dynamics in defective
graphene, a pristine benchmark, and a small Si4-graphene motif. The project
combines VASP DFT labels, MACE foundation-model fine-tuning, LAMMPS-MACE
molecular dynamics, and review-driven validation scripts.

The repository is intentionally code-first. Large generated data, licensed VASP
POTCAR files, raw trajectories, model checkpoints, logs, TeX build products,
and local archive bundles are not tracked. The manuscript source and curated
figures are tracked so the current paper draft can be reviewed on GitHub.

## Why This Project Is Interesting

Lithium transport near graphene defects is a compact but demanding test case for
modern machine-learning interatomic potentials. Defects alter adsorption
energetics, local reconstruction, and Li mobility, while Si decoration adds a
chemically heterogeneous environment. This project is designed to make those
questions testable with a transparent DFT-to-MACE-to-LAMMPS pipeline rather than
opaque one-off scripts.

The current codebase emphasizes:

- reproducible atomistic structure generation for pristine, vacancy,
  Stone-Wales, and Si4-graphene systems;
- deterministic VASP input generation and OUTCAR parsing into MACE-compatible
  `extxyz` datasets;
- MACE foundation-model fine-tuning without brittle layer-index freezing;
- explicit conversion of fine-tuned MACE models for LAMMPS;
- CPU LAMMPS-MACE smoke tests/scaling tests and local-GPU package workflows for
  MACE/LAMMPS validation;
- conservative review-response workflows for CI-NEB, model evaluation, and
  uncertainty checks.

Cluster GPU submission is disabled. Any future GPU calculation must be packaged
for manual execution on the local RTX 5080 workstation with an explicit
wall-clock budget below 24 hours.

## Start Here

For AI agents and collaborators reproducing the current report outputs, read:

- `AGENT_REPRODUCE_REPORT.md`: exact staged workflow and submission commands.
- `AGENT_PROJECT_STATUS.md`: current evidence boundaries and claim limits.
- `review_revision/README_REVIEW_FIXES.md`: validation jobs needed before strong
  kinetic claims.
- `submission_data/README.md`: curated 273-frame dataset splits, manuscript
  evidence tables, and the SHA256 manifest intended for public deposition.
- `skills/li-mace-reproduction/SKILL.md`: compact agent skill for this project.

## Repository Layout

Core setup and data generation:

- `setup_env.sh`: create the `mace_md` Conda environment.
- `download_mace.py`: download the MACE-MPA-0 medium foundation model.
- `build_defect_structures.py`: generate initial VASP POSCAR structures.
- `prepare_vasp_jobs.py`: create VASP relaxation job folders.
- `vasp_to_extxyz.py`: parse VASP OUTCAR files into MACE `extxyz`.
- `generate_li_sampling_structures.py`: generate Li adsorption/path sampling
  structures from relaxed slabs.
- `build_mace_datasets.py`: build train/valid/test MACE datasets.

MACE and LAMMPS:

- `inspect_mace_model.py`: inspect foundation-model parameter groups before
  fine-tuning.
- `run_finetune.sh`: run MACE fine-tuning with LR-factor freezing of the
  foundation backbone.
- `convert_model_for_lammps.py`: convert MACE `.model` files to LAMMPS
  TorchScript models.
- `build_lammps_data.py`: generate replicated LAMMPS data files.
- `install_lammps_mace_cpu.sh`: build CPU LAMMPS-MACE.
- `install_lammps_mace_gpu.sh`: deprecated cluster-GPU guard; use the local
  5080 packages for GPU builds/runs.
- `in.lammps_diffusion`, `in.lammps_short_cpu`, `in.lammps_scaling_cpu`: LAMMPS
  inputs for MD and performance testing.

Slurm workflows:

- `submit_cpu_data_prep.slurm`: CPU structure generation.
- `submit_gpu_finetune.slurm`: deprecated cluster-GPU guard; GPU fine-tuning
  must run from the local 5080 package/workflow.
- `submit_gpu_lammps.slurm`: deprecated cluster-GPU guard; GPU MD must run from
  the local 5080 package/workflow.
- `submit_cpu_short_md_array.slurm`: short CPU MD smoke array.
- `submit_cpu_lammps_scaling*.slurm`: CPU scaling tests.
- `review_revision/*.slurm`: review-driven CPU NEB/DFT workflows plus disabled
  cluster-GPU guard scripts.

Report post-processing:

- `report_postprocess.py`: regenerate report tables, diagnostic figures, a
  concise results brief, and a manifest from local VASP/MACE/LAMMPS outputs.

## Reproducibility Policy

This repository should remain lightweight and inspectable. Do not commit:

- `dft_outputs/`, `dft_sp_outputs/`, `logs/`, `lammps_logs/`, `trajectories/`,
  `restarts/`, `results/`, `models/`, `benchmarks/`, or `data/` outputs;
- VASP `POTCAR`, `WAVECAR`, `CHGCAR`, `OUTCAR`, `vasprun.xml`, and related
  licensed or heavy files;
- local run packs, zip/tar archives, and TeX build products.

Manuscript source files and curated manuscript figures under `manuscript/` are
tracked deliberately. The compact, sanitized `submission_data/` package is also
tracked deliberately; its `MANIFEST.sha256` provides file-level integrity
checks. A public release must declare a data license before submission.

The workflow regenerates these artifacts from source scripts. If a small
reference dataset is needed later, add it deliberately under a documented
`examples/` or release asset path rather than mixing it with live outputs.

## Minimal Smoke Test

On the cluster:

```bash
cd /home/xh121/Li-vasp
bash -n *.sh submit_*.slurm review_revision/*.slurm
python -m py_compile *.py review_revision/*.py
```

Then follow `AGENT_REPRODUCE_REPORT.md` for the full staged run.

## Scientific Status

The current workflow can reproduce the screening/report package, but the
project is deliberately conservative about claims:

- fixed-geometry path scans are not CI-NEB migration barriers;
- wrapped-coordinate Li displacement is not a diffusion coefficient;
- short MLMD smoke tests are not converged ns-scale diffusion;
- a single fine-tuned MACE checkpoint is not enough for strong transferability
  claims without foundation-model comparison and committee/uncertainty checks.

The `review_revision/` workflow directly targets these gaps.

## References

- MACE fine-tuning documentation:
  https://mace-docs.readthedocs.io/en/latest/guide/finetuning.html
- MACE LAMMPS documentation:
  https://mace-docs.readthedocs.io/en/latest/guide/lammps.html
- MACE ML-IAP documentation:
  https://mace-docs.readthedocs.io/en/latest/guide/lammps_mliap.html
- LAMMPS KOKKOS documentation:
  https://docs.lammps.org/Speed_kokkos.html

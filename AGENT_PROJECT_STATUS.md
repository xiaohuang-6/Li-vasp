# Agent Project Status

Last updated: 2026-07-21

This file is the first handoff document for collaborators and coding agents.
It summarizes the current computational state of the Li-MACE defective graphene
project without relying on local chat history.

## Repository Scope

Track in GitHub:

- Source code, reusable workflow scripts, Slurm submission scripts, and
  lightweight markdown documentation.
- Review-response computational scripts under `review_revision/`.

Do not track in GitHub:

- Manuscript drafts, manuscript figures, publication archives, or compiled
  LaTeX outputs.
- VASP outputs, LAMMPS trajectories, logs, restart files, trained model
  checkpoints, local 3060Ti run packs, generated datasets, or licensed POTCAR
  files.

## Current Evidence State

- The core workflow scaffold exists: structure generation, VASP job
  preparation, OUTCAR parsing, MACE fine-tuning, LAMMPS model conversion, LAMMPS
  data generation, and Slurm wrappers for CPU/GPU partitions.
- The data-expansion workflow exists in `README_DATA_EXPANSION.md` and includes
  Li sampling structures, VASP single-point job preparation, job monitoring, and
  train/valid/test dataset construction.
- A local final MACE dataset and local 3060Ti fine-tuned model have been
  generated outside the GitHub-tracked file set. Treat these as local
  reproducibility artifacts until checks are rerun and summarized in tracked
  result tables.
- Short CPU LAMMPS-MACE tests have been used for workflow smoke testing. These
  runs are not enough to support production diffusion coefficients or kinetic
  claims.
- Review-driven follow-up scripts have been added for four missing validation
  classes: foundation-vs-fine-tuned MACE evaluation, multi-seed committee
  training, unwrapped-coordinate MD, and VASP CI-NEB templates.

## Scientific Claim Boundaries

Do not claim the following until the corresponding computations are complete:

- Do not call fixed-geometry Li path scans migration barriers. They are only
  local path energy spans until relaxed CI-NEB calculations finish.
- Do not use wrapped-coordinate Li displacement as a diffusion coefficient.
  Production MD must dump unwrapped coordinates and image flags.
- Do not interpret high energy drift in monovacancy or divacancy MD as confirmed
  physical reconstruction without DFT checks and model uncertainty analysis.
- Do not describe the Si-containing toy motif as a full Si-graphene composite
  anode. It is a small Si4-graphene motif.
- Do not rely on one fine-tuned MACE checkpoint alone for strong kinetic
  conclusions. Compare against the foundation model and preferably train a
  small committee.

## Recommended Submission Order

The CPU VASP CI-NEB tasks do not depend on the GPU jobs and can be submitted
before or while GPU tasks wait in queue.

1. Prepare CI-NEB templates after setting the real PAW_PBE root:

   ```bash
   cd /home/xh121/Li-vasp
   conda activate mace_md
   python review_revision/prepare_review_neb_jobs.py --potcar-root /path/to/potpaw_PBE
   N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
   sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
   ```

   Remove `%2` if the queue can tolerate all NEB jobs at once.

2. Run foundation-vs-fine-tuned MACE evaluation on GPU:

   ```bash
   sbatch review_revision/submit_gpu_review_mace_eval.slurm
   ```

3. Run a short unwrapped MD smoke test on GPU:

   ```bash
   NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
   ```

4. If the smoke test is stable, run multi-seed review MD:

   ```bash
   NSTEPS=100000 EQUIL_STEPS=10000 DUMP_EVERY=100 sbatch review_revision/submit_gpu_review_md_array.slurm
   ```

5. If MD-based conclusions will remain in the paper, train the review committee:

   ```bash
   sbatch review_revision/submit_gpu_review_committee_train.slurm
   ```

## Key Files

- `README.md`: base end-to-end workflow.
- `README_DATA_EXPANSION.md`: VASP single-point expansion and dataset build
  workflow.
- `build_defect_structures.py`: starting defective graphene structures.
- `prepare_vasp_jobs.py`: VASP relaxation job folders.
- `vasp_to_extxyz.py`: OUTCAR-to-extxyz conversion.
- `build_mace_datasets.py`: train/valid/test dataset builder.
- `run_finetune.sh`: MACE fine-tuning entrypoint.
- `convert_model_for_lammps.py`: MACE-to-LAMMPS model conversion.
- `build_lammps_data.py`: replicated LAMMPS data generation.
- `review_revision/README_REVIEW_FIXES.md`: validation-task details.
- `review_revision/prepare_review_neb_jobs.py`: CI-NEB job template builder.
- `review_revision/evaluate_mace_on_splits.py`: model error and parity data.
- `review_revision/in.lammps_review_unwrapped_md`: MD input with unwrapped dumps.

## Handoff Checklist

Before a collaborator makes claims from new runs, verify:

- VASP jobs finished with `General timing` and parse successfully.
- `data/mace_datasets/li_mace_dataset_report.json` reports expected frame counts
  and no skipped OUTCARs.
- MACE evaluation reports separate energy and force errors for train, valid,
  and test splits.
- LAMMPS logs show no lost atoms, no runaway energy drift, and expected atom
  counts.
- MD post-processing uses unwrapped coordinates and discards equilibration.
- CI-NEB endpoints are chemically sensible and were built with the same
  pseudopotential, spin, vdW, and dipole settings intended for final reporting.

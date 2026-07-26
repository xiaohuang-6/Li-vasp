# Agent Project Status

Last updated: 2026-07-26

This file is the first handoff document for collaborators and coding agents.
It summarizes the current computational state of the Li-MACE defective graphene
project without relying on local chat history.

## Repository Scope

Track in GitHub:

- Source code, reusable workflow scripts, Slurm submission scripts, and
  lightweight markdown documentation.
- Review-response computational scripts under `review_revision/`.
- Manuscript source files and curated manuscript figures under `manuscript/`
  when the user requests GitHub manuscript updates.

Do not track in GitHub:

- Publication archives, local run packs, compiled PDFs, and generated LaTeX
  build outputs.
- VASP outputs, LAMMPS trajectories, logs, restart files, trained model
  checkpoints, local 3060Ti run packs, generated datasets, or licensed POTCAR
  files.

## Current Evidence State

- The core workflow scaffold exists: structure generation, VASP job
  preparation, OUTCAR parsing, MACE fine-tuning, LAMMPS model conversion, LAMMPS
  data generation, CPU Slurm wrappers, and local-GPU transfer/package
  workflows.
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
- Review-driven follow-up scripts have been added for missing validation
  classes: foundation-vs-fine-tuned MACE evaluation, grouped-E0 retraining,
  snapshot force evaluation, unwrapped-coordinate MD, and VASP CI-NEB
  templates. Cluster GPU entry points are disabled; GPU work must be run from
  local 5080 packages.
- The local RTX 5080 reviewer follow-up package
  `local_5080_referee_followup_pack_20260725_1825.tar.gz` has been run and
  returned. Accepted cleaned outputs are in
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/`;
  the returned archive SHA256 is
  `35ac20123795f978c64ee7a5266eba1e96c40a9ca954da99be742e0039edb0d2`.
- The grouped-E0 model and LAMMPS TorchScript model were produced on the local
  RTX 5080. Direct snapshot-force evaluation over the nine initial-campaign
  high-displacement DFT snapshots is complete for foundation MACE-MPA-0, the
  earlier 3060Ti fine-tuned model, and the grouped-E0 model.
- PBE-D3/dipole adsorption-energy single points are complete for all five
  families: 11/11 component jobs usable, 0 fatal markers, and 5/5 family-level
  `E_ads` values usable as single-geometry adsorption anchors.

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
- Do not treat the accepted grouped-E0 snapshot-force result as proof of a
  high-displacement transport mechanism. It improves D Si4-graphene force RMSE
  to 113.6 meV/A over six snapshots, but B1 monovacancy remains poor at
  1107.0 meV/A over three snapshots.

## Recommended Submission Order

The CPU VASP CI-NEB tasks do not depend on GPU diagnostics. Submit only CPU
jobs on the cluster. Do not submit GPU jobs on the cluster; any new GPU work
requires a bounded local RTX 5080 package and manual local execution.

1. Prepare CI-NEB templates after setting the real PAW_PBE root:

   ```bash
   cd /home/xh121/Li-vasp
   conda activate mace_md
   python review_revision/prepare_review_neb_jobs.py --potcar-root /path/to/potpaw_PBE
   N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
   sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
   ```

   Remove `%2` if the queue can tolerate all NEB jobs at once.

2. Continue monitoring only the active 24h CPU reviewer follow-up arrays with:

   ```bash
   cd /home/xh121/Li-vasp
   review_revision/check_reviewer_jobs.sh
   ```

   The remaining manuscript gates are formally converged NEB barriers and
   production-trajectory high-displacement DFT snapshot checks.

3. For any future GPU work, prepare a new local RTX 5080 package with an
   explicit under-24h runner and return-package instructions. Do not use cluster
   GPU partitions for reviewer follow-up.

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
- `review_revision/evaluate_mace_snapshot_forces.py`: direct MACE-vs-DFT
  force evaluator for high-displacement snapshots.
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

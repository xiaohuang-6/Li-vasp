# Review-Driven Computational Follow-Up

This directory contains reusable scripts for the validation work needed before
the project can make strong kinetic or diffusion claims. It intentionally does
not contain manuscript drafts, manuscript figures, generated trajectories, model
checkpoints, or VASP/LAMMPS output data.

## Purpose

The current evidence is enough to show that the pipeline can run, but not enough
to claim final Li diffusion mechanisms. The missing work is computational:

- Real migration barriers require relaxed endpoints and CI-NEB, not fixed-path
  energy scans.
- Diffusion analysis requires unwrapped coordinates, equilibration removal,
  multiple seeds, and Li/time-origin averaging.
- MACE credibility requires held-out test errors, foundation-model comparison,
  and preferably a small committee or uncertainty check.

## Files

- `prepare_review_neb_jobs.py`: creates VASP CI-NEB job folders from existing Li
  path endpoints.
- `submit_cpu_review_neb_array.slurm`: runs the generated VASP NEB folders on
  the CPU partition.
- `evaluate_mace_on_splits.py`: evaluates a MACE model on train/valid/test
  extxyz splits and writes summary/parity CSV files.
- `submit_gpu_review_mace_eval.slurm`: compares the fine-tuned model against
  the foundation model on GPU.
- `submit_gpu_review_committee_train.slurm`: launches a small multi-seed MACE
  fine-tuning committee.
- `in.lammps_review_unwrapped_md`: LAMMPS input that dumps wrapped and unwrapped
  coordinates plus image flags.
- `submit_gpu_review_md_array.slurm`: runs 5 structures x 3 seeds for unwrapped
  review MD on the GPU partition.

## CPU CI-NEB Workflow

Prepare the templates only after setting the real licensed PAW_PBE root:

```bash
cd /home/xh121/Li-vasp
conda activate mace_md
python review_revision/prepare_review_neb_jobs.py --potcar-root /path/to/potpaw_PBE
N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
echo "NEB jobs: $N"
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
```

Use `%2` or another concurrency cap when the CPU queue is crowded. Remove the
cap only if it is acceptable to start every NEB job at once.

Generated folders under `review_revision/neb_jobs/` are ignored by Git because
they contain run-specific POSCAR/POTCAR/job data. Regenerate them as needed.

## GPU Validation Workflow

Run the model evaluator first because it is relatively small:

```bash
cd /home/xh121/Li-vasp
sbatch review_revision/submit_gpu_review_mace_eval.slurm
```

Run a short MD smoke test before production-length runs:

```bash
NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
```

If stable, run the default 100 ps production jobs:

```bash
sbatch review_revision/submit_gpu_review_md_array.slurm
```

Train the committee if MD conclusions will be retained:

```bash
sbatch review_revision/submit_gpu_review_committee_train.slurm
```

## Output Locations

Expected generated outputs are local-only and ignored by Git:

- `review_revision/neb_jobs/`
- `results/review_revision/`
- `trajectories/review_revision/`
- `review_revision/md_outputs/`
- `review_revision/md_logs/`
- `models/review_revision/`

## Acceptance Checks

Before using the results scientifically:

- Confirm every VASP NEB job finished normally and did not stop at an
  unconverged electronic step.
- Confirm the MACE evaluator reports errors for train, validation, and test
  splits for both foundation and fine-tuned models.
- Confirm MD logs show no lost atoms and no runaway energy drift.
- Confirm MSD or displacement analysis uses unwrapped coordinates, not wrapped
  coordinates.
- Confirm any reported barrier is from CI-NEB, not from the fixed-geometry path
  scan used for rapid screening.

# Reviewer-Revision Submission Sequence

This file records the intended order for running the reviewer-revision calculations. CPU VASP jobs and GPU MACE/LAMMPS jobs are independent enough that the CPU validation jobs can be submitted before GPU jobs.

## 0. Refresh Current Status

Before submitting anything, check whether equivalent jobs are already running:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
squeue -u "$USER"
```

Do not resubmit an array index whose job directory already has an active `vasp.log` unless you intentionally restart it with the appropriate restart flag.

## 1. CPU CI-NEB Jobs

Prepare NEB folders only after replacing the POTCAR root with the real licensed PAW_PBE path:

```bash
cd /home/xh121/Li-vasp
conda activate mace_md
python review_revision/prepare_review_neb_jobs.py --potcar-root /real/path/to/potpaw_PBE
N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
echo "NEB jobs: $N"
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
```

For time-critical jobs that have not started yet, use the full-node launcher on selected indices only:

```bash
sbatch --array=4-9%1 review_revision/submit_cpu_review_neb_fullnode_array.slurm
```

## 2. GPU MACE Evaluation And MD

Run the evaluator before MD because it is the fastest check of whether the copied-back fine-tuned model is better than the foundation model:

```bash
cd /home/xh121/Li-vasp
sbatch review_revision/submit_gpu_review_mace_eval.slurm
```

Run a short unwrapped-MD smoke test:

```bash
NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
```

If that passes, run the 100 ps unwrapped-MD array:

```bash
sbatch review_revision/submit_gpu_review_md_array.slurm
```

Train the three-seed committee if committee uncertainty will be reported:

```bash
sbatch review_revision/submit_gpu_review_committee_train.slurm
```

## 3. MD Snapshot DFT Checks

After unwrapped MD has produced trajectories, prepare high-displacement snapshot checks:

```bash
cd /home/xh121/Li-vasp
conda activate mace_md
python review_revision/prepare_md_snapshot_dft_checks.py --top-runs 3 --snapshots-per-run 2 --also-final
N=$(wc -l < review_revision/md_snapshot_dft_jobs/md_snapshot_dft_job_list.txt)
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_md_snapshot_dft_array.slurm
```

If the default 16-rank jobs are too slow, submit not-yet-started indices with 32 ranks and 192 GB:

```bash
sbatch -J li-md-dft32 --ntasks=32 --mem=192G --array=0-$((N-1))%2 \
  review_revision/submit_cpu_md_snapshot_dft_array.slurm
```

## 4. Collect Results

Collect partial status at any time:

```bash
python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_current
python review_revision/collect_md_snapshot_dft_checks.py \
  --output-dir results/review_revision/md_snapshot_dft_analysis_current
```

Only use final NEB barriers in the manuscript if the NEB collector reports formal convergence. Only use MD snapshot DFT energies if the snapshot collector reports both `completed = True` and `electronic_converged_marker = True`.

## 5. Current Conservative Route

The active manuscript does not depend on pending NEB or snapshot-DFT jobs. If those jobs do not finish in time, submit the conservative manuscript version that withholds migration barriers, converged diffusion coefficients, and practical anode-performance claims.

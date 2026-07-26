# Reviewer-Revision Submission Sequence

This file records the intended order for running the reviewer-revision
calculations. CPU VASP jobs may run on the cluster. Reviewer follow-up GPU work
must not be submitted on the cluster. The current local RTX 5080 follow-up
package has already been run and accepted; future GPU work requires a new
bounded local 5080 package.

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

## 2. Local RTX 5080 GPU Diagnostics

Do not submit `review_revision/submit_gpu_*.slurm` scripts. Those reviewer GPU
Slurm entry points are disabled so that automatic continuations do not submit
work to the cluster GPU partition.

The active 24h reviewer follow-up package was:

```text
/home/xh121/Li-vasp/local_5080_referee_followup_pack_20260725_1825.tar.gz
```

Expected SHA256:

```text
eed07f8d599df605c679fb1a6bdeb30f050fd515f3a5c2098b9fb02843a25174
```

It returned
`incoming_gpu_results/local_5080_referee_followup_results_20260725_2309.tar.gz`
with SHA256
`35ac20123795f978c64ee7a5266eba1e96c40a9ca954da99be742e0039edb0d2`.
Accepted cleaned outputs are in
`results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/`.
For any future GPU task, create a new local 5080 package with an explicit
under-24h runner and result-return instructions.

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
cd /home/xh121/Li-vasp
bash review_revision/check_reviewer_jobs.sh
```

The unified checker refreshes adsorption single points, fast NEB, full NEB, the
initial-campaign snapshot checks, and the production-trajectory snapshot
checks. The adsorption-energy collector now marks all five family-level values
usable as single-geometry PBE-D3/dipole anchors. Only use final NEB barriers or
production-trajectory MD snapshot DFT energies in the manuscript if the
corresponding collector marks the rows usable.

## 5. Current Conservative Route

The active manuscript does not depend on pending NEB or snapshot-DFT jobs. If those jobs do not finish in time, submit the conservative manuscript version that withholds migration barriers, converged diffusion coefficients, and practical anode-performance claims.

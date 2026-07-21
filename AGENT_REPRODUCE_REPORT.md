# Agent Reproduction Guide

This guide is written for an AI coding agent running inside the project root.
Follow it to regenerate the current report artifacts from source scripts without
using any checked-in logs, trajectories, VASP outputs, model checkpoints, or
manuscript drafts.

## Non-Negotiable Rules

- Do not commit generated data or manuscript drafts.
- Do not commit licensed VASP `POTCAR` files.
- Use Slurm for CPU and GPU jobs on the cluster.
- Treat `results/`, `data/`, `dft_outputs/`, `dft_sp_outputs/`, `logs/`,
  `lammps_logs/`, `trajectories/`, `restarts/`, `models/`, and `benchmarks/` as
  local generated directories.
- Stop and report if VASP, POTCAR roots, CUDA, MACE, or LAMMPS-MACE are missing.

## Required Inputs

Set these variables before running:

```bash
export PROJECT_ROOT=/home/xh121/Li-vasp
export PATH=/usr/local/slurm/bin:$PATH
export CONDA_BASE=/home/xh121/anaconda3
export POTCAR_ROOT=/path/to/potpaw_PBE
```

`POTCAR_ROOT` must contain subdirectories such as `C/POTCAR`, `Li_sv/POTCAR`,
and `Si/POTCAR`.

## Stage 0: Static Checks

```bash
cd "$PROJECT_ROOT"
bash -n *.sh submit_*.slurm review_revision/*.slurm
python -m py_compile *.py review_revision/*.py
```

## Stage 1: Environment And Foundation Model

```bash
cd "$PROJECT_ROOT"
bash setup_env.sh
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate mace_md
python download_mace.py --destination models/foundation
```

Expected generated file:

```text
models/foundation/mace-mpa-0-medium.model
```

## Stage 2: Relaxation Structures And VASP Jobs

Generate initial structures:

```bash
sbatch submit_cpu_data_prep.slurm
```

Prepare VASP relaxation folders:

```bash
conda activate mace_md
python prepare_vasp_jobs.py --mode relax --potcar-root "$POTCAR_ROOT"
```

Submit each generated relaxation job, or use a short loop after inspection:

```bash
for d in dft_outputs/*; do
  [ -f "$d/submit_vasp.slurm" ] || continue
  (cd "$d" && sbatch submit_vasp.slurm)
done
```

Completion gate:

```bash
rg "General timing" dft_outputs/*/OUTCAR
```

Every system should have a completed `OUTCAR` and `CONTCAR`.

## Stage 3: Build MACE Dataset

Parse relaxation trajectories:

```bash
conda activate mace_md
python vasp_to_extxyz.py --input-glob "dft_outputs/**/OUTCAR" --output data/train_data.extxyz
bash scripts_extract_relax_frames.sh
```

Generate Li sampling structures:

```bash
bash scripts_generate_li_sampling.sh
```

Prepare and submit fixed-geometry VASP single-point labels:

```bash
bash scripts_prepare_sp_jobs.sh
DRY_RUN=1 bash scripts_submit_sp_jobs.sh
LIMIT=5 bash scripts_submit_sp_jobs.sh
```

After the pilot parses cleanly:

```bash
bash scripts_submit_sp_jobs.sh
python check_sp_jobs.py --jobs-root dft_sp_outputs
```

Completion gate:

```bash
python check_sp_jobs.py --jobs-root dft_sp_outputs --report results/sp_job_status.json
bash scripts_build_mace_datasets.sh
```

Expected generated files:

```text
data/mace_datasets/li_mace_all.extxyz
data/mace_datasets/li_mace_train.extxyz
data/mace_datasets/li_mace_valid.extxyz
data/mace_datasets/li_mace_test.extxyz
data/mace_datasets/li_mace_dataset_report.json
```

## Stage 4: MACE Fine-Tuning

Submit on GPU:

```bash
sbatch submit_gpu_finetune.slurm
```

If GPU queue is unavailable, run only a tiny CPU smoke test before committing to
long CPU training:

```bash
DEVICE=cpu DEFAULT_DTYPE=float32 MAX_NUM_EPOCHS=2 START_SWA=1 CONVERT_FOR_LAMMPS=0 bash run_finetune.sh
```

Completion gate:

```bash
find models -name "*.model" -o -name "*-lammps.pt"
```

## Stage 5: Report Tables And Screening Figures

Run after DFT labels and MACE logs are available:

```bash
conda activate mace_md
python report_postprocess.py --output-dir results/report
```

Expected generated files include:

```text
results/report/SUMMARY.md
results/report/REPORT_RESULTS_BRIEF.md
results/report/RESULTS_MANIFEST.json
results/report/dataset_summary.json
results/report/site_energy_rankings.csv
results/report/path_barriers.csv
results/report/path_profiles.csv
results/report/site_energy_rankings.png
results/report/path_profiles.png
```

## Stage 6: LAMMPS-MACE MD And Post-Processing

Build LAMMPS data files:

```bash
bash scripts_prepare_two_day_lammps_data.sh
```

Run a short CPU smoke/stability array if GPU is unavailable:

```bash
sbatch submit_cpu_short_md_array.slurm
```

Run scaling if deciding whether CPU MD is acceptable:

```bash
sbatch submit_cpu_lammps_scaling_flexible.slurm
```

For review-quality MD, use GPU unwrapped-coordinate runs:

```bash
NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
NSTEPS=100000 EQUIL_STEPS=10000 DUMP_EVERY=100 sbatch review_revision/submit_gpu_review_md_array.slurm
```

Post-process short MD outputs:

```bash
conda activate mace_md
python report_postprocess.py --output-dir results/report
```

## Stage 7: Review-Driven Validation

Run MACE foundation-vs-fine-tuned evaluation:

```bash
sbatch review_revision/submit_gpu_review_mace_eval.slurm
```

Prepare CI-NEB templates:

```bash
conda activate mace_md
python review_revision/prepare_review_neb_jobs.py --potcar-root "$POTCAR_ROOT"
N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
```

Train a small committee if MD-based claims remain:

```bash
sbatch review_revision/submit_gpu_review_committee_train.slurm
```

## Final Acceptance Checklist

Before reporting completion:

- `python check_sp_jobs.py --jobs-root dft_sp_outputs` shows all required
  single-point labels parsed.
- `data/mace_datasets/li_mace_dataset_report.json` exists and reports the
  expected train/valid/test split.
- `results/report/SUMMARY.md` and `RESULTS_MANIFEST.json` exist.
- MD quality notes exist and identify any unstable trajectories.
- Any claimed migration barrier comes from CI-NEB, not fixed-geometry path
  scans.
- Any claimed diffusion coefficient uses unwrapped coordinates, not wrapped
  coordinates.

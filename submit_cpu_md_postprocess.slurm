#!/usr/bin/env bash
#SBATCH -J li-rush-md-post
#SBATCH -p et2_medmem,et3_medmem,et4_medmem,et2,et3,et4,et1_new
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p logs results/two_day_rush/md

# shellcheck disable=SC1091
source /home/xh121/anaconda3/etc/profile.d/conda.sh
conda activate mace_md

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"

python analyze_short_md.py \
    --log-dir lammps_logs/two_day_md \
    --log-glob "*_400K_10000steps.log,*_800K_2000steps.log" \
    --traj-dir trajectories/two_day_md \
    --traj-glob "*_400K_10000steps.lammpstrj,*_800K_2000steps.lammpstrj" \
    --output-dir results/two_day_rush/md \
    --expected-steps 10000

python refresh_current_stable_md.py --also-write-step-label
python write_md_quality_notes.py
python write_paper_results_brief.py
python write_manuscript_results_draft.py
python make_results_manifest.py
bash package_two_day_results.sh

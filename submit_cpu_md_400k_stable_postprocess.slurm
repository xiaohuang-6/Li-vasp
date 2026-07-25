#!/usr/bin/env bash
# Post-process a conservative 400 K stable subset from the in-progress 10 ps
# array. This uses the first 2 ps for A, B2, C, and D, and excludes B1 because
# its 400 K trajectory shows a strong temperature/energy excursion after ~2.4 ps.
#SBATCH -J li-rush-md-400stable
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
mkdir -p logs results/two_day_rush/md_400k_stable2ps

# shellcheck disable=SC1091
source /home/xh121/anaconda3/etc/profile.d/conda.sh
conda activate mace_md

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"

python analyze_short_md.py \
    --log-dir lammps_logs/two_day_md \
    --log-glob "*_400K_10000steps.log" \
    --traj-dir trajectories/two_day_md \
    --traj-glob "*_400K_10000steps.lammpstrj" \
    --output-dir results/two_day_rush/md_400k_stable2ps \
    --expected-steps 2000 \
    --max-step 2000 \
    --exclude-cases B1_Monovacancy

python write_md_quality_notes.py
python write_paper_results_brief.py
python write_manuscript_results_draft.py
python make_results_manifest.py

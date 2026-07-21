#!/usr/bin/env bash
# Rerun review-required MD with unwrapped coordinates and multiple seeds.
#
# Submit:
#   sbatch review_revision/submit_gpu_review_md_array.slurm
#
# Optional overrides:
#   NSTEPS=100000 EQUIL_STEPS=10000 TEMPERATURE=400 sbatch review_revision/submit_gpu_review_md_array.slurm

#SBATCH -J li-review-md
#SBATCH -p et_gpu
#SBATCH --array=0-14
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace/build-gpu/install/bin/lmp}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-gpu}"
MODEL="${MODEL:-${PROJECT_ROOT}/local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt}"
TEMPERATURE="${TEMPERATURE:-400}"
NSTEPS="${NSTEPS:-100000}"
EQUIL_STEPS="${EQUIL_STEPS:-10000}"
DUMP_EVERY="${DUMP_EVERY:-100}"

CASES=(A_Perfect B1_Monovacancy B2_Divacancy C_StoneWales D_SiGraphene)
SEEDS=(20260427 20260428 20260429)
CASE_INDEX=$((SLURM_ARRAY_TASK_ID % ${#CASES[@]}))
SEED_INDEX=$((SLURM_ARRAY_TASK_ID / ${#CASES[@]}))
CASE="${CASES[$CASE_INDEX]}"
SEED="${SEEDS[$SEED_INDEX]}"
DATA_FILE="${PROJECT_ROOT}/data/lammps/two_day_${CASE}_2x2x1.data"
OUT_TAG="${CASE}_${TEMPERATURE}K_seed${SEED}_${NSTEPS}steps"

cd "${PROJECT_ROOT}"
mkdir -p logs review_revision/md_outputs review_revision/md_logs trajectories/review_revision

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load gcc/12.2.0 cmake/3.26.1 mpi/openmpi-3.1.4_gcc cuda >/dev/null 2>&1 || true
fi

if [[ ! -x "${LAMMPS_BIN}" && -x "${PROJECT_ROOT}/external/lammps-mace/build-gpu/lmp" ]]; then
    LAMMPS_BIN="${PROJECT_ROOT}/external/lammps-mace/build-gpu/lmp"
fi
if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "Missing GPU LAMMPS binary: ${LAMMPS_BIN}" >&2
    echo "Build it first with submit_gpu_install_lammps.slurm or set LAMMPS_BIN." >&2
    exit 1
fi
if [[ ! -f "${MODEL}" ]]; then
    echo "Missing MACE LAMMPS model: ${MODEL}" >&2
    exit 1
fi
if [[ ! -f "${DATA_FILE}" ]]; then
    echo "Missing data file: ${DATA_FILE}" >&2
    exit 1
fi

export LD_LIBRARY_PATH="${PROJECT_ROOT}/external/lammps-mace/build-gpu/install/lib:${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

echo "case=${CASE}"
echo "seed=${SEED}"
echo "temperature=${TEMPERATURE}"
echo "equil_steps=${EQUIL_STEPS}"
echo "production_steps=${NSTEPS}"
echo "out_tag=${OUT_TAG}"
echo "node=$(hostname)"
nvidia-smi || true
"${LAMMPS_BIN}" -h | grep -i mace

mpirun -np 1 "${LAMMPS_BIN}" -k on g 1 -sf kk \
    -var case "${CASE}" \
    -var data_file "${DATA_FILE}" \
    -var mace_model "${MODEL}" \
    -var temperature "${TEMPERATURE}" \
    -var nsteps "${NSTEPS}" \
    -var equil_steps "${EQUIL_STEPS}" \
    -var dump_every "${DUMP_EVERY}" \
    -var seed "${SEED}" \
    -var out_tag "${OUT_TAG}" \
    -in review_revision/in.lammps_review_unwrapped_md

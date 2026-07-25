#!/usr/bin/env bash
# Reviewer task 3b: unwrapped-coordinate MD for 5 structures x 3 seeds.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

ENV_NAME="${ENV_NAME:-mace_review_5080}"
if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base)"
    # shellcheck disable=SC1091
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate "${ENV_NAME}" || true
fi

LAMMPS_BIN="${LAMMPS_BIN:-${ROOT}/external/lammps-mace/build-5080/install/bin/lmp}"
if [[ ! -x "${LAMMPS_BIN}" && -x "${ROOT}/external/lammps-mace/build-5080/lmp" ]]; then
    LAMMPS_BIN="${ROOT}/external/lammps-mace/build-5080/lmp"
fi
if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "Missing LAMMPS_BIN=${LAMMPS_BIN}" >&2
    echo "Run environment/build_lammps_mace_5080.sh or set LAMMPS_BIN=/path/to/lmp with ML-MACE enabled." >&2
    exit 1
fi

MODEL="${MODEL:-${ROOT}/models/finetuned_reference/li_mace_v1_3060ti.model-lammps.pt}"
TEMPERATURE="${TEMPERATURE:-400}"
NSTEPS="${NSTEPS:-100000}"
EQUIL_STEPS="${EQUIL_STEPS:-10000}"
DUMP_EVERY="${DUMP_EVERY:-100}"
CASE_LIST="${CASE_LIST:-A_Perfect B1_Monovacancy B2_Divacancy C_StoneWales D_SiGraphene}"
SEED_LIST="${SEED_LIST:-20260427 20260428 20260429}"

mkdir -p logs review_revision/md_outputs review_revision/md_logs review_revision/restarts trajectories/review_revision

if python - <<'PY' >/tmp/li_mace_torch_lib.txt 2>/dev/null
from pathlib import Path
import torch
print(Path(torch.__file__).resolve().parent / "lib")
PY
then
    TORCH_LIB_DIR="$(cat /tmp/li_mace_torch_lib.txt)"
    export LD_LIBRARY_PATH="${TORCH_LIB_DIR}:${CONDA_PREFIX:-}/lib:${LD_LIBRARY_PATH:-}"
fi

if ! "${LAMMPS_BIN}" -h | grep -qi mace; then
    echo "LAMMPS binary does not report MACE support: ${LAMMPS_BIN}" >&2
    exit 1
fi

nvidia-smi || true
RUNNER=()
if command -v mpirun >/dev/null 2>&1; then
    RUNNER=(mpirun -np 1)
fi

for case in ${CASE_LIST}; do
    data_file="${ROOT}/data/lammps/two_day_${case}_2x2x1.data"
    if [[ ! -s "${data_file}" ]]; then
        echo "Missing data file: ${data_file}" >&2
        exit 1
    fi
    for seed in ${SEED_LIST}; do
        out_tag="${case}_${TEMPERATURE}K_seed${seed}_${NSTEPS}steps"
        echo "Running ${out_tag}"
        "${RUNNER[@]}" "${LAMMPS_BIN}" -k on g 1 -sf kk \
            -var case "${case}" \
            -var data_file "${data_file}" \
            -var mace_model "${MODEL}" \
            -var temperature "${TEMPERATURE}" \
            -var nsteps "${NSTEPS}" \
            -var equil_steps "${EQUIL_STEPS}" \
            -var dump_every "${DUMP_EVERY}" \
            -var seed "${seed}" \
            -var out_tag "${out_tag}" \
            -in review_revision/in.lammps_review_unwrapped_md \
            2>&1 | tee "logs/${out_tag}.driver.log"
    done
done

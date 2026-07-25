#!/usr/bin/env bash
# Four-day sprint task: run selected MD with available committee models.
#
# This tests whether qualitative displacement behavior depends strongly on the
# fine-tuning seed. It is not a substitute for DFT snapshot validation.
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

mkdir -p models/review_revision
shopt -s nullglob
models=(models/review_revision/li_mace_review_seed*.model)
if (( ${#models[@]} == 0 )); then
    echo "No committee .model files found under models/review_revision." >&2
    echo "Run scripts/run_02_committee_train.sh first." >&2
    exit 1
fi

for model in "${models[@]}"; do
    case "${model}" in
        *-lammps.pt|*-mliap_lammps.pt|*_compiled.model|*_stagetwo.model)
            continue
            ;;
    esac
    lammps_model="${model}-lammps.pt"
    if [[ ! -s "${lammps_model}" ]]; then
        echo "Converting ${model} for LAMMPS"
        python convert_model_for_lammps.py "${model}" --format=libtorch --dtype="${DEFAULT_DTYPE:-float32}"
    fi
    if [[ ! -s "${lammps_model}" ]]; then
        echo "Missing converted model after conversion: ${lammps_model}" >&2
        exit 1
    fi

    model_name="$(basename "${model}" .model)"
    echo "Running selected MD with ${model_name}"
    MODEL="${ROOT}/${lammps_model}" \
    CASE_LIST="${CASE_LIST:-D_SiGraphene B1_Monovacancy}" \
    SEED_LIST="${SEED_LIST:-20260427}" \
    NSTEPS="${NSTEPS:-200000}" \
    EQUIL_STEPS="${EQUIL_STEPS:-10000}" \
    DUMP_EVERY="${DUMP_EVERY:-1000}" \
    bash scripts/run_04_review_md_array.sh
done

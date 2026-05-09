#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

PRESET="${1:-10ps}"

case "${PRESET}" in
    100step)
        NSTEPS=100
        DUMP_EVERY=10
        RESTART_EVERY=100
        ;;
    10ps)
        NSTEPS=10000
        DUMP_EVERY=100
        RESTART_EVERY=5000
        ;;
    100ps)
        NSTEPS=100000
        DUMP_EVERY=500
        RESTART_EVERY=25000
        ;;
    1ns)
        NSTEPS=1000000
        DUMP_EVERY=1000
        RESTART_EVERY=100000
        ;;
    3ns)
        NSTEPS=3000000
        DUMP_EVERY=2000
        RESTART_EVERY=100000
        ;;
    *)
        echo "Unknown preset: ${PRESET}" >&2
        echo "Use one of: 100step, 10ps, 100ps, 1ns, 3ns" >&2
        exit 2
        ;;
esac

RUN_LABEL="${RUN_LABEL:-gpu_${PRESET}_$(date +%Y%m%d_%H%M%S)}"

# shellcheck disable=SC1091
source scripts/env_gpu_lammps.sh

mkdir -p logs trajectories restarts data/lammps

if [[ ! -s "${DATA_FILE}" ]]; then
    echo "Missing DATA_FILE=${DATA_FILE}" >&2
    exit 1
fi
if [[ ! -s "${MACE_MODEL}" ]]; then
    echo "Missing MACE_MODEL=${MACE_MODEL}" >&2
    exit 1
fi

ACCEL_ARGS=()
if [[ "${USE_KOKKOS:-0}" == "1" ]]; then
    ACCEL_ARGS=(-k on g 1 -sf kk)
else
    echo "USE_KOKKOS is not set; pair_style mace will use Torch CUDA if available."
fi

echo "Running preset=${PRESET}, nsteps=${NSTEPS}, label=${RUN_LABEL}"
echo "LAMMPS_BIN=${LAMMPS_BIN}"
echo "DATA_FILE=${DATA_FILE}"
echo "MACE_MODEL=${MACE_MODEL}"

"${LAMMPS_BIN}" \
    "${ACCEL_ARGS[@]}" \
    -var data_file "${DATA_FILE}" \
    -var mace_model "${MACE_MODEL}" \
    -var run_label "${RUN_LABEL}" \
    -var nsteps "${NSTEPS}" \
    -var dump_every "${DUMP_EVERY}" \
    -var restart_every "${RESTART_EVERY}" \
    -in inputs/in.gpu_md_template

python scripts/summarize_md.py "logs/${RUN_LABEL}.lammps.log" "trajectories/${RUN_LABEL}.lammpstrj" \
    > "analysis/${RUN_LABEL}.summary.json"

echo "Done. Summary: analysis/${RUN_LABEL}.summary.json"

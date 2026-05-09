#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

RESTART_FILE="${1:-}"
ADDITIONAL_PRESET="${2:-100ps}"

if [[ -z "${RESTART_FILE}" ]]; then
    RESTART_FILE="$(find restarts -maxdepth 1 -type f -name '*.restart' -printf '%T@ %p\n' | sort -nr | awk 'NR==1 {print $2}')"
fi
if [[ -z "${RESTART_FILE}" || ! -s "${RESTART_FILE}" ]]; then
    echo "No restart file found. Pass one explicitly." >&2
    exit 1
fi

case "${ADDITIONAL_PRESET}" in
    100step) NSTEPS=100; DUMP_EVERY=10; RESTART_EVERY=100 ;;
    10ps) NSTEPS=10000; DUMP_EVERY=100; RESTART_EVERY=5000 ;;
    100ps) NSTEPS=100000; DUMP_EVERY=500; RESTART_EVERY=25000 ;;
    1ns) NSTEPS=1000000; DUMP_EVERY=1000; RESTART_EVERY=100000 ;;
    3ns) NSTEPS=3000000; DUMP_EVERY=2000; RESTART_EVERY=100000 ;;
    *)
        echo "Unknown preset: ${ADDITIONAL_PRESET}" >&2
        exit 2
        ;;
esac

RUN_LABEL="${RUN_LABEL:-continue_${ADDITIONAL_PRESET}_$(date +%Y%m%d_%H%M%S)}"

# shellcheck disable=SC1091
source scripts/env_gpu_lammps.sh

ACCEL_ARGS=()
if [[ "${USE_KOKKOS:-0}" == "1" ]]; then
    ACCEL_ARGS=(-k on g 1 -sf kk)
fi

"${LAMMPS_BIN}" \
    "${ACCEL_ARGS[@]}" \
    -var restart_file "${RESTART_FILE}" \
    -var mace_model "${MACE_MODEL}" \
    -var run_label "${RUN_LABEL}" \
    -var nsteps "${NSTEPS}" \
    -var dump_every "${DUMP_EVERY}" \
    -var restart_every "${RESTART_EVERY}" \
    -in inputs/in.gpu_continue_template

python scripts/summarize_md.py "logs/${RUN_LABEL}.lammps.log" "trajectories/${RUN_LABEL}.lammpstrj" \
    > "analysis/${RUN_LABEL}.summary.json"

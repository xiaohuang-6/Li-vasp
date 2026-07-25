#!/usr/bin/env bash
# Run CPU thread scaling tests for LAMMPS-MACE on one allocated et2024 node.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "${PROJECT_ROOT}"

LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace-cpu/bin/lmp}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-cpu}"
DATA_FILE="${DATA_FILE:-${PROJECT_ROOT}/data/lammps/local_D_SiGraphene_2x2x1.data}"
MACE_MODEL="${MACE_MODEL:-${PROJECT_ROOT}/local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt}"
NSTEPS="${NSTEPS:-100}"
THREAD_LIST="${THREAD_LIST:-1 2 4 8 16 32 64}"
OUTDIR="${OUTDIR:-${PROJECT_ROOT}/benchmarks/cpu_scaling_${SLURM_JOB_ID:-manual_$(date +%Y%m%d_%H%M%S)}}"

mkdir -p "${OUTDIR}" benchmarks/cpu_scaling_tmp

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load gcc/12.2.0 cmake/3.26.1 mpi/openmpi-3.1.4_gcc
fi

if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "Missing LAMMPS binary: ${LAMMPS_BIN}" >&2
    exit 1
fi
if [[ ! -s "${DATA_FILE}" ]]; then
    echo "Missing data file: ${DATA_FILE}" >&2
    exit 1
fi
if [[ ! -s "${MACE_MODEL}" ]]; then
    echo "Missing MACE model: ${MACE_MODEL}" >&2
    exit 1
fi

export LD_LIBRARY_PATH="${PROJECT_ROOT}/external/lammps-mace-cpu/lib:${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"

summary="${OUTDIR}/scaling_summary.tsv"
printf "threads\tsteps\tloop_seconds\tsteps_per_second\thours_per_100ps\thours_per_1ns\thours_per_3ns\tlog\n" > "${summary}"

for threads in ${THREAD_LIST}; do
    label="cpu_${threads}t_${NSTEPS}steps"
    log_tmp="${PROJECT_ROOT}/benchmarks/cpu_scaling_tmp/${label}.lammps.log"
    log_final="${OUTDIR}/${label}.lammps.log"

    export OMP_NUM_THREADS="${threads}"
    export MKL_NUM_THREADS="${threads}"
    export OPENBLAS_NUM_THREADS="${threads}"
    export OMP_PROC_BIND=spread
    export OMP_PLACES=cores

    echo "Running ${label} with OMP_NUM_THREADS=${OMP_NUM_THREADS}"
    rm -f "${log_tmp}"

    mpirun -np 1 "${LAMMPS_BIN}" \
        -var data_file "${DATA_FILE}" \
        -var mace_model "${MACE_MODEL}" \
        -var run_label "${label}" \
        -var nsteps "${NSTEPS}" \
        -in in.lammps_scaling_cpu

    cp "${log_tmp}" "${log_final}"

    python - "${threads}" "${NSTEPS}" "${log_final}" "${summary}" <<'PY'
import re
import sys
from pathlib import Path

threads = int(sys.argv[1])
steps = int(sys.argv[2])
log_path = Path(sys.argv[3])
summary_path = Path(sys.argv[4])
text = log_path.read_text(errors="ignore")
match = re.search(r"Loop time of\s+([0-9.]+)", text)
if not match:
    raise SystemExit(f"Loop time not found in {log_path}")
loop = float(match.group(1))
sps = steps / loop if loop > 0 else 0.0
hours_100ps = 100_000 / sps / 3600 if sps > 0 else float("inf")
hours_1ns = 1_000_000 / sps / 3600 if sps > 0 else float("inf")
hours_3ns = 3_000_000 / sps / 3600 if sps > 0 else float("inf")
with summary_path.open("a") as handle:
    handle.write(
        f"{threads}\t{steps}\t{loop:.6f}\t{sps:.6f}\t"
        f"{hours_100ps:.3f}\t{hours_1ns:.3f}\t{hours_3ns:.3f}\t{log_path}\n"
    )
PY
done

column -t -s $'\t' "${summary}" | tee "${OUTDIR}/scaling_summary.pretty.txt"
echo "Scaling benchmark finished: ${OUTDIR}"

#!/usr/bin/env bash
# Submit generated VASP single-point jobs. Use DRY_RUN=1 to preview.
set -euo pipefail

export PATH="/usr/local/slurm/bin:${PATH}"

ROOT="${ROOT:-dft_sp_outputs}"
LIMIT="${LIMIT:-0}"
DRY_RUN="${DRY_RUN:-0}"
ONLY_MISSING="${ONLY_MISSING:-1}"
RESUBMIT="${RESUBMIT:-0}"

submitted=0
for submit in "${ROOT}"/*/submit_vasp.slurm; do
    [[ -f "${submit}" ]] || continue
    job_dir="$(dirname "${submit}")"
    jobid_file="${job_dir}/submitted_jobid.txt"
    if [[ "${ONLY_MISSING}" == "1" && -s "${job_dir}/OUTCAR" ]]; then
        if grep -q "General timing" "${job_dir}/OUTCAR"; then
            echo "skip complete: ${job_dir}"
            continue
        fi
    fi
    if [[ "${RESUBMIT}" != "1" && -s "${jobid_file}" ]]; then
        echo "skip previously submitted: ${job_dir} ($(cat "${jobid_file}"))"
        continue
    fi
    if [[ "${LIMIT}" != "0" && "${submitted}" -ge "${LIMIT}" ]]; then
        break
    fi
    echo "submit: ${job_dir}"
    if [[ "${DRY_RUN}" != "1" ]]; then
        output="$(cd "${job_dir}" && sbatch submit_vasp.slurm)"
        echo "${output}"
        printf "%s\n" "${output}" > "${jobid_file}"
    fi
    submitted=$((submitted + 1))
done

echo "Submitted or previewed ${submitted} jobs from ${ROOT}"

#!/usr/bin/env bash
# Refresh reviewer-response job status and partial result summaries.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
export PATH="/usr/local/slurm/bin:${PATH}"

cd "${PROJECT_ROOT}"

echo "== Time =="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "== Slurm status: reviewer CPU jobs =="
if [[ -n "${REVIEW_JOB_IDS:-}" ]]; then
    squeue -j "${REVIEW_JOB_IDS}" || true
else
    squeue -u "${USER}" -o '%.18i %.24j %.9P %.2t %.12M %.12l %.6D %R' \
        | awk 'NR == 1 || $2 ~ /^(li-review-neb|li-md-dft|li-ads-sp|li-fast-neb|li-fast-neb-end|li-md-dftcheck)/'
fi

echo
echo "== Slurm GPU guard =="
gpu_lines="$(
    squeue -u "${USER}" -h -o '%.18i %.9P %.24j %.8T %.10M %.10l %.6D %R' \
        | awk 'tolower($2 " " $3) ~ /(gpu|li-e0-grouped|li-snap-force)/'
)"
if [[ -n "${gpu_lines}" ]]; then
    echo "WARNING: cluster GPU-related jobs are present; cancel or move them to the local 5080 package."
    echo "${gpu_lines}"
else
    echo "No matching cluster GPU jobs for reviewer follow-up."
fi

echo
echo "== Refresh adsorption-energy single-point results =="
python review_revision/collect_adsorption_energies.py \
    --manifest review_revision/adsorption_energy_jobs/adsorption_manifest.csv \
    --output-dir results/review_revision/adsorption_energy_analysis
sed -n '1,80p' results/review_revision/adsorption_energy_analysis/ADSORPTION_ENERGY_STATUS.md

echo
echo "== Refresh fast NEB partial results =="
python review_revision/collect_neb_results.py \
    --job-list review_revision/neb_fast_jobs/neb_fast_job_list.txt \
    --paths-csv results/two_day_rush/path_barriers.csv \
    --endpoint-mode endpoint_sp \
    --endpoint-manifest review_revision/neb_fast_endpoint_jobs/endpoint_manifest.csv \
    --output-dir results/review_revision/neb_fast_analysis
sed -n '1,80p' results/review_revision/neb_fast_analysis/REVIEW_NEB_STATUS.md

echo
echo "== Refresh full NEB partial results =="
python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_current
sed -n '1,80p' results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md

echo
echo "== Refresh initial-campaign MD snapshot DFT-check results =="
python review_revision/collect_md_snapshot_dft_checks.py --output-dir results/review_revision/md_snapshot_dft_analysis_current
sed -n '1,80p' results/review_revision/md_snapshot_dft_analysis_current/MD_SNAPSHOT_DFT_STATUS.md

echo
echo "== Refresh production-trajectory MD snapshot DFT-check results =="
python review_revision/collect_md_snapshot_dft_checks.py \
    --manifest review_revision/production_md_snapshot_dft_jobs/md_snapshot_dft_manifest.csv \
    --output-dir results/review_revision/production_md_snapshot_dft_analysis
sed -n '1,80p' results/review_revision/production_md_snapshot_dft_analysis/MD_SNAPSHOT_DFT_STATUS.md

echo
echo "== Recent VASP output timestamps =="
python - <<'PY'
from pathlib import Path
import time

for root in [
    Path("review_revision/adsorption_energy_jobs"),
    Path("review_revision/neb_fast_endpoint_jobs"),
    Path("review_revision/neb_fast_jobs"),
    Path("review_revision/neb_jobs"),
    Path("review_revision/md_snapshot_dft_jobs"),
    Path("review_revision/production_md_snapshot_dft_jobs"),
]:
    for job_dir in sorted(path for path in root.glob("*") if path.is_dir()):
        candidates = []
        for pattern in ["vasp.log", "OUTCAR", "OSZICAR", "stdout", "*/OUTCAR", "*/OSZICAR", "*/stdout"]:
            candidates.extend(path for path in job_dir.glob(pattern) if path.is_file())
        if not candidates:
            continue
        newest = max(candidates, key=lambda path: path.stat().st_mtime)
        stat = newest.stat()
        rel = newest.relative_to(job_dir)
        print(f"{job_dir.name}: latest={rel} size={stat.st_size} age_s={time.time() - stat.st_mtime:.1f}")
PY

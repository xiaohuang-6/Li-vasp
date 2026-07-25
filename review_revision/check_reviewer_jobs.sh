#!/usr/bin/env bash
# Refresh reviewer-response job status and partial result summaries.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
export PATH="/usr/local/slurm/bin:${PATH}"

cd "${PROJECT_ROOT}"

echo "== Time =="
date '+%Y-%m-%d %H:%M:%S %Z'

echo
echo "== Slurm status: NEB and MD snapshot DFT checks =="
if [[ -n "${REVIEW_JOB_IDS:-}" ]]; then
    squeue -j "${REVIEW_JOB_IDS}" || true
else
    squeue -u "${USER}" -o '%.18i %.24j %.9P %.2t %.12M %.12l %.6D %R' \
        | awk 'NR == 1 || $2 ~ /^(li-review-neb|li-md-dft)/'
fi

echo
echo "== Refresh NEB partial results =="
python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_current
sed -n '1,80p' results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md

echo
echo "== Refresh MD snapshot DFT-check partial results =="
python review_revision/collect_md_snapshot_dft_checks.py --output-dir results/review_revision/md_snapshot_dft_analysis_current
sed -n '1,80p' results/review_revision/md_snapshot_dft_analysis_current/MD_SNAPSHOT_DFT_STATUS.md

echo
echo "== Recent VASP log timestamps =="
python - <<'PY'
from pathlib import Path
import time

for root in [Path("review_revision/neb_jobs"), Path("review_revision/md_snapshot_dft_jobs")]:
    for path in sorted(root.glob("*/vasp.log")):
        stat = path.stat()
        print(f"{path.parent.name}: size={stat.st_size} age_s={time.time() - stat.st_mtime:.1f}")
PY

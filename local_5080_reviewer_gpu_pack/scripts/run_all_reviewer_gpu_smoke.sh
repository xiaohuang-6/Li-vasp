#!/usr/bin/env bash
# Runs the short reviewer GPU smoke workflow. Full committee/MD are launched separately.
set -euo pipefail

bash environment/check_reviewer_gpu_env.sh
bash scripts/run_01_mace_eval.sh

if [[ "${RUN_MD_SMOKE:-1}" == "1" ]]; then
    bash scripts/run_03_review_md_smoke.sh
fi

echo "Smoke workflow finished. Review results/ and logs/."

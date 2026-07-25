#!/usr/bin/env bash
# Reviewer task 3a: short unwrapped-coordinate MD smoke test on one representative system.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

CASE_LIST="${CASE_LIST:-D_SiGraphene}" \
SEED_LIST="${SEED_LIST:-20260427}" \
NSTEPS="${NSTEPS:-1000}" \
EQUIL_STEPS="${EQUIL_STEPS:-500}" \
DUMP_EVERY="${DUMP_EVERY:-100}" \
bash scripts/run_04_review_md_array.sh

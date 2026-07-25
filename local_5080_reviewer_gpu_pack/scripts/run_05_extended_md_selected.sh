#!/usr/bin/env bash
# Four-day sprint task: selected longer unwrapped MD on RTX 5080.
#
# This is intentionally selective. Longer MACE MD should be used to strengthen
# trends only after the priority DFT snapshot checks do not show obvious
# out-of-domain failures.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

# Defaults: 0.5 ns production, low trajectory output frequency to avoid I/O
# dominating the run. Increase NSTEPS to 1000000 for 1 ns after a short check.
CASE_LIST="${CASE_LIST:-A_Perfect C_StoneWales D_SiGraphene}" \
SEED_LIST="${SEED_LIST:-20260427 20260428 20260429}" \
NSTEPS="${NSTEPS:-500000}" \
EQUIL_STEPS="${EQUIL_STEPS:-10000}" \
DUMP_EVERY="${DUMP_EVERY:-1000}" \
bash scripts/run_04_review_md_array.sh

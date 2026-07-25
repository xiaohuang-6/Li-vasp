#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p data/lammps results/two_day_rush

CASES=(A_Perfect B1_Monovacancy B2_Divacancy C_StoneWales D_SiGraphene)
for case in "${CASES[@]}"; do
    input="dft_outputs/${case}/CONTCAR"
    output="data/lammps/two_day_${case}_2x2x1.data"
    summary="data/lammps/two_day_${case}_2x2x1.summary.json"
    if [[ ! -s "${input}" ]]; then
        echo "Missing optimized structure: ${input}" >&2
        exit 1
    fi
    python build_lammps_data.py \
        --input "${input}" \
        --output "${output}" \
        --repeat 2 2 1 \
        --summary "${summary}" \
        --specorder C Li Si
done

python - <<'PY'
import json
from pathlib import Path
rows = []
for path in sorted(Path("data/lammps").glob("two_day_*_2x2x1.summary.json")):
    rows.append(json.loads(path.read_text()))
Path("results/two_day_rush").mkdir(parents=True, exist_ok=True)
Path("results/two_day_rush/two_day_lammps_data_summary.json").write_text(
    json.dumps(rows, indent=2),
    encoding="utf-8",
)
for row in rows:
    print(f"{row['output']}: {row['formula']} ({row['natoms']} atoms)")
PY

#!/usr/bin/env bash
# Deprecated cluster GPU Slurm entry point.

set -euo pipefail

cat >&2 <<'MSG'
Cluster GPU execution is disabled for this project.

Do not submit this script with sbatch. Run GPU LAMMPS/MACE work only inside the
local RTX 5080 package/workflow. For the active reviewer follow-up, use:

  /home/xh121/Li-vasp/local_5080_referee_followup_pack_20260725_1825.tar.gz

See LOCAL_5080_DOWNLOAD_AND_AGENT_PROMPT.md for download, execution, and return
instructions.
MSG

exit 2

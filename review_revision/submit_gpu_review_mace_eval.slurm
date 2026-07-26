#!/usr/bin/env bash
# Deprecated reviewer GPU Slurm entry point.

set -euo pipefail

cat >&2 <<'MSG'
Cluster GPU execution is disabled for the reviewer follow-up.

Do not submit this script with sbatch. Run GPU diagnostics from the local RTX
5080 package instead:

  /home/xh121/Li-vasp/local_5080_referee_followup_pack_20260725_1825.tar.gz

See LOCAL_5080_DOWNLOAD_AND_AGENT_PROMPT.md for download, execution, and return
instructions.
MSG

exit 2

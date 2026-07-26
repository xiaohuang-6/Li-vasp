# Local 5080 Download And Agent Prompt

## 2026-07-25 Referee Follow-Up Pack

The cluster `et_gpu` reviewer follow-up jobs have been canceled. Use this
package as the only GPU path for the referee follow-up tasks; run it manually
on the local RTX 5080 workstation. This package is targeted to:

- grouped-split MACE fine-tuning with `E0S=estimated`;
- MACE-vs-DFT force evaluation on the nine completed snapshot OUTCAR files.

Download from your local machine:

```bash
scp -P 443 xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/local_5080_referee_followup_pack_20260725_1825.tar.gz .
sha256sum local_5080_referee_followup_pack_20260725_1825.tar.gz
tar -xzf local_5080_referee_followup_pack_20260725_1825.tar.gz
cd local_5080_referee_followup_pack_20260725_1825
```

Expected SHA256:

```text
eed07f8d599df605c679fb1a6bdeb30f050fd515f3a5c2098b9fb02843a25174
```

If your SSH connection does not use port 443, drop `-P 443`.

Prompt for the local AI Agent:

```text
You are running on my local RTX 5080 workstation. Work only inside
local_5080_referee_followup_pack_20260725_1825. Read
README_5080_REFEREE_FOLLOWUP.md and AGENT_PROMPT_5080_REFEREE_FOLLOWUP.md
completely before running commands.

Goal: execute the referee follow-up GPU diagnostics only. Do not redesign the
project, do not edit the manuscript, and do not change scientific claims.

Required commands:
1. conda activate mace_md
2. Check CUDA exactly as shown in AGENT_PROMPT_5080_REFEREE_FOLLOWUP.md.
3. bash scripts/run_all_under_24h_5080.sh

The bounded runner uses a 23h default wall-clock budget, runs baseline snapshot
force evaluation first, attempts grouped E0 fine-tuning only inside the
remaining budget, reruns force evaluation if time remains, and packages outputs
automatically. If CUDA is unavailable, stop and report. If grouped fine-tuning
fails or times out, keep logs and still retain the force-evaluation outputs.
Do not delete outputs.
```

Return results to the cluster:

```bash
rsync -avP -e "ssh -p 443" local_5080_referee_followup_results_*.tar.gz \
  xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/incoming_gpu_results/
```

If SSH does not use port 443, remove `-e "ssh -p 443"`.

Current gate status: no cluster GPU jobs should be submitted for this follow-up.
The initial-campaign DFT snapshot evidence is now 9/9 usable and traceable by
OUTCAR hash. Production-trajectory snapshot DFT checks, adsorption-energy
single points, and NEB jobs are still running or pending on CPU partitions.
The local 5080 diagnostics are model validation only; they do not replace
adsorption energies, final CI-NEB barriers, or converged diffusion statistics.

## 2026-07-24 Four-Day MD Extension Pack

Prepared on 2026-07-24.

## Download Command

From your local machine, run:

```bash
scp -P 443 xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/local_5080_four_day_sci_pack_20260724.tar.gz .
tar -xzf local_5080_four_day_sci_pack_20260724.tar.gz
cd local_5080_reviewer_gpu_pack
```

If your SSH connection does not use port 443, drop `-P 443`.

## Prompt For Local AI Agent

Use this prompt after unpacking the tarball:

```text
You are running on my local RTX 5080 workstation. Please read
FOUR_DAY_5080_AGENT_PROMPT.md, FOUR_DAY_5080_CURRENT_GATE_STATUS.md, and
AGENT_REVIEWER_GPU_GUIDE.md completely before running commands.

Goal: execute only the four-day SCI sprint GPU tasks for the Li-MACE graphene
project. Do not redesign the project and do not change scientific claims.

Required order:
1. Check/create the MACE CUDA environment:
   bash environment/setup_mace_env_5080.sh
   bash environment/check_reviewer_gpu_env.sh
2. Verify or build LAMMPS-MACE. If I provide LAMMPS_BIN, use it; otherwise run:
   bash environment/build_lammps_mace_5080.sh
3. Run smoke MD:
   bash scripts/run_03_review_md_smoke.sh
4. If smoke passes, run selected 0.5 ns extension:
   bash scripts/run_05_extended_md_selected.sh
5. If committee models are available, run:
   bash scripts/run_06_committee_md_selected.sh
   If committee models are missing and there is enough time, run:
   CONVERT_FOR_LAMMPS=1 bash scripts/run_02_committee_train.sh
   bash scripts/run_06_committee_md_selected.sh
6. Summarize:
   python scripts/summarize_reviewer_outputs.py
7. Package outputs for return exactly as instructed in FOUR_DAY_5080_AGENT_PROMPT.md.

Stop and report if torch.cuda.is_available() is false, if LAMMPS does not have
MACE support, if any MD run has LAMMPS ERROR/lost atoms/NaNs, or if temperature
runaway occurs. Do not delete outputs.
```

## Return Results To Cluster

After local runs finish, from the local machine:

```bash
rsync -avP -e "ssh -p 443" local_5080_reviewer_gpu_results_*.tar.gz \
  xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/incoming_gpu_results/
```

If SSH does not use port 443, remove `-e "ssh -p 443"`.

## Current Gate Status

As of the latest cluster check, GPU extension can be run as optional robustness
evidence, but still cannot replace NEB barriers or broader DFT validation:

- CI-NEB: 0 formally converged paths; 1 fatal B2 divacancy path is excluded,
  and the second B2 divacancy path has a huge force diagnostic and is also
  excluded from barrier interpretation.
- MD snapshot DFT: 8 usable converged energies out of 9 prepared checks.
- Therefore longer GPU MD may be run, but it should still be treated as
  robustness/stability evidence, not as a replacement for NEB barriers or a
  converged diffusion coefficient.

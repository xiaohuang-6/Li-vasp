# Local 5080 Download And Agent Prompt

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

# Prompt For Local RTX 5080 AI Agent

You are running on the user's local RTX 5080 workstation. Your task is to run
only the four-day SCI sprint GPU calculations for the Li-MACE graphene project.
Do not redesign the project and do not change the scientific claim boundaries.

## Goal

Run selected longer MACE/LAMMPS MD and optional committee-model MD only after
the environment is verified. These GPU runs are intended to strengthen
qualitative robustness after CPU DFT sanity checks. They do not replace
converged CI-NEB barriers or DFT validation of high-displacement snapshots.

## Required Order

1. Enter the package directory:

```bash
cd local_5080_reviewer_gpu_pack
```

2. Create/check the environment:

```bash
bash environment/setup_mace_env_5080.sh
bash environment/check_reviewer_gpu_env.sh
```

If an environment already exists, still run the checker.

3. Verify or build LAMMPS-MACE:

```bash
export LAMMPS_BIN=/absolute/path/to/lmp
"$LAMMPS_BIN" -h | grep -i mace
```

If no compatible binary exists:

```bash
bash environment/build_lammps_mace_5080.sh
```

4. Read the current gate status:

```bash
cat FOUR_DAY_5080_CURRENT_GATE_STATUS.md
```

5. Run a short smoke test:

```bash
bash scripts/run_03_review_md_smoke.sh
```

6. Run selected 0.5 ns extension:

```bash
bash scripts/run_05_extended_md_selected.sh
```

The default is:

- Cases: `A_Perfect C_StoneWales D_SiGraphene`
- Seeds: `20260427 20260428 20260429`
- Production length: 500000 steps = 0.5 ns
- Equilibration: 10000 steps
- Dump frequency: 1000 steps

7. If committee models exist or after running committee training, run selected
committee-model MD:

```bash
bash scripts/run_06_committee_md_selected.sh
```

If committee models are missing and there is enough time, run:

```bash
CONVERT_FOR_LAMMPS=1 bash scripts/run_02_committee_train.sh
bash scripts/run_06_committee_md_selected.sh
```

8. Summarize outputs:

```bash
python scripts/summarize_reviewer_outputs.py
```

9. Package outputs for return:

```bash
cd ..
tar -czf local_5080_reviewer_gpu_results_$(date +%Y%m%d_%H%M).tar.gz \
  local_5080_reviewer_gpu_pack/results \
  local_5080_reviewer_gpu_pack/review_revision/md_outputs \
  local_5080_reviewer_gpu_pack/review_revision/md_logs \
  local_5080_reviewer_gpu_pack/trajectories/review_revision \
  local_5080_reviewer_gpu_pack/logs \
  local_5080_reviewer_gpu_pack/models/review_revision
```

## Important Scientific Boundary

Do not claim final diffusion coefficients unless the MSD is approximately
linear over a documented fitting window across multiple seeds and the cluster
DFT snapshot checks do not show pathology. Otherwise report these runs as
extended stability/displacement diagnostics only.

## Failure Handling

- If `torch.cuda.is_available()` is false, stop and report the driver/CUDA
  problem.
- If LAMMPS lacks MACE, stop and build LAMMPS-MACE or ask for a compatible
  binary.
- If any MD run has LAMMPS ERROR, lost atoms, NaNs, or runaway temperature,
  keep the logs and do not rerun silently.
- Do not delete intermediate outputs.

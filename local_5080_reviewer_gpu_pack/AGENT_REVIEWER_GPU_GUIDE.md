# AI Agent Guide: RTX 5080 Reviewer GPU Tasks

You are running on a local workstation, expected to have an NVIDIA RTX 5080 or
similar Blackwell GPU. Your job is to execute reviewer-response GPU validation
for the Li-MACE graphene project, not to rerun unrelated exploratory workflows.

## Scope

Run only these GPU tasks:

1. `scripts/run_01_mace_eval.sh`: compare fine-tuned MACE and MACE-MPA-0 on
   train/valid/test splits.
2. `scripts/run_02_committee_train.sh`: train three seed models for uncertainty
   diagnostics.
3. `scripts/run_03_review_md_smoke.sh` then `scripts/run_04_review_md_array.sh`:
   run unwrapped-coordinate LAMMPS-MACE MD.

## Hardware And Software Assumptions

- GPU: RTX 5080, CUDA capability 12.0.
- Recommended NVIDIA driver: recent enough for CUDA 12.8 runtime.
- Python: 3.11.
- PyTorch: CUDA 12.8 wheel from the official PyTorch index.
- MACE: installed from ACEsuit GitHub.
- LAMMPS-MACE: either already installed and passed via `LAMMPS_BIN`, or built
  locally with `environment/build_lammps_mace_5080.sh`.

## Step 0: Unpack

```bash
tar -xzf local_5080_reviewer_gpu_pack.tar.gz
cd local_5080_reviewer_gpu_pack
```

## Step 1: Create Python/MACE Environment

```bash
bash environment/setup_mace_env_5080.sh
bash environment/check_reviewer_gpu_env.sh
```

If the environment name must differ:

```bash
ENV_NAME=my_env_name bash environment/setup_mace_env_5080.sh
ENV_NAME=my_env_name bash environment/check_reviewer_gpu_env.sh
```

## Step 2: Run MACE Evaluation

```bash
bash scripts/run_01_mace_eval.sh
python scripts/summarize_reviewer_outputs.py
```

Expected outputs:

```text
results/review_revision/mace_eval/finetuned_3060ti_summary.csv
results/review_revision/mace_eval/finetuned_3060ti_parity.csv
results/review_revision/mace_eval/foundation_mpa0_summary.csv
results/review_revision/mace_eval/foundation_mpa0_parity.csv
```

## Step 3: Train Review Committee

For full reviewer-response runs:

```bash
bash scripts/run_02_committee_train.sh
```

For a quick smoke run only:

```bash
MAX_NUM_EPOCHS=5 START_SWA=3 SEED_LIST="20260428" bash scripts/run_02_committee_train.sh
```

If RTX 5080 VRAM is tight:

```bash
BATCH_SIZE=2 VALID_BATCH_SIZE=2 bash scripts/run_02_committee_train.sh
```

Expected outputs:

```text
models/review_revision/li_mace_review_seed*.model
results/review_revision/li_mace_review_seed*/ ...
logs/review_revision/li_mace_review_seed*/ ...
```

## Step 4: Build Or Point To LAMMPS-MACE

If a compatible GPU LAMMPS-MACE binary already exists:

```bash
export LAMMPS_BIN=/absolute/path/to/lmp
```

Otherwise try:

```bash
bash environment/build_lammps_mace_5080.sh
```

The build requires CUDA Toolkit 12.8+ with `nvcc`, CMake, a compiler toolchain,
and working PyTorch CUDA 12.8 in the active env.

## Step 5: Run Review MD

Start with one short smoke case:

```bash
bash scripts/run_03_review_md_smoke.sh
```

Then run the reviewer array locally:

```bash
bash scripts/run_04_review_md_array.sh
```

The default array runs 5 structures x 3 seeds, 400 K, 100 ps production after
10 ps equilibration. Override with environment variables:

```bash
NSTEPS=1000000 EQUIL_STEPS=10000 DUMP_EVERY=1000 bash scripts/run_04_review_md_array.sh
```

## Optional Step 6: Four-Day Sprint Extensions

Only run these after the cluster-side DFT snapshot checks do not indicate an
obvious out-of-domain MACE artifact.

Selected 0.5 ns extension:

```bash
bash scripts/run_05_extended_md_selected.sh
```

Committee-model sensitivity MD on selected systems:

```bash
bash scripts/run_06_committee_md_selected.sh
```

These runs strengthen qualitative robustness. They still do not replace
converged CI-NEB barriers or DFT checks of high-displacement snapshots.

## Troubleshooting

- `torch.cuda.is_available() is false`: install a newer NVIDIA driver and rerun
  `environment/setup_mace_env_5080.sh`.
- `no kernel image is available`: the PyTorch wheel does not support RTX 5080;
  reinstall using the CUDA 12.8 wheel index in `setup_mace_env_5080.sh`.
- CUDA out of memory during committee training: use
  `BATCH_SIZE=2 VALID_BATCH_SIZE=2`, then `BATCH_SIZE=1` if needed.
- `mace_run_train` missing: rerun setup, then check `pip show mace-torch`.
- LAMMPS build cannot find Torch: run setup first; the build script reads
  `torch.utils.cmake_prefix_path`.
- LAMMPS binary lacks MACE: use `LAMMPS_BIN=/path/to/lmp` only if
  `lmp -h | grep -i mace` succeeds.
- LAMMPS/Kokkos does not recognize Blackwell arch: rerun with an explicit flag,
  for example `KOKKOS_ARCH=BLACKWELL120 bash environment/build_lammps_mace_5080.sh`,
  or inspect the Kokkos version for the exact architecture option.

## Return Results To Cluster

After completion, from the parent directory on the local machine:

```bash
rsync -avP -e "ssh -p 443" local_5080_reviewer_gpu_pack \
  xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/
```

Do not delete outputs until the cluster-side validation has parsed them.

## Source Notes

- NVIDIA lists GeForce RTX 5080 under CUDA capability 12.0:
  https://developer.nvidia.com/cuda/gpus
- NVIDIA's RTX 5080 product page also reports CUDA Capability 12.0:
  https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/
- PyTorch's official local installation page provides a CUDA 12.8 wheel index
  option and recommends checking `torch.cuda.is_available()` after install:
  https://pytorch.org/get-started/locally/

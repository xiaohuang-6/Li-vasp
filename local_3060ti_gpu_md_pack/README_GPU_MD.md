# Local RTX 3060 Ti GPU MD Runpack

This folder runs the fine-tuned Li/Si-graphene MACE model in LAMMPS on the local RTX 3060 Ti machine.

## Recommended MD Length

Do not start with 3 ns. Use staged validation:

1. `100step`: quick launch check.
2. `10ps`: first stability run. Confirm model loads on GPU, no lost atoms, no NaN, no violent structure collapse.
3. `100ps`: first meaningful thermal stability check. Inspect Li z motion, C/Si geometry, temperature, and energy drift.
4. `1ns`: first production-length pilot for MSD workflow.
5. `3ns`: only after the `100ps` and `1ns` runs are stable.

For a first scientific diffusion estimate, use at least `1ns`. For stronger MSD statistics, prefer multiple independent `1ns` replicas or `3-5ns` per system/temperature after active-learning validation.

## Contents

- `models/li_mace_v1_3060ti.model-lammps.pt`: LAMMPS TorchScript MACE model.
- `data/lammps/local_D_SiGraphene_2x2x1.data`: 220-atom Si-graphene/Li LAMMPS data file.
- `inputs/in.gpu_md_template`: fresh-run LAMMPS input template.
- `inputs/in.gpu_continue_template`: restart-continuation template.
- `scripts/check_gpu_env.sh`: checks GPU, LAMMPS, and ML-MACE availability.
- `scripts/run_gpu_md.sh`: runs `10ps`, `100ps`, `1ns`, or `3ns`.
- `scripts/continue_gpu_md.sh`: continues from the latest restart.
- `scripts/summarize_md.py`: summarizes LAMMPS log and trajectory progress.

## Expected Local Setup

This pack expects either:

- the previous `local_3060ti_runpack/` folder next to this folder, containing the GPU LAMMPS-MACE build and `local_runtime_env.sh`; or
- environment variables `LAMMPS_BIN` and `LIBTORCH_DIR` pointing to a GPU ML-MACE LAMMPS install.

The scripts automatically search these common locations.

## Run Order

From inside this folder on the local workstation:

```bash
bash scripts/check_gpu_env.sh
bash scripts/run_gpu_md.sh 100step
bash scripts/run_gpu_md.sh 10ps
bash scripts/run_gpu_md.sh 100ps
bash scripts/run_gpu_md.sh 1ns
```

Use `3ns` only after reviewing the `1ns` run:

```bash
bash scripts/run_gpu_md.sh 3ns
```

To force the KOKKOS command-line suffix:

```bash
USE_KOKKOS=1 bash scripts/run_gpu_md.sh 10ps
```

By default, the script does not pass `-sf kk`; `pair_style mace` should still use Torch CUDA when GPU libtorch is available. This matched the previous successful local smoke test.

## Continue From Restart

Continue the latest restart for another `100ps`:

```bash
bash scripts/continue_gpu_md.sh "" 100ps
```

Continue a specific restart for `1ns`:

```bash
bash scripts/continue_gpu_md.sh restarts/gpu_100ps_YYYYMMDD_HHMMSS.final.restart 1ns
```

## Outputs

- LAMMPS logs: `logs/<run_label>.lammps.log`
- trajectories: `trajectories/<run_label>.lammpstrj`
- restarts: `restarts/<run_label>.*.restart`
- summaries: `analysis/<run_label>.summary.json`

After each run, copy this whole folder back to `/home/xh121/Li-vasp` for validation.

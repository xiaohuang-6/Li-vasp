# Prompt For Local Coding Agent

You are running an RTX 3060 Ti local GPU MACE/LAMMPS MD validation pack.

Working directory: this `local_3060ti_gpu_md_pack` folder.

Goal:
1. Check that GPU LAMMPS-MACE is available.
2. Run the staged MD workflow: `10ps`, then `100ps`, then `1ns` only if earlier stages are stable.
3. Do not run `3ns` until the user has reviewed `1ns`.
4. Preserve all logs, trajectories, restarts, and summary JSON files.

Commands:

```bash
bash scripts/check_gpu_env.sh
bash scripts/run_gpu_md.sh 100step
bash scripts/run_gpu_md.sh 10ps
bash scripts/run_gpu_md.sh 100ps
bash scripts/run_gpu_md.sh 1ns
```

If `scripts/check_gpu_env.sh` cannot find LAMMPS:

1. Look for a sibling folder named `local_3060ti_runpack`.
2. If present, source `../local_3060ti_runpack/local_runtime_env.sh`.
3. If still missing, ask the user where the GPU LAMMPS binary is, or set `LAMMPS_BIN` and `LIBTORCH_DIR`.

Validation checklist:

- LAMMPS output should say `CUDA found` or `setting device type to torch::kCUDA`.
- `pair_style mace` must be present in `lmp -h`.
- No `ERROR`, `Lost atoms`, `nan`, `segmentation`, or `aborted` in logs.
- Final thermo line should be finite.
- Trajectory should contain frames beyond step 0.

After finishing, leave the folder intact so it can be copied back for inspection.

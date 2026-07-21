---
name: li-mace-reproduction
description: Reproduce the Li-MACE defective graphene report workflow on the HPC cluster.
---

# Li-MACE Reproduction Skill

Use this skill when asked to reproduce, audit, or extend the Li-MACE defective
graphene report workflow.

## First Files To Read

1. `AGENT_REPRODUCE_REPORT.md`
2. `AGENT_PROJECT_STATUS.md`
3. `README_DATA_EXPANSION.md`
4. `review_revision/README_REVIEW_FIXES.md`

## Operating Rules

- Keep generated data local: do not commit `results/`, `data/`, `dft_outputs/`,
  `dft_sp_outputs/`, `logs/`, `lammps_logs/`, `trajectories/`, `restarts/`,
  `models/`, `benchmarks/`, or VASP `POTCAR` files.
- Use `module` and Slurm on the cluster. CPU partition is `et2024`; GPU
  partition is `et_gpu`.
- Prefer `rg` for text/file searches.
- Before making scientific claims, check `AGENT_PROJECT_STATUS.md` claim
  boundaries.
- Treat fixed-geometry path scans as screening diagnostics only; use CI-NEB for
  migration barriers.
- Treat wrapped-coordinate MD as qualitative only; use unwrapped MD for
  diffusion analysis.

## Standard Commands

Static check:

```bash
bash -n *.sh submit_*.slurm review_revision/*.slurm
python -m py_compile *.py review_revision/*.py
```

Main reproduction guide:

```bash
less AGENT_REPRODUCE_REPORT.md
```

Review validation:

```bash
sbatch review_revision/submit_gpu_review_mace_eval.slurm
NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
python review_revision/prepare_review_neb_jobs.py --potcar-root "$POTCAR_ROOT"
```

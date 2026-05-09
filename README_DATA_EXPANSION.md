# Data Expansion Workflow For Li-MACE Fine-Tuning

This workflow expands the current 5 relaxed structures into a more useful MACE
training dataset.

## Step 1: Extract Existing Relaxation Frames

```bash
cd /home/xh121/Li-vasp
bash scripts_extract_relax_frames.sh
```

Outputs:

- `data/relax_all_frames.extxyz`
- `data/relax_all_frames.report.json`

## Step 2: Generate New Li Sampling Structures

```bash
bash scripts_generate_li_sampling.sh
```

Outputs:

- `structures/li_sampling/POSCAR_SP_*.vasp`
- `structures/li_sampling/li_sampling_summary.json`

The structures include adsorption sites and interpolated Li path images. Existing
Li atoms in the optimized slabs are removed first, then one Li atom is placed in
each sampled position.

## Step 3: Prepare VASP Single-Point Jobs

```bash
bash scripts_prepare_sp_jobs.sh
```

Outputs:

- `dft_sp_outputs/*/POSCAR`
- `dft_sp_outputs/*/INCAR`
- `dft_sp_outputs/*/KPOINTS`
- `dft_sp_outputs/*/POTCAR`
- `dft_sp_outputs/*/submit_vasp.slurm`

These are fixed-geometry labels: `IBRION=-1`, `NSW=0`.

## Step 4: Submit And Monitor VASP SP Jobs

Preview first:

```bash
DRY_RUN=1 bash scripts_submit_sp_jobs.sh
```

Submit a small pilot batch first:

```bash
LIMIT=5 bash scripts_submit_sp_jobs.sh
```

After those complete and parse successfully, submit the rest:

```bash
bash scripts_submit_sp_jobs.sh
```

`scripts_submit_sp_jobs.sh` writes `submitted_jobid.txt` inside each submitted
job directory. It will not resubmit those directories unless you explicitly use:

```bash
RESUBMIT=1 bash scripts_submit_sp_jobs.sh
```

Check status:

```bash
python check_sp_jobs.py --jobs-root dft_sp_outputs
```

## Step 5: Build MACE Train/Valid/Test Datasets

Run this only after the SP jobs are complete:

```bash
bash scripts_build_mace_datasets.sh
```

Outputs:

- `data/mace_datasets/li_mace_all.extxyz`
- `data/mace_datasets/li_mace_train.extxyz`
- `data/mace_datasets/li_mace_valid.extxyz`
- `data/mace_datasets/li_mace_test.extxyz`
- `data/mace_datasets/li_mace_dataset_report.json`

## Notes

- Slurm `COMPLETED` is not sufficient. Require `OUTCAR` parse success and
  `General timing`.
- Default SP jobs use 16 MPI ranks on `et2024`, matching the stable setting from
  the earlier relaxation jobs.
- If the queue is busy, use `LIMIT=5` or `LIMIT=10` batches.

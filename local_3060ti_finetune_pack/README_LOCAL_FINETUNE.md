# Local RTX 3060 Ti MACE Fine-Tune Pack

This directory contains the final Li-MACE dataset and scripts for running the
fine-tune locally on the previously configured RTX 3060 Ti workstation.

## Included Inputs

- `models/foundation/mace-mpa-0-medium.model`
- `data/mace_datasets/li_mace_train.extxyz` - 211 frames
- `data/mace_datasets/li_mace_valid.extxyz` - 31 frames
- `data/mace_datasets/li_mace_test.extxyz` - 31 frames
- `data/mace_datasets/li_mace_dataset_report.json`

## Assumed Local Environment

The scripts assume your local conda env from the previous 3060 Ti runpack exists:

- conda env name: `mace_md_local`
- conda base: auto-detected with `conda info --base`, or `$HOME/miniforge3`
- PyTorch CUDA works: `torch.cuda.is_available() == True`
- `mace_run_train` is on PATH inside the env

If your env has a different name:

```bash
ENV_NAME=your_env_name bash scripts/check_local_mace_env.sh
```

## Recommended Run Order

From the root of this copied directory:

```bash
bash scripts/check_local_mace_env.sh
bash scripts/run_short_smoke_5epoch.sh
bash scripts/run_local_finetune_3060ti.sh
python scripts/summarize_local_finetune.py
```

The short smoke run verifies local CUDA/MACE/dataset compatibility. The full run
uses these defaults:

- `DEFAULT_DTYPE=float32`
- `BATCH_SIZE=2`
- `VALID_BATCH_SIZE=2`
- `MAX_NUM_EPOCHS=300`
- `START_SWA=225`
- `LR=0.0005`
- fixed train/valid/test files, no random `valid_fraction`

If the full run hits CUDA out-of-memory, retry:

```bash
BATCH_SIZE=1 VALID_BATCH_SIZE=1 bash scripts/run_local_finetune_3060ti.sh
```

If you want a shorter first real run:

```bash
MAX_NUM_EPOCHS=100 START_SWA=75 bash scripts/run_local_finetune_3060ti.sh
```

## Expected Outputs

- `models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model`
- `models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt`
- `models/local_finetuned_li_mace_v1/li_mace_v1_3060ti_stagetwo.model`
- `results/local_li_mace_v1/*_train.txt`
- `logs/local_li_mace_v1/*.log`
- `local_finetune_summary.json`

After the run finishes, copy this entire directory back to the HPC project path
so the results can be inspected.

## Notes

This model is intended as the first full local fine-tune using the expanded 273
frame dataset. It is not yet the final production force field until validation
metrics, force parity, and LAMMPS stability are checked.

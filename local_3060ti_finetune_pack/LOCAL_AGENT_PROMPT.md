# Prompt For Local AI Coding Agent

You are running on my local Linux/WSL workstation with an NVIDIA RTX 3060 Ti.
I copied this `local_3060ti_finetune_pack` directory from the HPC project. Run
the MACE fine-tune locally and preserve all outputs.

Work only inside this copied directory. Do not run VASP. Do not regenerate DFT
data. Use the included dataset and foundation model.

Run from the package root:

```bash
bash scripts/check_local_mace_env.sh
bash scripts/run_short_smoke_5epoch.sh
bash scripts/run_local_finetune_3060ti.sh
python scripts/summarize_local_finetune.py
```

If the full run hits CUDA out-of-memory:

```bash
BATCH_SIZE=1 VALID_BATCH_SIZE=1 bash scripts/run_local_finetune_3060ti.sh
```

If the environment name is not `mace_md_local`, rerun with:

```bash
ENV_NAME=<actual_env_name> bash scripts/check_local_mace_env.sh
ENV_NAME=<actual_env_name> bash scripts/run_short_smoke_5epoch.sh
ENV_NAME=<actual_env_name> bash scripts/run_local_finetune_3060ti.sh
```

Expected completion artifacts:

- `models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model`
- `models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt`
- `results/local_li_mace_v1/`
- `logs/local_li_mace_v1/`
- `local_finetune_summary.json`

When finished, summarize the GPU detected, whether the 5-epoch smoke run passed,
whether the full run completed, validation/test RMSE from the logs, and any
warnings/errors. Then I will copy the whole folder back to HPC for inspection.

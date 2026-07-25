# GPU Local Transfer Bundle

This bundle contains the two local GPU runpacks prepared on the cluster:

- `local_3060ti_finetune_pack.zip`: MACE dataset, foundation model, fine-tune scripts, and previous local fine-tune outputs.
- `local_3060ti_gpu_md_pack.zip`: LAMMPS-MACE model/data/input scripts for staged GPU MD.

## Unpack

```bash
tar -xzf li_mace_gpu_local_tasks_bundle.tar.gz
unzip local_3060ti_finetune_pack.zip
unzip local_3060ti_gpu_md_pack.zip
```

## Fine-Tune Run Order

```bash
cd local_3060ti_finetune_pack
bash scripts/check_local_mace_env.sh
bash scripts/run_short_smoke_5epoch.sh
bash scripts/run_local_finetune_3060ti.sh
python scripts/summarize_local_finetune.py
```

If VRAM is tight:

```bash
BATCH_SIZE=1 VALID_BATCH_SIZE=1 bash scripts/run_local_finetune_3060ti.sh
```

## GPU MD Run Order

```bash
cd ../local_3060ti_gpu_md_pack
bash scripts/check_gpu_env.sh
bash scripts/run_gpu_md.sh 100step
bash scripts/run_gpu_md.sh 10ps
bash scripts/run_gpu_md.sh 100ps
bash scripts/run_gpu_md.sh 1ns
```

Run `3ns` only after the `100ps` and `1ns` runs are stable:

```bash
bash scripts/run_gpu_md.sh 3ns
```

## Copy Results Back To Cluster

From your local machine, after the runs finish:

```bash
rsync -avP -e "ssh -p 443" local_3060ti_finetune_pack local_3060ti_gpu_md_pack xh121@et-mei.chem.duke.edu:/home/xh121/Li-vasp/
```

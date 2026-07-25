# Two-Day Rush Execution Notes

This folder contains the accelerated workflow used to produce paper-ready
evidence without waiting for long ns-scale GPU MD.

## Completed Immediately

- DFT/SP status check: 79/79 fixed-geometry VASP single-point jobs parsed.
- Dataset summary: 273 MACE frames, split 211 train / 31 valid / 31 test.
- DFT Li site rankings and path barrier estimates.
- Training curve extraction from the local 3060 Ti MACE fine-tune log.

Primary output directory:

```bash
results/two_day_rush
```

Current deliverable archive:

```bash
results/two_day_rush_deliverable_20260708.tar.gz
```

Important files:

```bash
results/two_day_rush/SUMMARY.md
results/two_day_rush/PAPER_RESULTS_BRIEF.md
results/two_day_rush/MANUSCRIPT_RESULTS_DRAFT.md
results/two_day_rush/MD_QUALITY_NOTES.md
results/two_day_rush/NEXT_48H_ACTION_PLAN.md
results/two_day_rush/RESULTS_MANIFEST.json
results/two_day_rush/site_energy_rankings.csv
results/two_day_rush/path_barriers.csv
results/two_day_rush/path_profiles.csv
results/two_day_rush/mace_error_table_final.csv
results/two_day_rush/site_energy_rankings.png
results/two_day_rush/path_profiles.png
results/two_day_rush/training_curve.png
```

## Completed MD Jobs

400 K / 10 ps stability MD:

```bash
sacct -j 3095788 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P
```

This was a 5-task Slurm array over:

```text
A_Perfect
B1_Monovacancy
B2_Divacancy
C_StoneWales
D_SiGraphene
```

Each task completed 10 ps:

```text
10000 steps x 1 fs = 10 ps
```

800 K accelerated short MD:

```bash
sacct -j 3095794,3095863 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P
```

Each task runs 2 ps:

```text
2000 steps x 1 fs = 2 ps
```

The 800 K run and its independent post-processing are complete. Outputs:

```bash
results/two_day_rush/md_800k/md_summary.csv
results/two_day_rush/md_800k/md_temperature_energy.png
results/two_day_rush/md_800k/md_li_xy_msd.png
```

Unified MD post-processing:

```bash
sacct -j 3095864 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P
```

The final post-processing job completed successfully. The main MD outputs are in:

```bash
results/two_day_rush/md
```

A `md_partial` progress analysis is retained for auditability:

```bash
results/two_day_rush/md_partial
```

For paper figures, prefer the final `results/two_day_rush/md` outputs and the
clean 400 K subset in `results/two_day_rush/md_400k_stable_current`.

A shorter 400 K / 1 ps backup run has completed and was post-processed:

```bash
sacct -j 3095801,3095808 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P
```

Its complete-run backup figures are available at:

```bash
results/two_day_rush/md_fast
```

Current final/backup MD files:

```bash
results/two_day_rush/md_fast/md_summary.csv
results/two_day_rush/md_fast/md_thermo.csv
results/two_day_rush/md_fast/md_li_msd.csv
results/two_day_rush/md_fast/md_temperature_energy.png
results/two_day_rush/md_fast/md_li_xy_msd.png
results/two_day_rush/md_400k_stable2ps/md_summary.csv
results/two_day_rush/md_400k_stable2ps/md_temperature_energy.png
results/two_day_rush/md_400k_stable2ps/md_li_xy_msd.png
results/two_day_rush/md_400k_stable2p5ps/md_summary.csv
results/two_day_rush/md_400k_stable2p5ps/md_temperature_energy.png
results/two_day_rush/md_400k_stable2p5ps/md_li_xy_msd.png
results/two_day_rush/md_400k_stable2p7ps/md_summary.csv
results/two_day_rush/md_400k_stable2p7ps/md_temperature_energy.png
results/two_day_rush/md_400k_stable2p7ps/md_li_xy_msd.png
results/two_day_rush/md_400k_stable2p8ps/md_summary.csv
results/two_day_rush/md_400k_stable2p8ps/md_temperature_energy.png
results/two_day_rush/md_400k_stable2p8ps/md_li_xy_msd.png
results/two_day_rush/md_400k_stable_current/md_summary.csv
results/two_day_rush/md_400k_stable_current/md_temperature_energy.png
results/two_day_rush/md_400k_stable_current/md_li_xy_msd.png
results/two_day_rush/md/md_summary.csv
results/two_day_rush/md/md_thermo.csv
results/two_day_rush/md/md_li_msd.csv
results/two_day_rush/md/md_temperature_energy.png
results/two_day_rush/md/md_li_xy_msd.png
```

Final post-processing intentionally excludes the 1 ps backup run, so `md/`
contains the main 10 ps 400 K and 2 ps 800 K trajectories only. The clean
`md_400k_stable_current` subset contains the completed 10 ps 400 K runs for
`A_Perfect`, `B2_Divacancy`, `C_StoneWales`, and `D_SiGraphene`, excluding the
unstable `B1_Monovacancy` trajectory.

CPU scaling benchmark:

```bash
sacct -j 3095807 --format=JobID,JobName,Partition,State,ExitCode,Elapsed,AllocCPUS,NodeList -P
cat benchmarks/cpu_scaling_3095807/scaling_summary.tsv
```

The completed scaling benchmark shows no CPU thread-count speedup for this
small 200-220 atom system. The fastest tested setting was 1 OpenMP thread.

## Monitoring Commands

Check all current project jobs:

```bash
squeue -u xh121 -o "%.18i %.9P %.28j %.8u %.2t %.12M %.6D %R"
```

Check MD progress:

```bash
for f in lammps_logs/two_day_md/*.log; do
  echo "### $f"
  rg '^\s*[0-9]+\s+' "$f" | tail -5
done
```

Check final accounting:

```bash
sacct -j 3095788,3095794,3095864,3095801,3095808,3095807,3095863 --format=JobID,JobName,Partition,State,ExitCode,Elapsed,MaxRSS,NodeList -P
```

Run MD post-processing manually if needed:

```bash
conda activate mace_md
python analyze_short_md.py \
  --log-dir lammps_logs/two_day_md \
  --log-glob "*_400K_10000steps.log,*_800K_2000steps.log" \
  --traj-dir trajectories/two_day_md \
  --traj-glob "*_400K_10000steps.lammpstrj,*_800K_2000steps.lammpstrj" \
  --output-dir results/two_day_rush/md \
  --expected-steps 10000
```

Refresh the current longest non-B1 400 K stable subset after adding or changing
MD logs:

```bash
conda activate mace_md
python refresh_current_stable_md.py --also-write-step-label
python write_md_quality_notes.py
python write_paper_results_brief.py
python write_manuscript_results_draft.py
python make_results_manifest.py
bash package_two_day_results.sh
```

## Current Limitation

MACE parity via ASE on CPU is currently skipped because the serialized `.model`
triggers a CUDA-driver check during `torch.load`, even with CPU map-location.
This does not block LAMMPS CPU MD because the TorchScript LAMMPS model loads and
runs on CPU. For model validation in the two-day writeup, use the MACE training
log error table and the completed DFT/SP energy landscape.

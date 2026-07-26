# 24h Reviewer-Revision Action Status

Updated: 2026-07-26.

## Current Constraint

Do not submit reviewer follow-up GPU work on the cluster. GPU model-validation
tasks were run from the local RTX 5080 package:

```text
/home/xh121/Li-vasp/local_5080_referee_followup_pack_20260725_1825.tar.gz
SHA256 eed07f8d599df605c679fb1a6bdeb30f050fd515f3a5c2098b9fb02843a25174
```

The previously submitted cluster GPU jobs `3129655` (`li-e0-grouped`) and
`3129656` (`li-snap-force`) were canceled on 2026-07-25 after the local 5080
handoff package was prepared. The 24h cluster path now consists only of CPU
jobs with 24h-or-shorter limits. Older optional full-node NEB CPU jobs
`3115996_6`--`3115996_9` had 48h limits and were canceled on 2026-07-25 to
keep the active reviewer-follow-up queue inside the 24h operating constraint.

The returned local 5080 result package was accepted on 2026-07-26:

```text
/home/xh121/Li-vasp/incoming_gpu_results/local_5080_referee_followup_results_20260725_2309.tar.gz
SHA256 35ac20123795f978c64ee7a5266eba1e96c40a9ca954da99be742e0039edb0d2
```

Clean accepted outputs are in:

```text
/home/xh121/Li-vasp/results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/
```

That directory excludes stale `*_failed_snapshots.csv` files from an earlier
failed evaluator attempt; the accepted CSVs are the later 9 frames x 3 models
summary/error outputs.

## What Was Fixed Immediately

- The MACE data builder now creates leakage-audited grouped splits. Relaxation
  trajectories and fixed-path image groups cannot be split across
  train/validation/test unless the legacy mode is explicitly requested.
- `run_finetune.sh` now defaults to `E0S=estimated`, using MACE foundation-model
  assisted E0 estimation instead of the old `--E0s=average` default.
- The manuscript no longer treats the original same-workflow split as an
  independent transferability benchmark.
- The manuscript no longer reports short-window diffusion coefficients from
  the 200--500 ps MSD traces.
- A direct MACE-vs-DFT force evaluator was added for the nine completed
  high-displacement DFT snapshot checks.
- The grouped-E0 local RTX 5080 fine-tune completed and produced both a MACE
  model and a LAMMPS TorchScript model.
- The direct snapshot-force evaluator completed for foundation MACE-MPA-0, the
  earlier 3060Ti fine-tuned model, and the new grouped-E0 model on all nine
  initial-campaign high-displacement DFT snapshots.
- PBE-D3/dipole adsorption-energy single points completed for all five
  families, with 11/11 component energies usable and 0 fatal VASP markers.
- `review_revision/SNAPSHOT_DFT_EVIDENCE.md` and `.csv` now archive the
  current nine initial-campaign snapshot OUTCAR hashes, final energies,
  electronic-convergence markers, fatal-marker screens, and force-readability
  checks. The current archive resolves the earlier 8/9-vs-9/9 inconsistency by
  tying every manuscript Table 4 energy to a concrete OUTCAR hash.
- The manuscript now names the foundation model as MACE-MPA-0 and gives the
  exact checkpoint file `mace-mpa-0-medium.model`.
- The manuscript now labels the original 20.1 meV/A test force RMSE as a
  same-workflow diagnostic, not an independent transferability benchmark.
- Figure 3 was split into separate full-width site-scan and path-scan figures,
  and the archive plan now includes a license and reproducibility manifest.

## Submitted Slurm Jobs

| Job ID | Name | Partition | Purpose |
|---:|---|---|---|
| 3129645 | li-ads-sp | et2024 | PBE-D3 + dipole adsorption-energy single points |
| 3129657 | li-fast-neb | et2024 | 3-image Gamma-only fast CI-NEB fallback |
| 3129672 | li-fast-neb-end | et2024 | Endpoint single points at the same level as fast CI-NEB |
| 3129676 | li-md-dftcheck | et2024 | Production-set high-displacement DFT snapshot checks |

Latest collector status at 03:41 EDT on 2026-07-26:

- Adsorption-energy single points: 11/11 usable components, 5/5 usable
  family-level `E_ads` values. Use them only as single-geometry PBE-D3/dipole
  anchors.
- Fast NEB fallback: 5/5 paths have image energies, 0/5 formally converged,
  0/5 fatal; no usable barriers yet.
- Production-set high-displacement DFT snapshots: 2/7 usable, three additional
  rows have partial SCF energies, and two have not produced an SCF energy. The
  two usable rows come from one Si$_4$--graphene trajectory, so they are not
  enough for a production-set validation claim.
- No matching cluster GPU jobs are present.

## Canceled GPU Slurm Jobs

| Job ID | Name | Partition | Replacement |
|---:|---|---|---|
| 3129655 | li-e0-grouped | et_gpu | Run `scripts/run_all_under_24h_5080.sh` inside the local 5080 package |
| 3129656 | li-snap-force | et_gpu | Run `scripts/run_all_under_24h_5080.sh` inside the local 5080 package |

## Canceled Optional 48h CPU Slurm Jobs

| Job ID | Name | Reason |
|---:|---|---|
| 3115996_6 | li-review-neb60 | Optional full-node NEB; canceled to enforce the active 24h follow-up constraint |
| 3115996_7 | li-review-neb60 | Optional full-node NEB; canceled to enforce the active 24h follow-up constraint |
| 3115996_8 | li-review-neb60 | Optional full-node NEB; canceled to enforce the active 24h follow-up constraint |
| 3115996_9 | li-review-neb60 | Optional full-node NEB; canceled to enforce the active 24h follow-up constraint |

## Commands To Collect Results

```bash
cd /home/xh121/Li-vasp

# Adsorption-energy status and E_ads table
python review_revision/collect_adsorption_energies.py \
  --manifest review_revision/adsorption_energy_jobs/adsorption_manifest.csv \
  --output-dir results/review_revision/adsorption_energy_analysis

# Fast NEB status
python review_revision/collect_neb_results.py \
  --job-list review_revision/neb_fast_jobs/neb_fast_job_list.txt \
  --paths-csv results/two_day_rush/path_barriers.csv \
  --endpoint-mode endpoint_sp \
  --endpoint-manifest review_revision/neb_fast_endpoint_jobs/endpoint_manifest.csv \
  --output-dir results/review_revision/neb_fast_analysis

# Full NEB status
python review_revision/collect_neb_results.py \
  --job-list review_revision/neb_jobs/neb_job_list.txt \
  --paths-csv results/two_day_rush/path_barriers.csv \
  --output-dir results/review_revision/neb_analysis_final

# Production-set high-displacement DFT snapshots
python review_revision/collect_md_snapshot_dft_checks.py \
  --manifest review_revision/production_md_snapshot_dft_jobs/md_snapshot_dft_manifest.csv \
  --output-dir results/review_revision/production_md_snapshot_dft_analysis
```

## Rules For Manuscript Use

- Use adsorption energies only when `usable = True` in
  `results/review_revision/adsorption_energy_analysis/adsorption_energies.csv`.
  This gate is now passed for all five families, but the values are still
  single-geometry anchors rather than exhaustive relaxed site searches.
- Use NEB barriers only when `barrier_usable = True` in the collector output;
  the collector leaves barrier columns blank until all images are available,
  VASP reports ionic convergence, and no fatal marker is detected.
- Use high-displacement snapshot force validation only as an out-of-domain
  stress diagnostic. The accepted grouped-E0 result improves D Si4-graphene
  force RMSE to 113.6 meV/A over six snapshots, but B1 monovacancy remains poor
  at 1107.0 meV/A over three snapshots. This does not validate high-displacement
  transport mechanisms.
- Do not reintroduce diffusion coefficients unless longer/larger MD gives
  approximately linear MSD behavior with acceptable seed statistics.

# Review-Driven Computational Follow-Up

This directory contains reusable scripts for the validation work needed before
the project can make strong kinetic or diffusion claims. It intentionally does
not contain manuscript drafts, manuscript figures, generated trajectories, model
checkpoints, or VASP/LAMMPS output data.

## Purpose

The current evidence is enough to show that the pipeline can run, but not enough
to claim final Li diffusion mechanisms. The missing work is computational:

- Real migration barriers require relaxed endpoints and CI-NEB, not fixed-path
  energy scans.
- Diffusion analysis requires unwrapped coordinates, equilibration removal,
  multiple seeds, and Li/time-origin averaging.
- MACE credibility requires held-out test errors, foundation-model comparison,
  and preferably a small committee or uncertainty check.

## Files

- `prepare_review_neb_jobs.py`: creates VASP CI-NEB job folders from existing Li
  path endpoints.
- `submit_cpu_review_neb_array.slurm`: runs the generated VASP NEB folders on
  the CPU partition.
- `submit_cpu_review_neb_fullnode_array.slurm`: optional high-parallelism NEB
  launcher for time-critical reruns or not-yet-started NEB jobs.
- `evaluate_mace_on_splits.py`: evaluates a MACE model on train/valid/test
  extxyz splits and writes summary/parity CSV files.
- `submit_gpu_review_mace_eval.slurm`: compares the fine-tuned model against
  the foundation model on GPU.
- `submit_gpu_review_committee_train.slurm`: launches a small multi-seed MACE
  fine-tuning committee.
- `in.lammps_review_unwrapped_md`: LAMMPS input that dumps wrapped and unwrapped
  coordinates plus image flags.
- `submit_gpu_review_md_array.slurm`: runs 5 structures x 3 seeds for unwrapped
  review MD on the GPU partition.
- `analyze_reviewer_gpu_results.py`: analyzes returned local/GPU reviewer
  outputs and writes MACE, committee, and MD summary CSV/PNG/Markdown files.
- `collect_neb_results.py`: safely collects partial or final VASP CI-NEB image
  energies, status flags, barrier tables, and profile figures.
- `prepare_md_snapshot_dft_checks.py`: extracts high-displacement MD snapshots
  and prepares VASP single-point checks for possible MLIP extrapolation.
- `submit_cpu_md_snapshot_dft_array.slurm`: runs the generated MD-snapshot DFT
  checks on the CPU partition.
- `submit_cpu_md_snapshot_dft_fullnode_array.slurm`: optional high-parallelism
  launcher for time-critical snapshot checks.
- `collect_md_snapshot_dft_checks.py`: summarizes partial/final VASP
  single-point results for the selected MD snapshots.
- `check_reviewer_jobs.sh`: one-command Slurm/status refresh for the active NEB
  and MD-snapshot DFT-check jobs.
- `static_check_manuscript.py`: checks the conservative manuscript for missing
  figures, missing bibliography keys, missing cross-reference labels, and
  residual internal-revision or overclaiming phrases.
- `REVIEWER_RESPONSE_STATUS.md`: current checklist of which reviewer issues are
  covered by existing evidence and which still require NEB/DFT follow-up.
- `RESPONSE_LETTER_SUBMISSION_DRAFT.md`: cleaner point-by-point response letter
  draft for the conservative submission route.
- `SUBMISSION_SEQUENCE.md`: concise command order for CPU and GPU reviewer
  calculations.
- `REVIEW_FEEDBACK_COVERAGE.md`: reviewer feedback coverage map.
- `COMPLETION_AUDIT.md`: final audit tying the imported GPU evidence,
  manuscript changes, response draft, validation checks, and remaining external
  limitations together.
- `SCI_IMPACT_STRATEGY.md`: publication-impact review explaining why the
  conservative route is defensible but lower-impact, and which CPU/GPU
  calculations would restore a stronger diffusion story.
- `FOUR_DAY_SCI_COMPUTE_PLAN.md`: four-day CPU/GPU compute plan with evidence
  gates for a realistic 3--4 IF SCI submission route.

## CPU CI-NEB Workflow

Prepare the templates only after setting the real licensed PAW_PBE root:

```bash
cd /home/xh121/Li-vasp
conda activate mace_md
python review_revision/prepare_review_neb_jobs.py --potcar-root /path/to/potpaw_PBE
N=$(wc -l < review_revision/neb_jobs/neb_job_list.txt)
echo "NEB jobs: $N"
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_review_neb_array.slurm
```

Use `%2` or another concurrency cap when the CPU queue is crowded. Remove the
cap only if it is acceptable to start every NEB job at once.

Generated folders under `review_revision/neb_jobs/` are ignored by Git because
they contain run-specific POSCAR/POTCAR/job data. Regenerate them as needed.

For time-critical NEB runs, prefer fewer concurrent jobs with more ranks per
NEB rather than many underpowered NEB jobs. The full-node alternative uses 60
MPI ranks so that the default `IMAGES = 5` is divided evenly:

```bash
# Only submit indices whose directories are not being written by active jobs.
sbatch --array=4-9%1 review_revision/submit_cpu_review_neb_fullnode_array.slurm
```

The full-node script refuses to overwrite a directory that already contains
`vasp.log`. Set `RESTART_EXISTING=1` only after confirming no active Slurm job
is writing that directory.

Collect partial or final NEB status at any time:

```bash
cd /home/xh121/Li-vasp
python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_current
```

After all NEB jobs converge, rerun with a final output directory:

```bash
python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_final
```

## GPU Validation Workflow

Run the model evaluator first because it is relatively small:

```bash
cd /home/xh121/Li-vasp
sbatch review_revision/submit_gpu_review_mace_eval.slurm
```

Run a short MD smoke test before production-length runs:

```bash
NSTEPS=1000 EQUIL_STEPS=500 sbatch review_revision/submit_gpu_review_md_array.slurm
```

If stable, run the default 100 ps production jobs:

```bash
sbatch review_revision/submit_gpu_review_md_array.slurm
```

Train the committee if MD conclusions will be retained:

```bash
sbatch review_revision/submit_gpu_review_committee_train.slurm
```

Analyze copied-back local or GPU reviewer outputs:

```bash
python review_revision/analyze_reviewer_gpu_results.py \
  --input-root incoming_gpu_results/reviewer_5080_20260721/extracted/local_5080_reviewer_gpu_pack \
  --output-dir results/review_revision/gpu_analysis
```

## MD Snapshot DFT Checks

Prepare a small set of VASP single-point checks for the highest-displacement
unwrapped MD snapshots. These are qualitative sanity checks for possible MLIP
extrapolation, so the generated KPOINTS are Gamma-only by default:

```bash
cd /home/xh121/Li-vasp
conda activate mace_md
python review_revision/prepare_md_snapshot_dft_checks.py --top-runs 3 --snapshots-per-run 2 --also-final
```

Submit them on CPU nodes when resources are acceptable:

```bash
N=$(wc -l < review_revision/md_snapshot_dft_jobs/md_snapshot_dft_job_list.txt)
sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_md_snapshot_dft_array.slurm
```

If the 16-rank snapshot checks are too slow, a practical middle ground is to
override the Slurm resources at submission time and use 32 ranks with 192 GB:

```bash
sbatch -J li-md-dft32 --ntasks=32 --mem=192G --array=0-$((N-1))%2 \
  review_revision/submit_cpu_md_snapshot_dft_array.slurm
```

For still more aggressive reruns, use the full-node alternative for directories
that have not started yet:

```bash
sbatch --array=0-$((N-1))%1 review_revision/submit_cpu_md_snapshot_dft_fullnode_array.slurm
```

As with the NEB full-node launcher, this script refuses to overwrite an existing
`vasp.log` unless `RESTART_EXISTING=1` is set deliberately.

Collect partial or final DFT-check status:

```bash
python review_revision/collect_md_snapshot_dft_checks.py \
  --output-dir results/review_revision/md_snapshot_dft_analysis_current
```

The collector separates in-progress SCF energies from usable DFT energies.
Only rows with both `completed = True` and `electronic_converged_marker = True`
should be used in the manuscript or response letter.

## One-Command Status Check

Refresh Slurm status plus both partial result summaries:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

## Manuscript Static Check And Compile

Run the static manuscript check before sending the source to a TeX environment:

```bash
cd /home/xh121/Li-vasp
python review_revision/static_check_manuscript.py
```

When a LaTeX engine is available, compile the manuscript with:

```bash
cd /home/xh121/Li-vasp/manuscript
bash compile_manuscript.sh
```

The current cluster login environment does not expose `latexmk`, `pdflatex`,
`xelatex`, or `tectonic`, so the source has been statically checked but not
compiled to PDF here.

## Output Locations

Expected generated outputs are local-only and ignored by Git:

- `review_revision/neb_jobs/`
- `results/review_revision/`
- `trajectories/review_revision/`
- `review_revision/md_outputs/`
- `review_revision/md_logs/`
- `models/review_revision/`

## Acceptance Checks

Before using the results scientifically:

- Confirm every VASP NEB job finished normally and did not stop at an
  unconverged electronic step.
- Confirm the MACE evaluator reports errors for train, validation, and test
  splits for both foundation and fine-tuned models.
- Confirm MD logs show no lost atoms and no runaway energy drift.
- Confirm MSD or displacement analysis uses unwrapped coordinates, not wrapped
  coordinates.
- Confirm any reported barrier is from CI-NEB, not from the fixed-geometry path
  scan used for rapid screening.

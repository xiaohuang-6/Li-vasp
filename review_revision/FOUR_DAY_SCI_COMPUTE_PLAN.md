# Four-Day SCI Compute Plan

Date: 2026-07-21

Goal: maximize the chance of submitting a defensible 3--4 impact-factor SCI
manuscript within four days. This plan cannot guarantee acceptance. It is
designed to avoid the original overclaiming risk while adding the minimum
DFT/GPU evidence needed to make the paper more than a low-impact workflow note.

## Target Manuscript Positioning

Primary target story if DFT anchors finish:

> DFT-benchmarked MACE screening of local Li migration and trapping in defective
> graphene and Si4--graphene motifs.

Fallback story if DFT anchors do not finish:

> Fine-tuned MACE validation and conservative local Li energy screening in
> defective graphene and Si4--graphene motifs.

Do not return to "silicon--graphene composite anode performance" language
unless voltage/capacity/Li-metal-reference calculations are added. Those are
not realistic within four days.

## Current Status After 2026-07-26 01:28 EDT Check

CPU VASP:

- Full CI-NEB: 10/10 paths have all intermediate image energies.
- CI-NEB: 0/10 formally converged.
- CI-NEB: 1 fatal marker, from B2 divacancy path01 force blow-up/internal
  VASP errors. B2 divacancy path02 also has a huge force diagnostic and is not
  interpretable as a barrier.
- Initial-campaign MD snapshot DFT: 9/9 completed, 9/9 usable electronically
  converged energies, and 0 fatal markers.
- Production-trajectory MD snapshot DFT: Slurm array `3129676`
  (`li-md-dftcheck`) is active with a 24h limit; 1/7 completed, 1/7 usable,
  0/7 fatal markers, and 5/7 with in-progress SCF energies. The single usable
  row is a sanity check only, not production-set validation.
- Adsorption-energy D3/dipole single points: 11/11 single-point components are
  completed/usable, 0 fatal markers, and all 5 family-level adsorption
  energies are usable as single-geometry anchors.
- Fast 3-image Gamma-only CI-NEB fallback: Slurm array `3129657`
  (`li-fast-neb`) is active with a 24h limit; 5/5 paths have all image
  energies, 0/5 are formally converged, and 0/5 have fatal markers.

GPU/MACE:

- Foundation vs fine-tuned evaluator is complete.
- Test force RMSE improved from 285.2 to 20.1 meV/A.
- Three committee seeds completed.
- 15/15 unwrapped 100 ps MD runs completed cleanly.
- The local RTX 5080 grouped-E0 fine-tune and nine-snapshot force-evaluation
  diagnostics completed from `local_5080_referee_followup_pack_20260725_1825.tar.gz`.
  The returned result package is accepted as diagnostic evidence.
- Do not submit reviewer follow-up GPU work on the cluster.

## Non-Negotiable Evidence Gates

Use these gates to decide what can be claimed.

### Gate A: Migration Barrier Claim

Allowed only if at least one CI-NEB path formally converges and the collector
reports `converged = True`.

Use in manuscript:

- "Converged CI-NEB barrier for path X is ..."
- "Fixed-geometry scans over/underestimate or qualitatively bracket the
  relaxed path ..."

Do not use:

- Partial NEB image energies.
- `last BRION g(F) < |EDIFFG|` without formal VASP completion.

### Gate B: High-Displacement MD Mechanism Claim

The current run has nine high-displacement MD snapshot DFT checks with
`completed = True` plus `electronic_converged_marker = True`. The grouped-E0
snapshot-force evaluator improves the Si4-graphene subset but remains poor for
monovacancy. This allows only a DFT/MACE stress-test statement, not a mechanism
claim.

Use in manuscript:

- "Representative high-displacement snapshots were DFT sanity checked."

Do not use:

- In-progress SCF energies.
- Unchecked large MSD events as physical transport mechanisms.

### Gate C: Diffusion Coefficient Claim

Allowed only if longer GPU MD gives reasonably linear unwrapped MSD over a
defined fitting window across multiple seeds and the DFT snapshot checks are
not pathological.

If this gate is not met, report only finite-window displacement diagnostics.

## Four-Day Schedule

### Day 1: Preserve Running CPU Jobs And Monitor

Do not restart active NEB jobs unless they fail. Existing jobs have already
consumed significant wall time.

Run every 3--4 hours:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

If an active NEB job finishes, collect current results:

```bash
python review_revision/collect_neb_results.py \
  --output-dir results/review_revision/neb_analysis_current
```

If an active snapshot DFT job finishes:

```bash
python review_revision/collect_md_snapshot_dft_checks.py \
  --output-dir results/review_revision/md_snapshot_dft_analysis_current
```

### Day 2: Add Only Results That Pass Gates

If any CI-NEB path is formally converged:

1. Generate `results/review_revision/neb_analysis_final/`.
2. Add a NEB figure/table only for converged paths.
3. Upgrade the manuscript title and results from fixed-geometry-only screening
   to DFT-benchmarked local migration/trapping screening.

If no CI-NEB path is formally converged, do not add barrier values.

Given the current nine usable high-displacement snapshot DFT checks:

1. Compare the DFT energy/SCF behavior and geometry sanity of those snapshots.
2. Add one paragraph or table saying selected large-displacement configurations
   are DFT-sanity-checked.
3. Do not claim a diffusion mechanism without a systematic representative set.

Given the completed adsorption-energy single points:

1. Add the PBE-D3/dipole `E_ads` table only as single-geometry adsorption
   anchors.
2. Do not describe the values as voltage, capacity, clustering, or migration
   evidence.

### Day 3: Use RTX 5080 Only If Gate B Is Not Failing

On the local RTX 5080 pack:

```bash
cd local_5080_reviewer_gpu_pack
bash scripts/run_05_extended_md_selected.sh
```

Default: 0.5 ns, systems `A_Perfect C_StoneWales D_SiGraphene`, three seeds,
low trajectory output frequency.

If committee sensitivity matters:

```bash
bash scripts/run_06_committee_md_selected.sh
```

Default: selected systems `D_SiGraphene B1_Monovacancy`, one seed per committee
model, 0.2 ns each.

Return outputs to the cluster and rerun:

```bash
python review_revision/analyze_reviewer_gpu_results.py \
  --input-root incoming_gpu_results/reviewer_5080_20260721/extracted/local_5080_reviewer_gpu_pack \
  --output-dir results/review_revision/gpu_analysis
```

### Day 4: Manuscript Lock

Run checks:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
python review_revision/static_check_manuscript.py
python -m py_compile review_revision/*.py
bash -n review_revision/*.slurm review_revision/check_reviewer_jobs.sh manuscript/compile_manuscript.sh
```

Then choose one route:

Route 1, stronger SCI route:

- At least one converged CI-NEB path.
- At least one usable DFT snapshot check.
- Optional longer 5080 MD supports the same qualitative trend.
- Target as a computational materials article with DFT-benchmarked MACE
  migration/trapping screening.

Route 2, fallback SCI route:

- No final converged NEB and only snapshot DFT sanity checks.
- Keep current conservative manuscript.
- Target a lower-risk computational modeling/workflow journal.

## CPU Submission Policy

Current NEB and snapshot arrays are already running or queued. Do not duplicate
them. Submit only if a job fails or if a not-yet-started index is deliberately
rerun.

Status command:

```bash
squeue -u "$USER"
```

Full-node NEB fallback for not-yet-started indices only:

```bash
sbatch --array=<indices>%1 review_revision/submit_cpu_review_neb_fullnode_array.slurm
```

32-rank MD snapshot DFT fallback for not-yet-started indices only:

```bash
sbatch -J li-md-dft32 --ntasks=32 --mem=192G --array=<indices>%2 \
  review_revision/submit_cpu_md_snapshot_dft_array.slurm
```

## GPU Submission Policy

Do not submit GPU jobs on the cluster for the reviewer follow-up. The current
local RTX 5080 follow-up package has already been run and accepted. Any future
GPU model-validation work must be packaged for manual local 5080 execution with
an explicit under-24h runner and result-return instructions.

Do not spend future 5080 time on arbitrary long MD before DFT snapshot checks.
The best future GPU use remains:

1. Compare against newly completed DFT snapshot or NEB labels if they are added
   to the training set.
2. Extend selected already-stable MD only after representative DFT sanity
   checks pass.
3. Fine-tune a final model only if new DFT labels from NEB/snapshots are added.

## Target Journal Tier

A realistic 3--4 IF target is a computational materials or molecular modeling
journal that accepts sound, carefully bounded computational studies. The best
fit is not a high-impact battery-materials journal unless the DFT anchors finish.

Potential fit categories:

- Computational materials modeling journal.
- Molecular modeling journal.
- Carbon/graphene materials journal only if NEB barriers finish.

Final journal choice must be checked against the current JCR and the author's
institutional requirements before submission.

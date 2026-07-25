# Reviewer-Response Status

Last updated: 2026-07-25

## Completed Evidence Now In The Workspace

- Local GPU result archive was copied to `incoming_gpu_results/` and extracted.
- MACE evaluator outputs were synchronized to `results/review_revision/mace_eval/`.
- Committee checkpoints were synchronized to `models/review_revision/`.
- 100 ps reviewer MD logs, MSD files, and trajectories were synchronized to:
  - `review_revision/md_logs/`
  - `review_revision/md_outputs/`
  - `trajectories/review_revision/`
- Unified GPU analysis outputs are in `results/review_revision/gpu_analysis/`.
- The second 5080 GPU return package was analyzed in
  `results/review_revision/gpu_analysis_20260725_0116/`; it contains 18/18
  completed 200--500 ps production trajectories with no LAMMPS errors, lost
  atoms, NaNs, or dangerous neighbor-list builds.
- Submission-facing response letter draft:
  `review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md`.
- Reviewer feedback coverage map:
  `review_revision/REVIEW_FEEDBACK_COVERAGE.md`.
- Calculation submission sequence:
  `review_revision/SUBMISSION_SEQUENCE.md`.
- A first batch of high-displacement MD snapshot DFT-check jobs was prepared in
  `review_revision/md_snapshot_dft_jobs/`.
- Nine high-displacement snapshot DFT checks completed with electronic
  convergence and no fatal marker. They include six Si4-graphene snapshots and
  three monovacancy snapshots, and are used only as sanity checks, not as
  diffusion-mechanism proof.
- Full-node fallback launchers were added for time-critical NEB and MD snapshot
  reruns:
  - `review_revision/submit_cpu_review_neb_fullnode_array.slurm`
  - `review_revision/submit_cpu_md_snapshot_dft_fullnode_array.slurm`

## Reviewer Issues Addressed By Current Evidence

1. **Missing test-set error and foundation-model baseline**
   - Fine-tuned all-family test force RMSE: 20.1 meV/A.
   - Foundation MACE-MP-0 all-family test force RMSE: 285.2 meV/A.
   - Force RMSE reduction: 92.9%.
   - Caveat: all-family energy RMSE remains 39.1 meV/atom because of a Si4-graphene energy offset.

2. **Missing committee or uncertainty diagnostic**
   - Three committee seeds completed.
   - Validation force RMSE by seed: 96.4, 107.2, and 48.4 meV/A.
   - Interpretation: fine-tuning helps substantially, but seed spread remains a caution for small-data MD claims.

3. **Wrapped-coordinate MD artifact**
   - Replaced the first-draft 10 ps wrapped-coordinate diagnostic with 15 unwrapped-coordinate 100 ps runs.
   - All 15 runs completed without LAMMPS errors, lost atoms, or NaNs.
   - A follow-up 18-run 200--500 ps GPU production set also completed without
     LAMMPS errors, lost atoms, NaNs, or dangerous neighbor-list builds.
   - Interpretation: report as finite-window stability/MSD diagnostics only, not converged diffusion coefficients.

4. **Overclaiming of fixed-geometry path scans**
   - Manuscript text now states that fixed-geometry path scans are endpoint/path-roughness descriptors, not migration barriers.
   - Relaxed CI-NEB jobs are running on the CPU partition.

## Current Reviewer-Response Route

The active manuscript now follows the conservative submission route. It reports
completed MACE validation and finite-window unwrapped MD diagnostics, while
deliberately withholding migration barriers, converged diffusion coefficients,
and high-displacement transport mechanisms. The running CPU VASP jobs can
strengthen a later kinetic version, but the conservative manuscript no longer
depends on them.

## Optional VASP Follow-Up For A Stronger Kinetic Version

Run the unified status checker with:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

1. **CI-NEB barriers**
   - Current NEB status snapshot: 10/10 paths have all intermediate image energies, 0/10 have converged, and 1/10 has a fatal marker.
   - The fatal path is `B2_Divacancy_path01_prior_li_xy_to_bridge_C_C`, which
     developed force blow-up and `SETYLM_AUG` internal VASP errors. Exclude it
     from interpretation.
   - B2 divacancy path02 has complete intermediate image energies and no formal
     fatal marker, but its last force diagnostic is huge (`g(F) = 7.26e5`) and
     it is also excluded from barrier interpretation.
   - The original low-rank array tasks 0-3 are no longer in the current
     `squeue` snapshot.
   - The not-yet-started original low-rank tasks 4-9 were canceled before they
     wrote any `vasp.log` files and resubmitted as 60-rank full-node array
     `3115996_[4-9%1]`.
   - Current full-node NEB state: `3115996_[6-9]` are running.
   - The active NEB tasks use 10 MPI ranks per NEB. Because the templates use
     `IMAGES = 5`, this gives only about two ranks per intermediate image and
     is slow. The 60-rank full-node fallback launcher should not be pointed at
     directories currently being written by active jobs.
   - Run this after jobs finish:
     ```bash
     cd /home/xh121/Li-vasp
     python review_revision/collect_neb_results.py --output-dir results/review_revision/neb_analysis_final
     ```

2. **DFT checks of high-displacement MD snapshots**
   - Highest priority: the Si4-graphene 20260427 trajectory, because it dominates the 100 ps MSD scale.
   - Purpose: verify that the high-displacement configurations are not MACE extrapolation artifacts.
   - Prepared jobs: 9 single-point VASP checks selected from the three largest-MSD runs.
   - Initially submitted as Slurm job array `3115985` on `et2024`, then
     partially moved to the higher-rank fallback array `3115998`.
   - The original `3115985_0` run used a `2 2 1` k-point mesh and was canceled after slow startup with no parsed SCF energy; its outputs were moved to `slow_2x2x1_backup/`.
   - All active/pending snapshot checks now use Gamma-only (`1 1 1`) for faster qualitative DFT sanity checks.
   - Current scheduler state: no MD snapshot DFT job is visible in `squeue`.
   - The not-yet-started 16-rank pending snapshot tasks `3115985_2-8` and
     `3115993_0` were canceled before writing any `vasp.log` files and
     resubmitted as 32-rank/192G array `3115998_[0,2-8%2]`.
   - The collector now separates in-progress SCF energies from usable DFT
     energies. Nine of nine snapshots have completed with usable
     electronically converged energies and no fatal markers. They are included
     only as DFT sanity checks of selected high-displacement snapshots.
   - A 64-rank full-node fallback launcher is available if the 16-rank snapshot
     checks remain too slow. It refuses to overwrite an existing `vasp.log`
     unless `RESTART_EXISTING=1` is set deliberately.
   - Check status:
     ```bash
     cd /home/xh121/Li-vasp
     review_revision/check_reviewer_jobs.sh
     ```
   - Collect partial/final results:
     ```bash
     python review_revision/collect_md_snapshot_dft_checks.py \
       --output-dir results/review_revision/md_snapshot_dft_analysis_current
     ```

3. **Final manuscript and response letter**
   - Conservative route: use the current manuscript and response draft, which
     omit final barrier/diffusion claims.
   - Stronger kinetic route: update the manuscript again after final NEB
     barriers and snapshot DFT checks are available.
   - The submission-facing point-by-point response draft is:
     `review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md`.
   - Supporting internal status and result files are:
     - `results/review_revision/gpu_analysis/REVIEWER_GPU_ANALYSIS.md`
     - `results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md`
     - `review_revision/REVIEWER_RESPONSE_STATUS.md`
     - `review_revision/RESPONSE_LETTER_DRAFT.md`
   - If all CI-NEB jobs converge later, add:
     `results/review_revision/neb_analysis_final/REVIEW_NEB_STATUS.md`.

## Current Scientific Boundary

The revised evidence supports local fixed-geometry energy screening, target-domain force-field validation, and finite-window MD stability diagnostics. It does not yet support final Li migration barriers, converged diffusion coefficients, voltage/capacity claims, or practical Si-graphene anode performance claims.

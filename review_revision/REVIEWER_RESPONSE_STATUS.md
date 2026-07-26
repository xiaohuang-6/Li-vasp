# Reviewer-Response Status

Last updated: 2026-07-26

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
- The local RTX 5080 reviewer follow-up return package
  `incoming_gpu_results/local_5080_referee_followup_results_20260725_2309.tar.gz`
  was copied, extracted, and accepted for diagnostic use. SHA256:
  `35ac20123795f978c64ee7a5266eba1e96c40a9ca954da99be742e0039edb0d2`.
- Cleaned grouped-E0 snapshot-force outputs are in
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/`.
  This cleaned directory intentionally omits stale `*_failed_snapshots.csv`
  files from an earlier failed evaluator attempt; the later 23:07--23:08
  summary/error CSVs contain the accepted 9 frames x 3 models result set.
- PBE-D3/dipole adsorption-energy single points completed for all five
  families. Results are in
  `results/review_revision/adsorption_energy_analysis/`: 11/11 component jobs
  usable, 0 fatal markers, and 5/5 family-level `E_ads` values usable.
- Submission-facing response letter draft:
  `review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md`.
- Reviewer feedback coverage map:
  `review_revision/REVIEW_FEEDBACK_COVERAGE.md`.
- Calculation submission sequence:
  `review_revision/SUBMISSION_SEQUENCE.md`.
- A first batch of high-displacement MD snapshot DFT-check jobs was prepared in
  `review_revision/md_snapshot_dft_jobs/`.
- Nine high-displacement snapshot DFT checks from the initial 100 ps campaign
  completed with electronic convergence, no fatal marker, and ASE-readable
  forces. They include six Si4-graphene snapshots and three monovacancy
  snapshots, and are used only as traceable out-of-domain stress tests, not as
  diffusion-mechanism proof or production-trajectory validation.
- Full-node fallback launchers were added for time-critical NEB and MD snapshot
  reruns:
  - `review_revision/submit_cpu_review_neb_fullnode_array.slurm`
  - `review_revision/submit_cpu_md_snapshot_dft_fullnode_array.slurm`

## Reviewer Issues Addressed By Current Evidence

1. **Missing test-set error and foundation-model baseline**
   - Fine-tuned all-family same-workflow test force RMSE: 20.1 meV/A.
   - Foundation MACE-MPA-0 all-family test force RMSE: 285.2 meV/A.
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
   - Interpretation: report as finite-window runtime-completion/MSD diagnostics only, not converged diffusion coefficients.

4. **Overclaiming of fixed-geometry path scans**
   - Manuscript text now states that fixed-geometry path scans are endpoint/path-roughness descriptors, not migration barriers.
   - Relaxed CI-NEB jobs are running on the CPU partition.

5. **Grouped-split E0 and direct snapshot-force stress test**
   - Grouped-E0 fine-tune completed on the local RTX 5080 and produced both the
     MACE model and LAMMPS TorchScript model.
   - Same grouped test split force RMSEs from the accepted first-stage
     grouped-E0 checkpoint are 19.6, 10.9, 13.7, 42.9, and 9.2 meV/A for
     A Perfect, B1 Monovacancy, B2 Divacancy, C Stone-Wales, and D
     Si4-graphene, respectively.
   - Direct high-displacement snapshot force validation remains mixed:
     `grouped_e0` improves D Si4-graphene force RMSE to 113.6 meV/A over six
     snapshots, but B1 monovacancy remains poor at 1107.0 meV/A over three
     snapshots. Treat this as an out-of-domain diagnostic and caution, not
     proof of a high-displacement transport mechanism.

6. **PBE-D3/dipole adsorption-energy anchors**
   - All adsorption-energy components completed with electronic convergence and
     no fatal VASP marker.
   - Usable `E_ads` values per Li are -0.633524 eV (A Perfect), -3.114948 eV
     (B1 Monovacancy), -1.327739 eV (B2 Divacancy), 0.009397 eV
     (C Stone-Wales), and -3.348858 eV (D Si4-graphene).
   - These are single-geometry adsorption-energy anchors, not voltage,
     capacity, clustering, or migration-barrier claims.

## Current Reviewer-Response Route

The active manuscript now follows a validation-first submission route. It
reports completed MACE validation, PBE-D3/dipole adsorption-energy anchors,
finite-window unwrapped MD diagnostics, and direct DFT snapshot stress tests,
while deliberately withholding migration barriers, converged diffusion
coefficients, and high-displacement transport mechanisms. Remaining CPU VASP
jobs can strengthen a later kinetic version, but the manuscript does not depend
on them.

## Current 24h Follow-Up Audit

Last checked with the collectors and Slurm status at 03:09 EDT on
2026-07-26.

- No matching cluster GPU jobs are present. The grouped-E0 MACE fine-tune and
  snapshot force-evaluation diagnostics were completed manually on the local
  RTX 5080 workstation from `local_5080_referee_followup_pack_20260725_1825.tar.gz`.
  Do not submit follow-up GPU work on the cluster.
- Adsorption-energy single points from Slurm array `3129645` (`li-ads-sp`,
  24h limit) are complete: 11/11 single-point components completed with usable
  converged energies, 0/11 fatal markers, and 5/5 complete family-level
  `E_ads` values usable. No `li-ads-sp` task remains in the current `squeue`
  snapshot.
- Fast 3-image Gamma-only CI-NEB fallback array `3129657` (`li-fast-neb`,
  24h limit) completed at the scheduler level with exit code 0 for all five
  tasks. The VASP collector still reports 0/5 formally converged and 0/5 fatal;
  all five paths reached 80 ionic steps. Barrier values remain blank.
- Production-trajectory high-displacement DFT snapshot checks are active as CPU
  Slurm array `3129676` (`li-md-dftcheck`, 24h limit): 4 running, 1 pending,
  2/7 completed and usable, 0/7 fatal. The two usable rows are
  `D_SiGraphene_seed20260427_step057000` and
  `D_SiGraphene_seed20260427_step500000`; both come from the same trajectory,
  so they are not enough for a production-set validation claim.
- The older optional full-node NEB jobs `3115996_6`--`3115996_9` had 48h
  limits and were canceled on 2026-07-25 to keep the active
  reviewer-follow-up queue inside the 24h operating constraint.
- Current manuscript rule: adsorption energies can be used as single-geometry
  PBE-D3/dipole anchors. Continue to use NEB barriers or production-set
  snapshot DFT claims only after the corresponding collectors mark those rows
  usable.

## Optional VASP Follow-Up For A Stronger Kinetic Version

Run the unified status checker with:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

1. **CI-NEB barriers**
   - Current full NEB status snapshot: 10/10 paths have all intermediate image energies, 0/10 have converged, and 1/10 has a fatal marker.
   - Current fast NEB status snapshot: 5/5 paths have all intermediate image
     energies, 0/5 have converged, and 0/5 have fatal markers.
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
   - Current full-node NEB state: no `3115996` full-node NEB tasks remain in
     `squeue`; `3115996_6`--`3115996_9` were canceled after the user restored
     the 24h-only constraint for active follow-up work.
   - The manuscript remains gated on collector-usable NEB rows. Do not point
     the 60-rank full-node fallback launcher at these directories unless a new
     explicit longer-running kinetic follow-up is opened.
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
   - Current scheduler state: the initial-campaign snapshot set is complete;
     production-trajectory high-displacement snapshot jobs are submitted or
     pending separately.
   - The not-yet-started 16-rank pending snapshot tasks `3115985_2-8` and
     `3115993_0` were canceled before writing any `vasp.log` files and
     resubmitted as 32-rank/192G array `3115998_[0,2-8%2]`.
   - The collector now separates in-progress SCF energies from usable DFT
     energies. Nine of nine initial-campaign snapshots have completed with
     usable electronically converged energies, ASE-readable forces, and no
     fatal markers. The evidence archive records per-row OUTCAR hashes.
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
   - Validation-first route: use the current manuscript and response draft, which
     omit final barrier/diffusion claims.
   - Stronger kinetic route: update the manuscript again after final NEB
     barriers and snapshot DFT checks are available.
   - The submission-facing point-by-point response draft is:
     `review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md`.
   - Supporting internal status and result files are:
     - `results/review_revision/adsorption_energy_analysis/ADSORPTION_ENERGY_STATUS.md`
     - `results/review_revision/gpu_analysis/REVIEWER_GPU_ANALYSIS.md`
     - `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/SNAPSHOT_MACE_FORCE_VALIDATION.md`
     - `results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md`
     - `review_revision/REVIEWER_RESPONSE_STATUS.md`
     - `review_revision/RESPONSE_LETTER_DRAFT.md`
   - If all CI-NEB jobs converge later, add:
     `results/review_revision/neb_analysis_final/REVIEW_NEB_STATUS.md`.

## Current Scientific Boundary

The revised evidence supports a validation-first workflow for local
fixed-geometry energy screening,
single-geometry PBE-D3/dipole adsorption-energy anchors, target-domain
force-model diagnostics, finite-window MD runtime/displacement diagnostics, and a
direct out-of-domain snapshot-force stress test. It does not yet
support final Li migration barriers, converged diffusion coefficients,
voltage/capacity claims, high-displacement transport mechanisms, or practical
Si-graphene anode performance claims.

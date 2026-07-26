# Draft Response To Reviewers

Status: **validation-first revision draft**. This version is designed to remain scientifically defensible even if the CPU VASP follow-up jobs do not finish before submission. If final CI-NEB or production-snapshot DFT results become available, they can be added as optional strengthening evidence.

## Overview Of Major Revision

We thank the reviewers for identifying several issues in the first draft, especially the misuse of fixed-geometry path-scan energies as migration barriers, the lack of foundation-model comparison, and the wrapped-coordinate MD artifact. We have revised the manuscript from a quantitative Li-diffusion claim into a validation-first local-energy and MACE workflow. We removed claims of converged Li diffusivity, practical anode performance, and finalized migration barriers. We now report foundation-model baselines, same-workflow held-out test-set errors, committee fine-tuning diagnostics, leakage-audited split generation, first-principles adsorption anchors, and DFT snapshot stress tests.

The following new evidence is now in the workspace:

- MACE foundation-vs-fine-tuned evaluation: `results/review_revision/gpu_analysis/REVIEWER_GPU_ANALYSIS.md`
- MACE evaluator CSVs: `results/review_revision/mace_eval/`
- Committee models and logs: `models/review_revision/`, `logs/reviewer_gpu_5080_local/`
- 100 ps unwrapped MD outputs: `review_revision/md_outputs/`, `review_revision/md_logs/`, `trajectories/review_revision/`
- PBE-D3(BJ)/dipole adsorption-energy status and tables:
  `results/review_revision/adsorption_energy_analysis/`
- Grouped-E0 snapshot-force diagnostics:
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/`
- Current CI-NEB status: `results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md`
- Current MD snapshot DFT-check status: `results/review_revision/md_snapshot_dft_analysis_current/MD_SNAPSHOT_DFT_STATUS.md`

Two calculation classes remain pending as optional follow-up evidence:

1. Relaxed VASP CI-NEB jobs for migration-barrier claims.
2. Production-trajectory VASP single-point checks on high-displacement MD
   snapshots to test possible MACE extrapolation.

The validation-first manuscript does not rely on either pending result. It removes finalized migration barriers, converged diffusion coefficients, and practical anode-performance claims.

## Reviewer Issue 1: The Reported "Barriers" Were Endpoint Energy Differences

**Reviewer concern.** The first draft called fixed-geometry path-scan endpoint differences "migration barriers"; several reported values were exactly equal to `|Delta E_end-start|`, proving that the path maximum occurred at an endpoint rather than at a saddle point.

**Response.** We agree. The revised manuscript no longer describes the fixed-geometry path scans as activation barriers. The title, abstract, Results, Table 3 discussion, and Conclusion now state that these quantities are fixed-geometry endpoint/path-roughness descriptors only. We explicitly state that the 0.040 eV pristine graphene and 0.020 eV Stone-Wales values cannot be used to claim low Li migration barriers.

**Manuscript change.** We rewrote the fixed-geometry path section to say that physically meaningful migration-barrier claims require relaxed minimum-energy paths, preferably CI-NEB, and comparison with prior graphene literature. Because no completed CI-NEB result is used in the present manuscript, migration-barrier values are deliberately withheld rather than reported from preliminary paths.

**Optional follow-up calculation.** The completed fast CI-NEB array reached all image energies for 5/5 paths but 0/5 formal ionic convergence markers; every path reached its 80-step limit, so no barrier is usable. The older full CI-NEB set has all intermediate image energies for 10/10 paths, 0/10 formal convergence, and 1 fatal marker. The fatal case is `B2_Divacancy_path01_prior_li_xy_to_bridge_C_C`, which developed force blow-up and `SETYLM_AUG` internal VASP errors; it is excluded from interpretation. The collector leaves barrier columns blank until a path has all images, ionic convergence, and no fatal marker. No partial value is used in the manuscript.

## Reviewer Issue 2: Missing Held-Out Test Error And Foundation Baseline

**Reviewer concern.** The first draft only reported validation error and did not compare against the unfine-tuned MACE-MPA-0 foundation model.

**Response.** We agree and have added same-workflow held-out test-set and foundation-model evaluation. Fine-tuning reduces the all-family test force RMSE from 285.2 meV/A for the unfine-tuned MACE-MPA-0 model to 20.1 meV/A, a 92.9% reduction. Family-level test force RMSE values for the fine-tuned model are 12.7, 16.3, 29.3, 19.3, and 6.8 meV/A for pristine graphene, monovacancy graphene, divacancy graphene, Stone-Wales graphene, and the Si4-graphene motif, respectively.

**Caveat.** The all-family energy RMSE remains 39.1 meV/atom, mainly because the Si4-graphene family has a systematic energy offset while retaining low force error. We therefore emphasize force validation for MD stability diagnostics and do not use this model to claim precise absolute thermodynamics.

**Manuscript change.** The Results section now includes a foundation-versus-fine-tuned force RMSE plot and a table of external evaluator metrics. The revised text explicitly states that the original split is a same-workflow diagnostic, not a final independent transferability benchmark. A grouped-split, foundation-assisted-E0 retraining run also completed; the first-stage grouped-E0 checkpoint on its small grouped test split has force RMSEs of 19.6, 10.9, 13.7, 42.9, and 9.2 meV/A for pristine graphene, monovacancy graphene, divacancy graphene, Stone-Wales graphene, and the Si4-graphene motif, respectively. Because the grouped test set is only five frames and high-displacement snapshot errors remain mixed, this run is presented as a diagnostic audit rather than final force-field validation.

## Reviewer Issue 3: Missing Committee Or Uncertainty Diagnostic

**Reviewer concern.** The first draft did not quantify seed-to-seed uncertainty or model sensitivity.

**Response.** We trained a three-member fine-tuning committee. All three seeds completed successfully. Validation force RMSE values are 96.4, 107.2, and 48.4 meV/A for seeds 20260427, 20260428, and 20260429.

**Interpretation.** The committee confirms that fine-tuning improves the target domain relative to the foundation model, but the seed spread remains significant. We therefore use committee results as a caution against overinterpreting individual finite-temperature trajectories.

**Manuscript change.** The Results section now reports the committee validation spread and explicitly states that the small dataset limits transferability.

## Reviewer Issue 4: Wrapped-Coordinate MSD Artifact

**Reviewer concern.** The first draft plotted apparent Li displacement from wrapped coordinates, producing periodic-boundary artifacts and nonphysical sawtooth behavior.

**Response.** We agree and have replaced the first-draft wrapped-coordinate diagnostic with unwrapped-coordinate reviewer-response MD. We ran 15 trajectories: five structures, three velocity seeds, 400 K, 100 ps each. All 15 completed without LAMMPS errors, lost atoms, or NaNs.

**Key numbers.** Mean final in-plane Li MSD values are:

- Pristine graphene: 32.8 +/- 3.1 A^2
- Monovacancy graphene: 132.5 +/- 77.2 A^2
- Divacancy graphene: 76.4 +/- 70.0 A^2
- Stone-Wales graphene: 4.5 +/- 2.3 A^2
- Si4-graphene motif: 974.8 +/- 1462.3 A^2

**Interpretation.** These are finite-window displacement diagnostics, not converged diffusion coefficients. The Si4-graphene motif has very large seed-to-seed variability, dominated by individual high-displacement trajectories. We therefore do not use these trajectories to claim quantitative diffusivity or fast practical transport.

**Manuscript change.** The MD section now reports the 100 ps unwrapped-coordinate trajectories plus a follow-up 18-run 200--500 ps extended MD diagnostic set, with explicit language that the results are finite-window diagnostics and not converged diffusion coefficients.

## Reviewer Issue 5: Possible MACE Extrapolation In High-Displacement MD

**Reviewer concern.** Large MD displacements or energy changes could reflect MLIP out-of-domain behavior rather than physical reconstruction or transport.

**Response.** We agree that direct DFT checks are needed before interpreting high-displacement MD as a physical transport mechanism. In the validation-first revision, we therefore do not claim that the large-displacement trajectories prove fast Li transport or a robust Si4-graphene diffusion mechanism. We prepared nine VASP single-point checks from the initial 100 ps trajectory campaign, prioritizing the Si4-graphene seed 20260427 trajectory that dominated that initial campaign. These rows are now described explicitly as initial-campaign checks, not as validation of the later 200--500 ps production trajectories.

**Current status.** The DFT snapshot checks were submitted on `et2024`. The original first snapshot used a `2 2 1` k-point mesh and was canceled after slow startup with no parsed SCF energy; its partial outputs were backed up under `slow_2x2x1_backup/`. The accepted checks use Gamma-only (`1 1 1`) for qualitative DFT stress tests. Nine of nine current OUTCAR files have `completed = True`, `electronic_converged_marker = True`, no fatal markers, and ASE-readable forces. The evidence archive records OUTCAR SHA256 hashes for every energy reported in the manuscript table. These include six Si4-graphene snapshots and three monovacancy snapshots, with MSDxy values from 207.6 to 2694.8 A^2. A simple geometry screen found no sub-A atom overlaps; the monovacancy snapshots contain C-C contacts of 1.204, 1.212, and 1.217 A, and one Si4-graphene snapshot contains a Si-Si contact of 1.994 A. Foundation-model MACE-vs-DFT force errors are large on these rows. The grouped-E0 model improves the Si4-graphene snapshot force RMSE to 113.6 meV/A, but monovacancy remains poor at 1107.0 meV/A and the all-snapshot value remains 645.8 meV/A. These rows are therefore framed as out-of-domain stress tests, not as proof of a diffusion mechanism. Results are collected with:

```bash
python review_revision/collect_md_snapshot_dft_checks.py \
  --output-dir results/review_revision/md_snapshot_dft_analysis_current
```

**Manuscript change.** The MD section now describes these trajectories as finite-window stability and displacement diagnostics only. It adds a nine-row table of completed high-displacement snapshot DFT sanity checks and states that quantitative diffusion claims would still require longer trajectories, larger cells, independent Li concentrations, and additional representative DFT snapshot checks.

## Reviewer Issue 6: Overclaiming Anode Performance And Si-Graphene Composite Scope

**Reviewer concern.** The first draft overclaimed silicon-graphene composite anode performance from a Si4-graphene local motif and one-Li dilute models.

**Response.** We agree and have narrowed the language. The manuscript now describes the Si-containing structure as a "Si4-graphene motif", not a representative silicon-graphene composite anode. We removed unsupported claims about mechanical/electronic favorability, voltage, capacity, practical anode performance, and converged lithium mobility.

**Manuscript change.** The Abstract, Introduction, Results, and Conclusion now state that the defensible claim is local adsorption-energy screening plus target-domain MACE diagnostics, not practical anode prediction. The manuscript reports the completed PBE-D3(BJ)/dipole single-point adsorption-energy anchors only as dilute-limit single-geometry values, not as voltage, capacity, clustering, or migration-barrier evidence.

## Reviewer Issue 7: Reproducibility And Workflow Documentation

**Reviewer concern.** The first draft lacked enough parameter and workflow detail to reproduce the results.

**Response.** We expanded the workflow documentation and made the scripts explicit:

- `review_revision/analyze_reviewer_gpu_results.py`
- `review_revision/collect_neb_results.py`
- `review_revision/prepare_md_snapshot_dft_checks.py`
- `review_revision/collect_md_snapshot_dft_checks.py`
- `review_revision/prepare_adsorption_energy_jobs.py`
- `review_revision/collect_adsorption_energies.py`
- `review_revision/submit_cpu_review_neb_array.slurm`
- `review_revision/submit_cpu_md_snapshot_dft_array.slurm`

The current reviewer-response status is tracked in `review_revision/REVIEWER_RESPONSE_STATUS.md`.
The cleaner submission-facing point-by-point draft is `review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md`.
The calculation submission order is summarized in `review_revision/SUBMISSION_SEQUENCE.md`.

## Final Submission Checklist

- [x] Copy back, extract, and analyze local GPU reviewer results.
- [x] Add foundation baseline and held-out test metrics.
- [x] Add three-seed committee diagnostics.
- [x] Replace wrapped-coordinate MD artifact with unwrapped-coordinate 100 ps diagnostics.
- [x] Submit MD high-displacement snapshot DFT checks.
- [x] Finish and collect PBE-D3(BJ)/dipole adsorption-energy single points.
- [ ] Optional: finish and collect VASP CI-NEB barriers if kinetic claims are restored.
- [ ] Optional: finish and collect production-trajectory MD snapshot DFT checks if high-displacement mechanisms are interpreted.
- [x] Remove final NEB and production-snapshot dependence from the validation-first manuscript.
- [x] Compile final PDF with a temporary Tectonic engine and inspect rendered pages.
- [x] Convert this draft into a submission-facing point-by-point response letter.

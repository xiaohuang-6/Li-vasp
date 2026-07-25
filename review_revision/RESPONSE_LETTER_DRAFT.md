# Draft Response To Reviewers

Status: **conservative revision draft**. This version is designed to remain scientifically defensible even if the running CPU VASP follow-up jobs do not finish before submission. If final CI-NEB or snapshot-DFT results become available, they can be added as an optional strengthening revision.

## Overview Of Major Revision

We thank the reviewers for identifying several issues in the first draft, especially the misuse of fixed-geometry path-scan energies as migration barriers, the lack of independent MACE validation, and the wrapped-coordinate MD artifact. We have revised the manuscript to narrow the scientific claim from quantitative Li diffusion in defective graphene/Si-graphene anodes to a conservative local-energy and MACE-validation workflow. We removed claims of converged Li diffusivity, practical anode performance, and finalized migration barriers. We now report foundation-model baselines, held-out test-set errors, committee fine-tuning diagnostics, and unwrapped-coordinate multi-seed 100 ps MD diagnostics.

The following new evidence is now in the workspace:

- MACE foundation-vs-fine-tuned evaluation: `results/review_revision/gpu_analysis/REVIEWER_GPU_ANALYSIS.md`
- MACE evaluator CSVs: `results/review_revision/mace_eval/`
- Committee models and logs: `models/review_revision/`, `logs/reviewer_gpu_5080_local/`
- 100 ps unwrapped MD outputs: `review_revision/md_outputs/`, `review_revision/md_logs/`, `trajectories/review_revision/`
- Current CI-NEB status: `results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md`
- Current MD snapshot DFT-check status: `results/review_revision/md_snapshot_dft_analysis_current/MD_SNAPSHOT_DFT_STATUS.md`

Two calculations remain pending as optional follow-up evidence:

1. Relaxed VASP CI-NEB jobs for migration-barrier claims.
2. VASP single-point checks on high-displacement MD snapshots to test possible MACE extrapolation.

The conservative manuscript does not rely on either pending result. It removes finalized migration barriers, converged diffusion coefficients, and practical anode-performance claims.

## Reviewer Issue 1: The Reported "Barriers" Were Endpoint Energy Differences

**Reviewer concern.** The first draft called fixed-geometry path-scan endpoint differences "migration barriers"; several reported values were exactly equal to `|Delta E_end-start|`, proving that the path maximum occurred at an endpoint rather than at a saddle point.

**Response.** We agree. The revised manuscript no longer describes the fixed-geometry path scans as activation barriers. The title, abstract, Results, Table 1 discussion, and Conclusion now state that these quantities are fixed-geometry endpoint/path-roughness descriptors only. We explicitly state that the 0.040 eV pristine graphene and 0.020 eV Stone-Wales values cannot be used to claim low Li migration barriers.

**Manuscript change.** We rewrote the fixed-geometry path section to say that physically meaningful migration-barrier claims require relaxed minimum-energy paths, preferably CI-NEB, and comparison with prior graphene literature. Because no completed CI-NEB result is used in the present manuscript, migration-barrier values are deliberately withheld rather than reported from preliminary paths.

**Optional follow-up calculation.** Relaxed CI-NEB jobs are currently running on `et2024`. Current partial status is 5/10 paths with complete intermediate image energies, 0/10 formally converged, and 1 fatal marker. The fatal case is `B2_Divacancy_path01_prior_li_xy_to_bridge_C_C`, which developed force blow-up and `SETYLM_AUG` internal VASP errors; it is excluded from interpretation. Only one of the five partially collected paths is currently below the force-threshold diagnostic, and VASP has not printed a formal convergence/completion marker. These partial values are not used in the manuscript. If the jobs finish, the response and manuscript can be strengthened with `results/review_revision/neb_analysis_final/REVIEW_NEB_STATUS.md`.

## Reviewer Issue 2: Missing Held-Out Test Error And Foundation Baseline

**Reviewer concern.** The first draft only reported validation error and did not compare against the unfine-tuned MACE-MP-0 foundation model.

**Response.** We agree and have added independent held-out test-set and foundation-model evaluation. Fine-tuning reduces the all-family test force RMSE from 285.2 meV/A for the unfine-tuned MACE-MP-0 model to 20.1 meV/A, a 92.9% reduction. Family-level test force RMSE values for the fine-tuned model are 12.7, 16.3, 29.3, 19.3, and 6.8 meV/A for pristine graphene, monovacancy graphene, divacancy graphene, Stone-Wales graphene, and the Si4-graphene motif, respectively.

**Caveat.** The all-family energy RMSE remains 39.1 meV/atom, mainly because the Si4-graphene family has a systematic energy offset while retaining low force error. We therefore emphasize force validation for MD stability diagnostics and do not use this model to claim precise absolute thermodynamics.

**Manuscript change.** The Results section now includes a foundation-versus-fine-tuned force RMSE plot and a table of independent evaluator metrics.

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

**Interpretation.** These are short-window displacement diagnostics, not converged diffusion coefficients. The Si4-graphene motif has very large seed-to-seed variability, dominated by one seed. We therefore do not use these trajectories to claim quantitative diffusivity or fast practical transport.

**Manuscript change.** The MD section now reports the 100 ps unwrapped-coordinate traces and a short-window diagnostic table, with explicit language that the results are not converged diffusion coefficients.

## Reviewer Issue 5: Possible MACE Extrapolation In High-Displacement MD

**Reviewer concern.** Large MD displacements or energy changes could reflect MLIP out-of-domain behavior rather than physical reconstruction or transport.

**Response.** We agree that direct DFT checks are needed before interpreting high-displacement MD as a physical transport mechanism. In the conservative revision, we therefore do not claim that the large-displacement trajectories prove fast Li transport or a robust Si4-graphene diffusion mechanism. We prepared nine VASP single-point checks from the three largest-MSD runs, prioritizing the Si4-graphene seed 20260427 trajectory that dominates the displacement scale. Eight snapshots have now completed as usable spin-polarized DFT single-point sanity checks.

**Current status.** The DFT snapshot checks were submitted on `et2024`. The original first snapshot used a `2 2 1` k-point mesh and was canceled after slow startup with no parsed SCF energy; its partial outputs were backed up under `slow_2x2x1_backup/`. All active and pending snapshot checks now use Gamma-only (`1 1 1`) for faster qualitative DFT sanity checks. Eight of nine snapshots have completed with `completed = True`, `electronic_converged_marker = True`, and no fatal markers. These include five Si4-graphene snapshots and three monovacancy snapshots, with MSDxy values from 207.6 to 2683.4 A^2. A simple geometry screen found no sub-A atom overlaps, but the monovacancy snapshots contain short C-C contacts around 1.20--1.22 A and one Si4-graphene snapshot contains a short Si-Si contact around 1.99 A. These results are included only as DFT sanity checks, not as proof of a diffusion mechanism. One snapshot remains incomplete. Results are collected with:

```bash
python review_revision/collect_md_snapshot_dft_checks.py \
  --output-dir results/review_revision/md_snapshot_dft_analysis_current
```

**Manuscript change.** The MD section now describes these trajectories as short-window stability and displacement diagnostics only. It adds an eight-row table of completed high-displacement snapshot DFT sanity checks and states that quantitative diffusion claims would still require longer trajectories, larger cells, independent Li concentrations, and additional representative DFT snapshot checks.

## Reviewer Issue 6: Overclaiming Anode Performance And Si-Graphene Composite Scope

**Reviewer concern.** The first draft overclaimed silicon-graphene composite anode performance from a Si4-graphene local motif and one-Li dilute models.

**Response.** We agree and have narrowed the language. The manuscript now describes the Si-containing structure as a "Si4-graphene motif", not a representative silicon-graphene composite anode. We removed unsupported claims about mechanical/electronic favorability, voltage, capacity, practical anode performance, and converged lithium mobility.

**Manuscript change.** The Abstract, Introduction, Results, and Conclusion now state that the defensible claim is local fixed-geometry energy screening plus target-domain MACE validation, not practical anode prediction.

## Reviewer Issue 7: Reproducibility And Workflow Documentation

**Reviewer concern.** The first draft lacked enough parameter and workflow detail to reproduce the results.

**Response.** We expanded the workflow documentation and made the scripts explicit:

- `review_revision/analyze_reviewer_gpu_results.py`
- `review_revision/collect_neb_results.py`
- `review_revision/prepare_md_snapshot_dft_checks.py`
- `review_revision/collect_md_snapshot_dft_checks.py`
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
- [ ] Optional: finish and collect VASP CI-NEB barriers if kinetic claims are restored.
- [ ] Optional: finish and collect MD snapshot DFT checks if high-displacement mechanisms are interpreted.
- [x] Remove final NEB and DFT-check dependence from the conservative manuscript.
- [ ] Compile final PDF after a TeX engine is available.
- [x] Convert this draft into a submission-facing point-by-point response letter.

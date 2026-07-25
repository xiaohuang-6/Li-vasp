# Response To Reviewers

We thank the reviewers for their careful and constructive assessment. The revised manuscript has been substantially narrowed so that the claims match the evidence now available. In particular, we no longer present fixed-geometry path scans as Li migration barriers, no longer claim converged diffusion coefficients or practical anode performance, and no longer interpret short molecular dynamics trajectories as definitive transport mechanisms. The manuscript now presents a conservative DFT--MACE workflow for local Li--C--Si energy screening and target-domain force-field validation.

## Comment 1: Fixed-Geometry Path Scans Were Misidentified As Migration Barriers

We agree. The original path-span values were endpoint/path-roughness descriptors from frozen Cartesian interpolation scans, not relaxed minimum-energy-path barriers. In several cases, the reported path span equaled the endpoint energy difference, demonstrating that the maximum and minimum occurred at the endpoints rather than at an independent saddle point.

The revised manuscript removes migration-barrier claims from the abstract, results, tables, and conclusion. The relevant section is now titled "Endpoint energy differences, not migration barriers", and Table 1 is relabeled as fixed-geometry path-scan descriptors. We explicitly state that the pristine graphene and Stone--Wales values cannot be used to claim low Li migration barriers, and that meaningful kinetic comparison requires relaxed CI-NEB paths benchmarked against prior graphene literature.

## Comment 2: Missing Test-Set Error, Foundation-Model Baseline, And Uncertainty Diagnostics

We agree. The revised manuscript now reports independent held-out test-set errors and a direct comparison with the unfine-tuned MACE-MP-0 foundation model. Fine-tuning reduces the all-family held-out force RMSE from 285.2 to 20.1 meV A^-1. The all-family energy RMSE remains 39.1 meV atom^-1, mainly due to a systematic Si4--graphene family offset, and this limitation is now discussed explicitly.

We also added a three-seed committee diagnostic. The committee validation force RMSE values are 96.4, 107.2, and 48.4 meV A^-1. The manuscript uses this spread as a caution against overinterpreting individual finite-temperature trajectories.

## Comment 3: Wrapped-Coordinate MSD Artifact And Insufficient MD Statistics

We agree. The revised analysis replaces the wrapped-coordinate 10 ps trajectories with 15 unwrapped-coordinate 400 K NVT trajectories: five structures times three velocity seeds, 100 ps each. All 15 trajectories completed without LAMMPS errors, lost atoms, or NaNs. A follow-up GPU production set further completed 18/18 target-length 200--500 ps trajectories without LAMMPS errors, lost atoms, NaNs, or dangerous neighbor-list builds.

The revised manuscript reports these trajectories only as finite-window stability and displacement diagnostics. It no longer reports them as converged diffusion coefficients and no longer claims fast practical Li transport. The MD section also clarifies that the 2 x 2 x 1 replicated cells contain multiple Li atoms and periodic defect copies, so the trajectories are not concentration-converged electrode models.

## Comment 4: Possible MLIP Extrapolation In High-Displacement Trajectories

We agree that high-displacement configurations require direct DFT checks before they can be interpreted as physical transport or reconstruction mechanisms. The revised manuscript therefore removes claims that large-displacement trajectories prove fast Li transport, defect reconstruction, or a robust Si4--graphene diffusion mechanism.

Representative DFT snapshot checks have been prepared as follow-up validation, and nine high-displacement snapshots have now completed as usable spin-polarized DFT single-point sanity checks. These include six Si4--graphene snapshots and three monovacancy snapshots, spanning MSDxy values from 207.6 to 2694.8 A^2. All nine calculations reached electronic convergence and had no fatal markers. A simple geometry screen found no sub-A atom overlaps, although the monovacancy snapshots contain short C-C contacts of about 1.20--1.22 A and one Si4--graphene snapshot contains a short Si-Si contact of about 1.99 A. We use these results only to show that selected high-displacement snapshots are not immediate DFT input or electronic-convergence failures; they are not used to claim a diffusion mechanism or a converged diffusion coefficient.

## Comment 5: DFT Details, Structural Relaxation, And Literature Context

We expanded the Methods section to state the VASP setup, including PAW/PBE, spin polarization, ENCUT, k-point mesh, smearing, electronic and ionic convergence thresholds, LASPH, ADDGRID, and symmetry settings. The manuscript also explicitly states that the fixed-geometry scans do not include completed CI-NEB barriers and that the present labels did not include vdW or dipole corrections. These omissions are now treated as limitations rather than ignored sources of uncertainty.

The Introduction and Discussion now compare the study with prior DFT literature on Li adsorption and diffusion on graphene, vacancies, divacancies, Stone--Wales defects, Li clustering, and silicon-containing anode materials. The text emphasizes that the present Si-containing model is a Si4--graphene local motif, not a representative silicon--graphene composite anode.

## Comment 6: Overclaiming Battery-Anode Performance

We agree. The title, abstract, introduction, results, and conclusion have been rewritten to avoid claims about capacity, voltage, rate capability, cycling stability, practical anode performance, mechanical advantage, or electronic advantage. The revised manuscript states that a single-Li model on one graphene sheet is a dilute-limit local chemistry model and cannot establish realistic storage performance.

The conclusion now states that the defensible claim is local fixed-geometry energy screening plus target-domain MACE validation, not quantitative lithium diffusion or practical anode performance prediction.

## Comment 7: Reproducibility

We expanded the workflow documentation and generated reproducibility materials for the revision. The project now contains VASP preparation scripts, MACE evaluation scripts, committee training scripts, LAMMPS unwrapped-MD inputs, analysis scripts, processed CSV files, generated figures, and status summaries. The revised manuscript includes a Data and Code Availability section describing the reproducibility package to be archived with the final submission.

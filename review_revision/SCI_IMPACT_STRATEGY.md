# SCI Impact Strategy Review

Date: 2026-07-21

## Bottom Line

There is no way to guarantee SCI publication by making the manuscript more
conservative. The conservative revision improves scientific defensibility, but
it also lowers the impact from "Li diffusion mechanism in defective
graphene/Si-graphene anodes" to "local DFT--MACE screening and validation
workflow." That tradeoff is scientifically necessary with the current evidence,
because the stronger original claims are not supported by valid migration
barriers, converged diffusion coefficients, or DFT-checked high-displacement MD
mechanisms.

The right strategy is not to restore strong claims rhetorically. The right
strategy is to rebuild a smaller number of strong claims with targeted DFT
anchors.

## Current Manuscript Value

The current conservative manuscript has defensible value in four areas:

- It shows that MACE fine-tuning is necessary for the present Li--C--Si domain:
  test force RMSE improves from 285.2 to 20.1 meV/A.
- It reports a three-seed committee, which demonstrates useful but imperfect
  fine-tuning robustness.
- It includes PBE-D3/dipole single-point adsorption-energy anchors for all five
  current Li geometries.
- It replaces wrapped-coordinate artifacts with 15 unwrapped 100 ps MD
  diagnostics and adds an 18-run 200--500 ps GPU follow-up set. These runs
  complete without LAMMPS errors, lost atoms, or NaNs.
- It includes a local 5080 grouped-E0 force diagnostic for nine
  high-displacement DFT snapshots. This improves the Si4--graphene subset but
  remains poor for monovacancy, so it strengthens caution rather than mechanism
  claims.

This can support a modest computational workflow or screening manuscript. It is
unlikely to satisfy a higher-impact materials journal if presented as a full Li
diffusion or Si-graphene anode study, because the central physics remains
incomplete.

## Why The Strong Original Story Cannot Be Kept Yet

The original high-impact story would need at least one of the following:

- Relaxed CI-NEB migration barriers benchmarked against known graphene
  hollow-to-hollow Li diffusion literature.
- DFT single-point checks showing that high-displacement MACE MD snapshots are
  still physically reasonable and within the model domain.
- Longer/larger-cell MD that gives stable, approximately linear MSD behavior
  across multiple seeds and concentrations.
- Some electrochemical anchor such as Li metal reference, voltage, capacity, or
  clustering analysis if the manuscript claims anode performance.

The current evidence does not provide those anchors. Keeping the strong claims
without them would preserve apparent impact but would sharply increase rejection
risk.

## Computations That Actually Increase Impact

### Priority 1: Finish CPU CI-NEB

This is the most important path to restoring a real diffusion story. The
current NEB status is improving but not final:

- 10/10 paths have all intermediate image energies.
- 0/10 paths report formal ionic convergence.
- 1 fatal marker has been detected. The B2 divacancy path01 calculation
  developed force blow-up and `SETYLM_AUG` internal VASP errors and should be
  excluded from interpretation.
- B2 divacancy path02 has complete intermediate image energies but an
  unphysical force diagnostic (`g(F) = 7.26e5`) and should also be excluded
  from barrier interpretation.

Only formally converged NEB values should be added to the paper. Near-converged
or partial barriers should remain outside the manuscript.

If several paths converge, the title and results can be upgraded from
"fixed-geometry screening" to a more impactful but still honest claim:

> DFT-benchmarked MACE screening of local Li migration and trapping in defective
> graphene and Si4--graphene motifs.

### Priority 2: Finish MD Snapshot DFT Checks

These checks determine whether the largest MACE displacements are physical or
model extrapolation. The initial-campaign status is:

- 9/9 completed.
- 9/9 usable electronically converged energies.
- 0 fatal markers.
- Grouped-E0 direct force errors are mixed: the Si4--graphene subset improves
  to 113.6 meV/A, but monovacancy remains poor at 1107.0 meV/A.

Six high-displacement Si4--graphene snapshots and three monovacancy snapshots
have now converged without fatal VASP markers. This strengthens the MD section
as a DFT sanity check of selected high-displacement configurations, but the MD
must remain diagnostic until production-trajectory snapshots, a systematic
representative set, and longer statistics are available.

### Priority 3: Use The 5080 GPU Only After New DFT Anchors Exist

The current 5080 follow-up package has already been run and accepted. More MACE
MD on a 5080 is cheap relative to VASP, but it does not solve the core reviewer
concern unless the sampled configurations are DFT-checked.

Useful future 5080 tasks after new DFT checks:

- Extend selected stable systems from 100 ps to 0.5--1 ns with 3--5 seeds.
- Repeat at a larger cell or lower artificial Li concentration.
- Run the three committee models on the same MD initial conditions and compare
  qualitative displacement trends.
- If new DFT labels are added from NEB/snapshots, fine-tune a final model and
  rerun the evaluator.

Not useful by itself:

- Running longer MD before DFT snapshot checks. Longer trajectories can make an
  extrapolation artifact look more impressive, but not more credible.

## Recommended Two-Day Strategy

1. Let the running CPU NEB and production-snapshot DFT jobs continue. Do not
   restart active low-rank NEB jobs unless they fail or the user explicitly
   accepts losing the wall time already spent.
2. Collect NEB and snapshot DFT status every few hours with
   `review_revision/check_reviewer_jobs.sh`.
3. If any NEB path formally converges, collect final results and add only those
   converged barriers to the manuscript.
4. Use the completed snapshot checks only to support the narrow statement that
   selected high-displacement configurations are not immediate DFT input or
   electronic-convergence failures.
5. Use any future 5080 GPU work only as optional robustness evidence after new
   DFT anchors exist; it does not replace converged NEB barriers or systematic
   DFT snapshot validation.

## Final Decision

The current conservative manuscript is the correct fallback, but it should not
be treated as the highest-impact version. It is a defensible submission route if
time expires before DFT validation finishes. For a stronger SCI article, the
minimum upgrade is not more conservative wording and not more GPU MD alone; it
is final CPU DFT evidence: converged CI-NEB barriers plus DFT sanity checks of
representative production high-displacement MD snapshots.

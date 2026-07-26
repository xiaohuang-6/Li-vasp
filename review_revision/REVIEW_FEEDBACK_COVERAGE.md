# Review Feedback Coverage

This note maps the extracted reviewer feedback to the current validation-first
revision state.

## Covered In The Current Manuscript

- Fixed-geometry path spans are no longer called migration barriers.
- The manuscript no longer claims converged diffusion coefficients, practical anode performance, voltage, capacity, rate capability, cycling stability, mechanical advantage, or electronic advantage.
- `Si--graphene composite` language has been narrowed to a `Si4--graphene motif` wherever the model scope matters.
- The Introduction now states that a single-Li small-cell model cannot establish realistic storage performance, Li--Li clustering behavior, multilayer transport, electrolyte effects, or Si alloying.
- DFT details now include spin polarization, ENCUT, k-point mesh, smearing, convergence criteria, LASPH, ADDGRID, and ISYM.
- Missing vdW and dipole corrections in the MACE training labels are explicitly
  identified, and follow-up PBE-D3/dipole single-point adsorption-energy
  anchors are now reported for all five families.
- MACE validation now includes held-out test metrics, an unfine-tuned foundation baseline, family-level errors, and three-seed committee diagnostics.
- Wrapped-coordinate MD has been replaced by 100 ps unwrapped-coordinate trajectories with three velocity seeds per structure, plus a follow-up 18-run 200--500 ps GPU production set.
- MD is interpreted only as a finite-window stability and displacement diagnostic.
- Nine high-displacement snapshots have completed spin-polarized DFT
  single-point sanity checks without fatal VASP markers: six Si4--graphene
  snapshots and three monovacancy snapshots.
- The local 5080 grouped-E0 snapshot-force diagnostic is incorporated as a
  mixed out-of-domain result: Si4--graphene improves, monovacancy remains poor.
- The main text no longer contains internal revision phrases such as `first draft`, `reviewer-response`, or `before journal submission`.

## Not Claimed Unless New VASP Results Finish

- Final CI-NEB migration barriers.
- DFT-confirmed high-displacement MD mechanisms beyond the current nine
  single-point sanity checks.
- Quantitative diffusion coefficients.
- Practical anode performance.

## Still Needed For A Stronger Kinetic Paper

- Relaxed CI-NEB barriers benchmarked against the graphene literature.
- DFT checks of representative production-trajectory high-displacement MD
  snapshots.
- Longer and larger-cell MD with concentration variation.
- Full relaxed adsorption-site searches and dispersion/dipole sensitivity
  checks if adsorption thermodynamics become a central claim.
- A public reproducibility archive for final journal submission.

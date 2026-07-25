# Review Feedback Coverage

This note maps the extracted reviewer feedback to the current conservative revision state.

## Covered In The Current Manuscript

- Fixed-geometry path spans are no longer called migration barriers.
- The manuscript no longer claims converged diffusion coefficients, practical anode performance, voltage, capacity, rate capability, cycling stability, mechanical advantage, or electronic advantage.
- `Si--graphene composite` language has been narrowed to a `Si4--graphene motif` wherever the model scope matters.
- The Introduction now states that a single-Li small-cell model cannot establish realistic storage performance, Li--Li clustering behavior, multilayer transport, electrolyte effects, or Si alloying.
- DFT details now include spin polarization, ENCUT, k-point mesh, smearing, convergence criteria, LASPH, ADDGRID, and ISYM.
- Missing vdW and dipole corrections are explicitly identified as limitations.
- MACE validation now includes held-out test metrics, an unfine-tuned foundation baseline, family-level errors, and three-seed committee diagnostics.
- Wrapped-coordinate MD has been replaced by 100 ps unwrapped-coordinate trajectories with three velocity seeds per structure.
- MD is interpreted only as a short-window stability and displacement diagnostic.
- Eight high-displacement snapshots have completed spin-polarized DFT
  single-point sanity checks without fatal VASP markers: five Si4--graphene
  snapshots and three monovacancy snapshots.
- The main text no longer contains internal revision phrases such as `first draft`, `reviewer-response`, or `before journal submission`.

## Not Claimed Unless New VASP Results Finish

- Final CI-NEB migration barriers.
- DFT-confirmed high-displacement MD mechanisms beyond the current eight
  single-point sanity checks.
- Quantitative diffusion coefficients.
- Practical anode performance.

## Still Needed For A Stronger Kinetic Paper

- Relaxed CI-NEB barriers benchmarked against the graphene literature.
- DFT checks of representative high-displacement MD snapshots.
- Longer and larger-cell MD with concentration variation.
- Dispersion and slab-dipole sensitivity checks for key labels.
- A public reproducibility archive for final journal submission.

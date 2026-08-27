# Science Strengthening Audit (2026-08-25)

This audit distinguishes reviewer compliance from additional scientific
strengthening. Publication cannot be guaranteed; the completion criterion is
that every reviewer request is answered with traceable manuscript evidence and
that newly added calculations are used only after convergence and validation.

## Editor Requirements

| Requirement | Current state | Final gate |
|---|---|---|
| Point-by-point response | Present for Reviewer 2 comments 1-8 and Reviewer 3 comments 1-4 | Refresh page/line references after final compile |
| Manuscript and figure source | Present in the resubmission package | Rebuild source ZIP after new evidence |
| Highlights | Present | Recheck 85-character limit after conclusion changes |
| Graphical abstract | Present | Regenerate only if the central figure changes materially |

## Reviewer 2

| Comment | Current evidence | Strengthening action |
|---|---|---|
| 1. Compare with DeePMD-kit/DP-GEN | Introduction and SI comparison table explicitly distinguish the open validation gate from a closed retraining loop | Retain; no new calculation required |
| 2. Narrow novelty | Title omits `validation-first`; Introduction defines diagnostic-to-claim mapping | Retain and tie the contribution to measured environment-resolved errors |
| 3. Clarify committee role | Methods state qualitative seed sensitivity only and no deviation threshold | Retain; do not relabel committee spread as calibrated uncertainty |
| 4. Five-frame grouped split is too small | Manuscript calls it a leakage audit, not a population benchmark | Add a model-independent, balanced DFT force benchmark with five new perturbations per family (25 total); report only converged rows |
| 5. Path spans are not barriers | Main text and SI use fixed-path descriptors; curated CSV uses non-barrier columns | Re-run terminology search across final manuscript, SI, response, captions, and upload data |
| 6. Completed MD is not physical validation | Methods state this explicitly | Retain and keep trajectories out of diffusion claims |
| 7. Emphasize direct DFT validation | Direct high-displacement force comparison is central | Add the balanced five-family benchmark beside the existing monovacancy/Si4 challenge set |
| 8. State whether snapshots were retrained | Methods and Results state that no closed retraining cycle was completed | Retain; a new retraining cycle is not reviewer-mandated and would require a separate independent test set |

## Reviewer 3

| Comment | Current evidence | Remaining action |
|---|---|---|
| 1. Abstract should be a scientific summary | Physical adsorption trend now leads the Abstract | Remove the remaining 285.2-to-20.1 pre-audit metric from the Abstract; replace it with validated balanced-test findings after calculations finish |
| 2. Figure quality and labels | Main figures are high-resolution/vector; SI path and MSD panels have explicit labels and distinct styles | Rebuild the scientific summary as a legible vector figure including the balanced benchmark; inspect manuscript and SI PDFs at print scale |
| 3. Academic language | Internal status/debug phrasing was removed | Perform a final prose pass after numerical revisions and check response claims against the actual Abstract |
| 4. Potential-development methods | Dedicated subsection records architecture, training, E0 solve, dataset scope, and grouped split | Add the prespecified perturbation-benchmark protocol and its no-model-selection rule |

## Additional Scientific Risk Reduction

### Final-iteration SCF audit

The earlier collectors treated the presence of VASP's generic EDIFF message as
sufficient evidence of electronic convergence. A direct OSZICAR audit showed
that this message is also printed when the final Davidson iteration reaches
\texttt{NELM}; final-iteration counting is therefore now mandatory. The 273
training labels pass the corrected gate (194/194 relaxation frames and 79/79
fixed-geometry single points). The 25 family-balanced force configurations also
pass 25/25.

The earlier five D3 anchors and the first 15-site D3 array do not pass the
corrected gate and are excluded from the final evidence path. CPU-only two-stage
recalculations of 15 selected sites and five substrate references are running as
Slurm job 3192389. Four of the nine high-displacement snapshots, including all
three monovacancy frames, also required stable-SCF reruns; these are running as
CPU-only Slurm job 3192408. No old force-error or adsorption-energy number may
be retained until the replacement outputs pass \texttt{last\_iter < NELM} and
the model evaluations are regenerated.

The current adsorption comparison uses one PBE-relaxed geometry per family with
a PBE-D3(BJ)+dipole single point. To test whether the family trend is tied to one
Li placement, the three lowest-energy placements from each preceding PBE
fixed-site scan are being recomputed with PBE-D3(BJ)+dipole (15 CPU single
points). These calculations remain fixed-geometry site checks and will not be
described as relaxed adsorption thermodynamics.

No additional CI-NEB calculation is planned. Reviewer 2 explicitly accepted the
non-barrier interpretation, and the existing NEB attempts are not ionically
converged. Promoting them would weaken rather than strengthen the evidence.

## Journal-Scope And FAIR Gate

The current Computational Materials Science scope explicitly requires
validation and transferability analysis for non-first-principles models and
FAIR-compatible data and code for data-driven studies. The strengthened package
therefore adds both the balanced direct-DFT force test and redistributable
author-trained checkpoints. The MACE-MPA-0 foundation artifact is fixed by its
official MIT-licensed release URL, byte size, and SHA256; it is not duplicated.

Final release gates:

- 25/25 balanced DFT rows electronically converged, force-readable, and hashed;
- 15/15 multi-site D3 rows electronically converged with hashed adsorbate,
  substrate, and isolated-Li reference outputs;
- 50 frame/model force-error rows generated by CPU-only inference;
- five author-trained checkpoint hashes verified in the archive;
- manuscript, SI, response, figure, and data tables regenerated from the same
  curated CSV files.

## Runtime And Hardware Constraints

- Cluster calculations are CPU-only VASP jobs.
- No cluster GPU job may be submitted.
- Balanced-force jobs have a 12-hour per-task hard limit.
- D3 site jobs have a 12-hour per-task hard limit.
- Any future training or GPU-scale MACE work must be packaged for manual RTX
  5080 execution and designed to complete within 24 hours.

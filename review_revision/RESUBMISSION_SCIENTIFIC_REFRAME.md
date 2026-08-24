# Scientific Reframe for Resubmission

## Current decision state

- Manuscript: COMMAT-D-26-03061
- Decision: Reject in Current Form / Resubmit
- Resubmission deadline: 2026-10-13
- Available decision files: editor letter and the five-page review PDF recovered
  from `COMMAT-D-26-03061-reviews-2.zip`
- Reviewers in the platform export: Reviewer 2 (eight comments) and Reviewer 3
  (four comments)

The point-by-point response is now drafted against the verbatim comments in
`manuscript/response_to_reviewers.tex` and compiled as
`manuscript/response_to_reviewers.pdf`.

## What the reviews actually say

Reviewer 2 regards the study as potentially publishable after minor revision
and considers the direct DFT checks, leakage audit, and conservative kinetic
boundaries strengths. This review does not request new calculations. Its central
request is accurate positioning: the workflow shares explore-label logic with
DeePMD-kit/DP-GEN and committee active learning, but it neither uses a numerical
model-deviation threshold nor closes a retraining loop. The novelty must
therefore be a diagnostic-to-claim mapping and the environment-resolved result,
not the general idea of ML exploration followed by DFT.

Reviewer 3 identifies the presentation problem that drove the editorial
decision. The abstract reads like an audit log, the academic tone resembles
internal notes, the figures are hard to navigate, and the potential-development
methods are incomplete. This review asks for a conventional scientific abstract,
publication-quality figures, professional scientific English, and a dedicated
methods description covering architecture, training, E0 estimation, dataset
scope, and group-aware splitting.

The combined diagnosis is therefore not that the computational evidence is
invalid. The core problem is manuscript architecture: process failures,
excluded claims, and debugging history displaced the positive scientific
result. The resubmission must lead with defect-dependent Li adsorption and the
chemically specific contrast between Si4 and reconstructed-monovacancy force
transfer, while moving audit evidence to Methods and Supporting Information.

## Diagnosis of the submitted manuscript

The submitted version is organized as an audit report rather than a scientific
argument. Its title, abstract, Results section, tables, and conclusion repeatedly
foreground leakage, calibration, runtime completion, failed validation gates,
and excluded claims. The physical question and positive result are therefore
secondary to the history of how the workflow was debugged.

Specific structural problems are:

1. The abstract opens with validation requirements instead of a materials
   question or finding.
2. Results begin with data-split and calibration failures rather than Li-defect
   energetics.
3. Fixed path scans and finite-window MD receive extensive main-text space even
   though they do not support migration barriers or diffusion coefficients.
4. Per-run completion, hashes, seed identifiers, and validation gates dominate
   the main narrative despite being reproducibility or Supporting Information
   content.
5. Limitations are repeated throughout the paper instead of being stated once,
   precisely, after the supported findings.

## Revised scientific question

**How do distinct graphene defect and Si-containing local environments change
dilute Li adsorption, and how does that chemical diversity affect the
transferability of a fine-tuned foundation MLIP?**

This framing makes the work a defect-dependent MLIP transferability study. It is
not a Li diffusion paper, a battery-performance paper, or a presentation of a
new MLIP architecture.

## Evidence-supported findings

### 1. Local environments produce a broad adsorption-energy range

PBE-D3(BJ) fixed-geometry single points with a slab dipole correction give:

| Local environment | E_ads (eV/Li) | Change relative to pristine (eV) |
| --- | ---: | ---: |
| Pristine graphene | -0.634 | 0.000 |
| Monovacancy graphene | -3.115 | -2.481 |
| Divacancy graphene | -1.328 | -0.694 |
| Stone-Wales graphene | +0.009 | +0.643 |
| Si4-graphene motif | -3.349 | -2.715 |

Supported interpretation: the sampled monovacancy and Si4 local geometries bind
Li much more strongly than the sampled pristine geometry, whereas the sampled
Stone-Wales geometry does not show favorable adsorption relative to an isolated
Li atom.

Boundary: these are fixed-geometry single-point anchors, not an exhaustive
relaxed adsorption-site search or a statement about voltage, capacity,
clustering, or complete anode performance.

### 2. Same-workflow accuracy does not predict finite-temperature transfer

On the original correlated test split, fine-tuning reduces the all-family force
RMSE from 285.2 to 20.1 meV/A. This establishes that target-domain fine-tuning
improves interpolation within the sampled workflow, but the correlated split
cannot be presented as independent generalization.

The corrected grouped split gives only one held-out configuration per family.
Its family errors are useful sanity checks, not population-level transferability
statistics. The split construction and E0 correction belong in Methods and
Supporting Information, not in the paper's central result.

### 3. Transferability failure is local-environment dependent

Nine high-displacement DFT snapshots provide a direct out-of-domain force test:

| Snapshot group | Foundation RMSE (meV/A) | Grouped-E0 RMSE (meV/A) | Change |
| --- | ---: | ---: | ---: |
| All snapshots | 710 | 646 | -9% |
| Monovacancy | 1149 | 1107 | -4% |
| Si4-graphene | 310 | 114 | -63% |

Supported interpretation: corrected fine-tuning substantially improves the
Si-containing high-displacement regime but does not repair the reconstructed
monovacancy regime. Aggregate test errors therefore conceal a chemically
specific extrapolation failure. The short 1.20-1.22 A C-C contacts in the
monovacancy snapshots reinforce that this regime requires targeted DFT labels
before physical trajectories are interpreted.

This is the strongest MLIP result and should be the paper's central figure and
discussion.

## Proposed title and claim hierarchy

Preferred title:

> Local-environment-dependent transferability of a fine-tuned MACE potential
> for lithium adsorption on graphene defects

Alternative title if the Si4 motif remains prominent:

> Defect chemistry governs lithium adsorption and MLIP transferability in
> graphene-based local environments

Primary claim:

> Distinct defect environments change both dilute Li adsorption and the
> extrapolative reliability of a fine-tuned foundation MLIP; direct DFT force
> tests reveal strong improvement for the Si4 regime but persistent failure for
> reconstructed monovacancy configurations.

Secondary claim:

> Low same-workflow errors are insufficient to establish finite-temperature
> transferability across chemically and topologically distinct defect families.

## New manuscript order

1. Introduction: defect-dependent Li chemistry and the need for
   local-environment-resolved MLIP validation.
2. Methods: model systems, consistent DFT settings, MACE training, grouped
   evaluation, and targeted DFT snapshot selection.
3. Results 1: defect-dependent adsorption-energy anchors.
4. Results 2: interpolation improvement from fine-tuning.
5. Results 3: local-environment-dependent extrapolation revealed by snapshot
   DFT force errors.
6. Discussion: why Si4 improves while monovacancy remains outside the learned
   domain; implications for active-learning data selection.
7. Limitations: one concise subsection covering fixed geometries, small held-out
   groups, local Si4 model scope, and lack of kinetic claims.
8. Conclusion: answer the scientific question directly.

## Main text versus Supporting Information

Retain in the main text:

- structure-family overview;
- adsorption-energy comparison;
- concise foundation versus fine-tuned interpolation comparison;
- environment-resolved snapshot force-error comparison;
- representative strained monovacancy and Si4 configurations;
- one limitations paragraph.

Move to Supporting Information:

- dataset-family counts and full split audit;
- E0 fitting details and checkpoint names;
- seed-by-seed committee logs;
- complete site-ranking tables;
- fixed interpolation path scans;
- all finite-window MSD traces and runtime-completion tables;
- snapshot hashes, individual energies, and convergence markers;
- validation-gate table and reproducibility implementation details.

Remove from the scientific narrative:

- repeated statements that fixed paths are not NEB barriers;
- repeated statements that short MD is not a diffusion coefficient;
- job-completion language such as no NaN, no lost atoms, or 18/18 completed;
- operational next-step lists framed as manuscript conclusions.

One precise limitations section is sufficient.

## Resubmission deliverables

1. Clean revised manuscript source and PDF.
2. Marked manuscript with line numbers and visible changes.
3. Point-by-point Response to Reviewers covering all 8+4 numbered comments.
4. Revised Highlights with 3-5 findings, each at most 85 characters.
5. Revised graphical abstract centered on adsorption and transferability.
6. Updated source and reproducibility archives with matching version hashes.

No GPU work is authorized on the cluster. If a reviewer requires additional GPU
calculations, the runnable task will be packaged for the local RTX 5080 and
bounded to complete within 24 hours.

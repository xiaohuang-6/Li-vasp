# Original Comments Coverage Audit

Scope: the editor decision letter, Reviewer 2 comments 1--8, and Reviewer 3
comments 1--4 supplied by the author. Evidence refers to the recompiled
13-page manuscript and 7-page Supporting Information dated 1 September 2026.

## Editor requirements

| Requirement | Status | Current material |
|---|---|---|
| Point-by-point response in the peer-review platform | Addressed | `manuscript/response_to_reviewers_copy_paste.txt` contains an editor response plus 8 Reviewer 2 and 4 Reviewer 3 paste-ready blocks, each with paragraph, page, and line references. |
| Editable manuscript and figure source | Addressed | `04_Manuscript_Source.zip` is generated from the TeX, bibliography, compile script, figure generators, figure assets, structures, and curated inputs. |
| Highlights | Addressed | Five bullets; each is within the 85-character limit. |
| Graphical Abstract | Addressed | 3600 x 1440 pixels at 300 dpi; the annotation collision is removed and the force summary reports 450.0 to 267.5 meV A^-1. |
| Supporting material and data/code | Addressed | SI PDF/source and the version-pinned reproducibility archive are separate package items. |

## Reviewer 2

| Comment | Status | Evidence in the revision |
|---|---|---|
| 1. Compare with concurrent/active learning | Fully addressed | Introduction paragraph 3, p. 2, lines 46--53 cites DeePMD-kit and DP-GEN and distinguishes thresholded, closed-loop retraining from the present use of direct DFT. SI Table 2 gives the requested comparison table. |
| 2. State novelty precisely | Fully addressed | `validation-first` is removed from the title. Abstract and Introduction paragraphs 3--5, pp. 1--3, lines 1--68 frame the contribution as defect-dependent adsorption and local MLIP reliability supported by direct DFT, not a new active-learning architecture. |
| 3. Clarify the MACE committee | Fully addressed | Methods paragraph 4, p. 6, lines 164--172 states that the committee is a qualitative seed-sensitivity diagnostic and that no disagreement or force-deviation threshold selected DFT configurations. |
| 4. Keep grouped-split limitation prominent | Fully addressed | Methods paragraph 1, p. 5, lines 132--142 and Results Section 3.2, p. 9, lines 236--249 limit the grouped split to correlation sensitivity. A separate 25-configuration, five-family DFT benchmark is reported in Figure 2 and Section 3.3 without a global-transferability claim. |
| 5. Do not call path spans barriers | Fully addressed | Methods, pp. 4--5, lines 114--129 and Scope and limitations, p. 11, lines 305--310 explicitly identify non-NEB fixed-geometry descriptors. SI Figure 3/Table 5 and `fixed_path_descriptors.csv` use span/endpoint terminology. |
| 6. Treat MD completion conservatively | Fully addressed | Methods, pp. 6--7, lines 185--205 states that trajectories generate displaced configurations and that reliability is assessed by direct DFT forces rather than trajectory stability. No diffusion coefficient is reported. |
| 7. Emphasize direct DFT validation | Fully addressed | Abstract, Figure 2, Sections 3.3--3.4 (pp. 9--10, lines 250--299), and Conclusion (p. 11, lines 311--327) center the direct DFT force comparison. The interpretation is tied to measured errors and reconstructed C--C contacts, not displacement magnitude alone. |
| 8. State whether snapshots were retrained | Fully addressed | Methods p. 7, lines 200--205 and Results p. 10, lines 291--299 state that the DFT-validated snapshots were not incorporated into another training cycle and that a closed loop is outside scope. |

## Reviewer 3

| Comment | Status | Evidence in the revision |
|---|---|---|
| 1. Rewrite the Abstract | Fully addressed | The one-paragraph Abstract, p. 1, lines 9--27 follows problem, approach, validated results, and implication. It reports adsorption trends and environment-resolved force results without the prior audit-log structure. |
| 2. Improve figures and labeling | Fully addressed | Main Figures 1--2 are a high-resolution structure figure and a four-panel vector scientific summary. SI Figure 3 has panels (a)--(j). SI Figure 4 has panels (a)/(b), a colorblind-friendly palette, distinct line styles/markers, a vector PDF, and a 3150 x 1260, 300 dpi PNG. |
| 3. Improve academic language | Fully addressed | Title, Abstract, Introduction, Results, and Conclusion were rewritten as a continuous scientific argument. Searches of the active manuscript and SI return no `validation-first`, `same-workflow`, `prespecified`, internal status/log phrasing, or First/Second/Third/Finally construction. |
| 4. Complete MLIP methodology | Fully addressed | DFT labeling, pp. 4--5, lines 121--131 and MACE potential development and validation, pp. 5--6, lines 132--184 provide dataset scope, split algorithm, architecture, training parameters, checkpoint criteria, and full-rank E0 solve. SI Tables 1--2 provide detailed metrics and comparison context. |

## Boundary

No reviewer requested additional NEB calculations, diffusion coefficients, or a
closed retraining cycle. The revision therefore does not add such claims. No
GPU or cluster task was submitted during this audit.


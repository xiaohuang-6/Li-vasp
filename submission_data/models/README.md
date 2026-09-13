# Redistributed MACE Checkpoints

This directory contains the five author-trained checkpoints used by the
manuscript, including the results transferred from the R1 Supporting Information.
The files are redistributed as curated
research artifacts under CC BY 4.0. They are PyTorch/MACE model files and should
be loaded only in a trusted environment.

| File | Role | Bytes | SHA256 |
|---|---|---:|---|
| `li_mace_v1_3060ti.model` | Same-workflow baseline and reference trajectories | 6626839 | `2b5227ce65cc392bcba62cbdafd345a1be1fd31ebb0ca295e364f53d54b919d1` |
| `li_mace_review_seed20260427.model` | Committee seed 20260427 | 6632938 | `0811bed40f55755393b86c53edc0ec500cb8ad76d46b8393aad214f4a800d0b3` |
| `li_mace_review_seed20260428.model` | Committee seed 20260428 | 6632938 | `43102d78a25b8e8904db1cfda24a8e4105276980d65a4d1bcc9587de77f8d3e4` |
| `li_mace_review_seed20260429.model` | Committee seed 20260429 | 6632938 | `ae4fdce775236e5f9689387257402136877c7543e3cd1b71efd13750e6e9f7c1` |
| `li_mace_grouped_e0_seed20260430.model` | Grouped-E0 force-validation checkpoint | 12991294 | `2abd951d5c8dcf13925eb6e5d0974e4790373d288b35d711d24787cd0e629dcf` |

The MACE-MPA-0 foundation checkpoint is not duplicated here. The exact file is
`mace-mpa-0-medium.model`, 79,462,305 bytes, with SHA256
`75428afe3a1d7d8062e19bcaabd5c433623cabf308242ec9fb493e38604fb638`.
MACE distributes this model under the MIT license at:

`https://github.com/ACEsuit/mace-mp/releases/download/mace_mpa_0/mace-mpa-0-medium.model`

The manuscript uses MACE 0.3.15 for the reference checkpoint and MACE 0.3.16
for the committee and grouped-E0 checkpoints. Exact datasets and accepted
training settings are provided in the adjacent dataset and log directories.
For CPU-only inference on systems without an NVIDIA driver, use
`review_revision/evaluate_balanced_perturbation_forces.py`; its loader maps
the e3nn TorchScript submodules embedded by the RTX 5080 training environment
explicitly to CPU before constructing the MACE calculator.

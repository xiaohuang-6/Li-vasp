# Current Gate Status For 5080 Runs

Last cluster-side check: 2026-07-24 20:56 EDT.

## DFT Gates

- CI-NEB: 0 formally converged paths.
- CI-NEB paths with all intermediate image energies: 6/10.
- CI-NEB fatal markers: 1/10. The fatal case is
  `B2_Divacancy_path01_prior_li_xy_to_bridge_C_C`, which developed force
  blow-up and `SETYLM_AUG` internal VASP errors. Do not use that path as a
  migration barrier.
- `B2_Divacancy_path02_top_central_C_to_hollow_C3` has no formal fatal marker
  but has a huge force diagnostic (`g(F) = 7.26e5`) and is also excluded from
  barrier interpretation.
- MD snapshot DFT: 8 usable converged single-point energies out of 9 prepared
  checks.
- Usable snapshots:
  - `D_SiGraphene_seed20260427_step099800`: time 99.8 ps, MSDxy 2683.4 A^2,
    usable DFT energy -1899.23167491 eV, no fatal VASP marker.
  - `D_SiGraphene_seed20260427_step100000`: time 100.0 ps, MSDxy 2661.0 A^2,
    usable DFT energy -1902.31385426 eV, no fatal VASP marker.
  - `B1_Monovacancy_seed20260429_step058100`: time 58.1 ps, MSDxy 383.9 A^2,
    usable DFT energy -1407.42570590 eV, no fatal VASP marker. Geometry screen
    found no sub-A overlaps, but a short C-C contact around 1.20 A, so treat
    this as a strained high-displacement configuration.
  - `B1_Monovacancy_seed20260429_step058200`: time 58.2 ps, MSDxy 382.4 A^2,
    usable DFT energy -1407.643487 eV, no fatal VASP marker. Geometry screen
    found no sub-A overlaps, but a short C-C contact around 1.21 A.
  - `B1_Monovacancy_seed20260429_step100000`: time 100.0 ps, MSDxy 217.7 A^2,
    usable DFT energy -1406.796775 eV, no fatal VASP marker. Geometry screen
    found no sub-A overlaps, but a short C-C contact around 1.22 A.
  - `D_SiGraphene_seed20260429_step030900`: time 30.9 ps, MSDxy 356.8 A^2,
    usable DFT energy -1897.170310 eV, no fatal VASP marker.
  - `D_SiGraphene_seed20260429_step031000`: time 31.0 ps, MSDxy 350.7 A^2,
    usable DFT energy -1899.553470 eV, no fatal VASP marker. Geometry screen
    found no sub-A overlaps, but a short Si-Si contact around 1.99 A.
  - `D_SiGraphene_seed20260429_step100000`: time 100.0 ps, MSDxy 207.6 A^2,
    usable DFT energy -1902.947883 eV, no fatal VASP marker.

## Consequence For Local 5080 Agent

You may run the selected longer MD and committee-MD scripts as optional
robustness evidence:

```bash
bash scripts/run_05_extended_md_selected.sh
bash scripts/run_06_committee_md_selected.sh
```

Do not claim final diffusion coefficients or migration barriers from these GPU
runs. The NEB barrier gate is still not satisfied, and the eight DFT snapshot
checks are only sanity checks of selected configurations, not proof of a
diffusion mechanism.

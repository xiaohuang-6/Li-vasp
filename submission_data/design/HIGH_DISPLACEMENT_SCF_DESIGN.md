# High-displacement DFT strict-SCF design

The geometries and model-blind selection of the nine preselected snapshots are unchanged. Four frames use a CPU-only two-stage ALGO=All protocol: a 1e-4 eV preconditioning stage followed by a restart at 1e-6 eV. Five frames retain their original strict-SCF outputs. The final nine-row manifest is accepted only when every output has normal termination, no fatal marker, finite energy and forces, and last_iter < NELM. Only this strictly converged set is used for force-error evaluation.

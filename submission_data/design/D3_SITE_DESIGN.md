# Converged D3 Site Robustness Design

The 15 site geometries are exactly the frozen, model-blind selection in the preceding three-sites-per-family manifest. Five matching Li-removed substrates are recomputed. Each CPU-only calculation first preconverges PBE-D3(BJ) without the dipole correction, then restarts from WAVECAR and CHGCAR with the z-directed slab dipole correction and ALGO=All. A final result is accepted only when the last electronic iteration is strictly below NELM and all energies and forces are finite. The isolated-Li reference is the existing 33-iteration converged result.

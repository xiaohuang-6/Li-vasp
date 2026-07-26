# Four-Day Execution Status

Last checked: 2026-07-26 03:41 EDT

Production-snapshot evidence refreshed: 2026-07-26 14:09 EDT

## CPU Jobs

Current status from `review_revision/check_reviewer_jobs.sh` after the unified
24h reviewer-follow-up audit:

- Cluster GPU guard:
  - No matching cluster GPU jobs are present.
  - Do not submit reviewer follow-up GPU work on the cluster. The grouped-E0
    fine-tune and snapshot force-evaluation jobs were completed from
    `local_5080_referee_followup_pack_20260725_1825.tar.gz` on the local RTX
    5080 workstation.
- Adsorption-energy single points:
  - Slurm array `3129645` (`li-ads-sp`) completed its current reviewer
    follow-up role; no `li-ads-sp` task remains in the current `squeue`
    snapshot.
  - Current collected status: 11/11 single-point components completed with
    usable converged energies, 0/11 fatal markers, and 5/5 complete
    family-level adsorption energies. These can be used only as
    single-geometry PBE-D3/dipole adsorption anchors.
- Fast 3-image Gamma-only CI-NEB fallback:
  - Slurm array `3129657` (`li-fast-neb`) is active on `et2024` with a 24h
    limit.
  - Current `squeue` shows `3129657_2` and `3129657_4` running.
  - Current collected status: 5/5 paths have all available image energies,
    0/5 paths formally converged, and 0/5 have fatal markers. Barrier values
    remain blank until the formal convergence gate is met.
- Production-trajectory high-displacement MD snapshot DFT checks:
  - Slurm array `3129676` (`li-md-dftcheck`) completed all seven CPU tasks with
    exit code 0; each task finished within the 24h limit.
  - Current collected status: 7/7 completed with electronically converged,
    usable energies and ASE-readable forces.
  - The accepted set contains five snapshots from two reference-model
    trajectories and two snapshots from one committee-model trajectory. It spans
    57.0--500.0 ps, `MSDxy = 489.5--2687.8 A^2`, and DFT energies from
    -1903.961 to -1899.193 eV.

- CI-NEB:
  - 10/10 paths have all intermediate image energies.
  - 0/10 paths formally converged.
  - 1/10 paths have fatal markers.
  - The newly started Stone-Wales and Si-graphene paths are still in early
    electronic/ionic progress; their transient barrier values are not
    manuscript-ready.
- MD snapshot DFT:
  - 9/9 completed.
  - 9/9 have usable electronically converged energies.
  - 0/9 have fatal markers.
  - 9/9 have at least one parsed SCF energy.

Decision: do not modify manuscript with NEB barriers yet. The B2 divacancy
path01 NEB has force blow-up and `SETYLM_AUG` internal VASP errors, so it is
excluded from interpretation. The B2 divacancy path02 NEB has no formal fatal
marker but has a huge last BRION force diagnostic (`g(F) = 7.26e5`) and is also
excluded from barrier interpretation. The manuscript and response now include
only converged DFT snapshot evidence: nine initial-campaign rows used for direct
MACE--DFT force comparisons and seven extended-trajectory rows spanning three
trajectory/model contexts. These 16 checks remain out-of-domain stress tests,
not diffusion-mechanism proof. The fast NEB fallback has not produced
manuscript-usable barrier values. The adsorption-energy gate is now passed for
single-geometry PBE-D3/dipole anchors.

## Running/Pending Slurm Jobs

- `3115996_5`: canceled at 22:00 EDT. This was
  `B2_Divacancy_path02_top_central_C_to_hollow_C3`; image 03 had an
  `EDDDAV/ZHEGV` fatal marker, the path had unphysical force diagnostics, and
  the job had stopped writing useful output while occupying 60 CPU cores.
- `3115996_6`: canceled on 2026-07-25 after the active reviewer follow-up was
  restored to 24h-or-shorter tasks only.
- `3115996_7`: canceled on 2026-07-25 after the active reviewer follow-up was
  restored to 24h-or-shorter tasks only.
- `3115996_8`: canceled on 2026-07-25 after the active reviewer follow-up was
  restored to 24h-or-shorter tasks only.
- `3115996_9`: canceled on 2026-07-25 after the active reviewer follow-up was
  restored to 24h-or-shorter tasks only.
- Slurm array `3129676` completed all seven production-snapshot tasks; no
  resubmission is needed.
- No 48h `li-review-neb60` full-node NEB jobs remain active in `squeue`.

Do not resubmit the completed production-snapshot DFT array. Do not submit any
cluster GPU jobs.

Diagnostic note: `3115996_4` was the fatal
`B2_Divacancy_path01_prior_li_xy_to_bridge_C_C` NEB path and is no longer
running. `3115996_5` was the unphysical
`B2_Divacancy_path02_top_central_C_to_hollow_C3` path and has also been
canceled. The remaining optional full-node NEB tasks `3115996_6` through
`3115996_9` were canceled later because they had 48h limits and no longer fit
the active 24h-only follow-up policy.

Additional production-snapshot check at 14:09 EDT on 2026-07-26: `sacct`
records all seven `3129676` tasks as `COMPLETED` with exit code 0. The longest
elapsed time was 12:00:50, within the 24h operating constraint.

## 5080 Package

Prepared package:

- `local_5080_four_day_sci_pack_20260724.tar.gz`
- Size: 71 MB.
- Includes `FOUR_DAY_5080_AGENT_PROMPT.md`,
  `FOUR_DAY_5080_CURRENT_GATE_STATUS.md`,
  `scripts/run_05_extended_md_selected.sh`, and
  `scripts/run_06_committee_md_selected.sh`.

Download/prompt summary:

- `LOCAL_5080_DOWNLOAD_AND_AGENT_PROMPT.md`

Decision: the old four-day 5080 package remains a historical robustness
package. The active reviewer follow-up GPU path was the smaller
`local_5080_referee_followup_pack_20260725_1825.tar.gz`, which contains the
grouped-split E0 fine-tune and nine-snapshot force-evaluation diagnostics. Its
returned result package has been accepted:

- Return archive:
  `incoming_gpu_results/local_5080_referee_followup_results_20260725_2309.tar.gz`
- SHA256:
  `35ac20123795f978c64ee7a5266eba1e96c40a9ca954da99be742e0039edb0d2`
- Clean local result directory:
  `results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/`
- Accepted scope: local RTX 5080 training completed, a MACE model and LAMMPS
  TorchScript model were produced, and 9 high-displacement snapshots were
  evaluated against 3 models.
- Scientific boundary: `grouped_e0` improves D Si4-graphene force RMSE to
  113.6 meV/A over six snapshots, but B1 monovacancy remains poor at
  1107.0 meV/A over three snapshots. Use this only as an out-of-domain
  diagnostic; it cannot replace adsorption energies, converged NEB barriers,
  or production snapshot DFT checks.

## Next Check

Run:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

If any CI-NEB path reports `converged = True`, collect final NEB results and
update the manuscript only if the path is physically well behaved and has no
fatal marker or force blow-up. The current nine usable MD snapshot DFT checks
are already included only as conservative snapshot sanity checks. Do not make
stronger mechanism or diffusion claims from these snapshots.

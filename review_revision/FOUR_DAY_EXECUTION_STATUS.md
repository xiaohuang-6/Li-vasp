# Four-Day Execution Status

Last checked: 2026-07-26 03:41 EDT

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
  - Slurm array `3129676` (`li-md-dftcheck`) is active on `et2024` with a 24h
    limit.
  - Array tasks `3129676_2`--`3129676_5` are running and task 6 is pending
    behind the `%4` array limit. Tasks 0--1 have completed.
  - Current collected status: 2/7 completed with usable converged energies and
    0/7 fatal markers; three additional rows have partial SCF energies.
  - The two usable production snapshots are
    `D_SiGraphene_seed20260427_step057000` (`MSDxy = 2687.8 A^2`,
    `E_DFT = -1899.724675 eV`) and
    `D_SiGraphene_seed20260427_step500000` (`MSDxy = 2436.1 A^2`,
    `E_DFT = -1903.110484 eV`). Both come from the same trajectory, so they do
    not support production-trajectory validation or mechanism claims.

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
only a narrow DFT snapshot sanity-check statement/table for nine electronically
converged initial-campaign snapshots. These remain DFT input/electronic
convergence sanity checks, not diffusion-mechanism proof. The production-set
snapshot checks have produced one usable single-row sanity check, but not a
production-set validation. The fast NEB fallback has not produced
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
- The active 24h CPU follow-up arrays visible in `squeue` are `3129657`
  (`li-fast-neb`) and `3129676` (`li-md-dftcheck`). At the 01:28 EDT snapshot,
  the visible running tasks were `3129657_2`, `3129676_1`--`3129676_4`;
  `3129676_[5-6%4]` remained pending behind the array limit.
- No 48h `li-review-neb60` full-node NEB jobs remain active in `squeue`.

Do not resubmit or cancel the currently running fast NEB or production snapshot
DFT CPU jobs unless they develop fatal markers, stop writing output for hours,
or exceed the queue strategy needed for the 24h reviewer-follow-up plan. Do not
submit any cluster GPU jobs.

Diagnostic note: `3115996_4` was the fatal
`B2_Divacancy_path01_prior_li_xy_to_bridge_C_C` NEB path and is no longer
running. `3115996_5` was the unphysical
`B2_Divacancy_path02_top_central_C_to_hollow_C3` path and has also been
canceled. The remaining optional full-node NEB tasks `3115996_6` through
`3115996_9` were canceled later because they had 48h limits and no longer fit
the active 24h-only follow-up policy.

Additional check at 01:28 EDT on 2026-07-26: all current reviewer-follow-up CPU
work visible in `squeue` is either running or queued with 24h limits. Recent
`vasp.log`, `OUTCAR`, `OSZICAR`, or `stdout` timestamps show active output for
the running fast NEB and production snapshot directories. This
preserves useful queue progress without adding new GPU work on the cluster.

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

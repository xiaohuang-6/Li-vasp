# Four-Day Execution Status

Last checked: 2026-07-24 22:18 EDT

## CPU Jobs

Current status from `review_revision/check_reviewer_jobs.sh`:

- CI-NEB:
  - 10/10 paths have all intermediate image energies.
  - 0/10 paths formally converged.
  - 1/10 paths have fatal markers.
  - The newly started Stone-Wales and Si-graphene paths are still in early
    electronic/ionic progress; their transient barrier values are not
    manuscript-ready.
- MD snapshot DFT:
  - 8/9 completed.
  - 8/9 have usable electronically converged energies.
  - 0/9 have fatal markers.
  - 9/9 have at least one parsed SCF energy.
  - The missing snapshot has been restarted as a 64-rank full-node job.

Decision: do not modify manuscript with NEB barriers yet. The B2 divacancy
path01 NEB has force blow-up and `SETYLM_AUG` internal VASP errors, so it is
excluded from interpretation. The B2 divacancy path02 NEB has no formal fatal
marker but has a huge last BRION force diagnostic (`g(F) = 7.26e5`) and is also
excluded from barrier interpretation. The manuscript and response now include
only a narrow DFT snapshot sanity-check statement/table for eight
electronically converged snapshots. These remain DFT input/electronic
convergence sanity checks, not diffusion-mechanism proof.

## Running/Pending Slurm Jobs

- `3115996_5`: canceled at 22:00 EDT. This was
  `B2_Divacancy_path02_top_central_C_to_hollow_C3`; image 03 had an
  `EDDDAV/ZHEGV` fatal marker, the path had unphysical force diagnostics, and
  the job had stopped writing useful output while occupying 60 CPU cores.
- `3115996_6`: running full-node NEB for
  `C_StoneWales_path01_prior_li_xy_to_hollow_C3` on `et103`.
- `3115996_7`: running full-node NEB for
  `C_StoneWales_path02_top_central_C_to_top_offset_C` on `et104`.
- `3115996_8`: running full-node NEB for
  `D_SiGraphene_path01_prior_li_xy_to_bridge_C_C` on `et108`.
- `3115996_9`: running full-node NEB for
  `D_SiGraphene_path02_top_central_C_to_hollow_C3` on `et111`.
- `3126845_0`: running 64-rank MD snapshot DFT retry for
  `D_SiGraphene_seed20260427_step099700` on `et106`.
- The remaining incomplete snapshot,
  `D_SiGraphene_seed20260427_step099700`, previously timed out after 24 hours
  on 32 ranks at electronic step 143. It is now being retried on a 64-rank full
  node as optional strengthening evidence. The current conservative manuscript
  already has eight usable snapshot checks and does not depend on this retry.

Do not resubmit or cancel the currently running Stone-Wales, Si-graphene, or
snapshot DFT jobs unless they develop fatal markers, stop writing output for
hours, or exceed the queue strategy needed for the two-day plan.

Diagnostic note: `3115996_4` was the fatal
`B2_Divacancy_path01_prior_li_xy_to_bridge_C_C` NEB path and is no longer the
running array task. The current running task, `3115996_5`, is
`B2_Divacancy_path02_top_central_C_to_hollow_C3`; it has complete intermediate
image energies but no formal convergence and an unphysical force diagnostic.
It remains excluded from interpretation. Canceling it would free a full node
and allow `3115996_6` to start, but it has not been canceled because
cancellation needs a new explicit user decision.

Additional check at 22:18 EDT: all remaining NEB array tasks are running, and
the improved status script confirms active `OUTCAR`, `OSZICAR`, or `stdout`
updates in the newly started directories. This preserved useful queue progress
without deleting the failed B2 output.

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

Decision: the 5080 package is ready, but longer GPU MD should be interpreted as
optional robustness evidence. It cannot replace converged NEB barriers or a
systematic DFT snapshot validation set.

## Next Check

Run:

```bash
cd /home/xh121/Li-vasp
review_revision/check_reviewer_jobs.sh
```

If any CI-NEB path reports `converged = True`, collect final NEB results and
update the manuscript only if the path is physically well behaved and has no
fatal marker or force blow-up. The current eight usable MD snapshot DFT checks
are already included only as conservative snapshot sanity checks. Do not make
stronger mechanism or diffusion claims from these snapshots.

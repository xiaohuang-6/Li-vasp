# Four-Day Execution Status

Last checked: 2026-07-24 20:56 EDT

## CPU Jobs

Current status from `review_revision/check_reviewer_jobs.sh`:

- CI-NEB:
  - 6/10 paths have all intermediate image energies.
  - 0/10 paths formally converged.
  - 1/10 paths have fatal markers.
- MD snapshot DFT:
  - 8/9 completed.
  - 8/9 have usable electronically converged energies.
  - 0/9 have fatal markers.
  - 9/9 have at least one parsed SCF energy.

Decision: do not modify manuscript with NEB barriers yet. The B2 divacancy
path01 NEB has force blow-up and `SETYLM_AUG` internal VASP errors, so it is
excluded from interpretation. The B2 divacancy path02 NEB has no formal fatal
marker but has a huge last BRION force diagnostic (`g(F) = 7.26e5`) and is also
excluded from barrier interpretation. The manuscript and response now include
only a narrow DFT snapshot sanity-check statement/table for eight
electronically converged snapshots. These remain DFT input/electronic
convergence sanity checks, not diffusion-mechanism proof.

## Running/Pending Slurm Jobs

- `3115996_5`: full-node NEB job running for
  `B2_Divacancy_path02_top_central_C_to_hollow_C3`.
- `3115996_[6-9%1]`: full-node NEB jobs pending by array task limit.
- No MD snapshot DFT jobs are currently visible in `squeue`.
- The remaining incomplete snapshot,
  `D_SiGraphene_seed20260427_step099700`, previously timed out after 24 hours
  on 32 ranks at electronic step 143. It can be retried on a 64-rank full node
  as optional strengthening evidence, but the current conservative manuscript
  already has eight usable snapshot checks and does not depend on this retry.

Do not resubmit or cancel these without a new explicit decision.

Diagnostic note: `3115996_4` was the fatal
`B2_Divacancy_path01_prior_li_xy_to_bridge_C_C` NEB path and is no longer the
running array task. The current running task, `3115996_5`, is
`B2_Divacancy_path02_top_central_C_to_hollow_C3`; it has complete intermediate
image energies but no formal convergence and an unphysical force diagnostic.
It remains excluded from interpretation. Canceling it would free a full node
and allow `3115996_6` to start, but it has not been canceled because
cancellation needs a new explicit user decision.

Additional check at 20:56 EDT: `3115996_5` is still RUNNING with a 2-day time
limit, but the latest job-level `vasp.log` timestamp is 18:20 and the latest
image OUTCAR timestamp is 19:02. This reinforces the current decision not to
use this path scientifically unless it later finishes with physically
reasonable forces and no fatal markers.

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

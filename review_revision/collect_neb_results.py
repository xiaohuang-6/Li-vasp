#!/usr/bin/env python3
"""Collect VASP CI-NEB energies and convergence status.

The script is safe to run while jobs are still running. It writes partial tables
when only some images or jobs have energies, and final barrier estimates once
all images are present.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # noqa: BLE001
    plt = None


OUTCAR_ENERGY_RE = re.compile(r"energy\s+without entropy\s*=\s*([-+0-9.]+)")
OSZICAR_ENERGY_RE = re.compile(r"\bF=\s*([-+0-9.Ee]+)")
ION_STEP_RE = re.compile(r"^\s*(\d+)\s+F=\s*([-+0-9.Ee]+)", re.MULTILINE)
BRION_RE = re.compile(r"BRION:\s+g\(F\)=\s*([-+0-9.Ee]+)")
IMAGES_RE = re.compile(r"^\s*IMAGES\s*=\s*(\d+)", re.MULTILINE)
EDIFFG_RE = re.compile(r"^\s*EDIFFG\s*=\s*([-+0-9.Ee]+)", re.MULTILINE)
FATAL_RE = re.compile(
    r"ERROR|Error|VERY BAD NEWS|segmentation|SIGSEGV|KILLED|killed|ZBRENT|Sub-Space-Matrix is not hermitian"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-list", default="review_revision/neb_jobs/neb_job_list.txt")
    parser.add_argument("--paths-csv", default="results/two_day_rush/path_barriers.csv")
    parser.add_argument("--output-dir", default="results/review_revision/neb_analysis")
    parser.add_argument(
        "--endpoint-mode",
        choices=["path_csv", "image_outputs", "endpoint_sp"],
        default="path_csv",
        help="Where endpoint energies come from. Use endpoint_sp for fast NEB jobs with separate endpoint single points.",
    )
    parser.add_argument(
        "--endpoint-manifest",
        default="review_revision/neb_fast_endpoint_jobs/endpoint_manifest.csv",
        help="Endpoint SP manifest used when --endpoint-mode=endpoint_sp.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def read_job_dirs(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [Path(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def job_key(family: str, path_id: str, start: str, end: str) -> str:
    return f"{family}_{path_id}_{start}_to_{end}"


def parse_images_count(job_dir: Path) -> int:
    incar = job_dir / "INCAR"
    if incar.exists():
        match = IMAGES_RE.search(incar.read_text(errors="replace"))
        if match:
            return int(match.group(1))
    image_dirs = sorted(path for path in job_dir.iterdir() if path.is_dir() and path.name.isdigit())
    return max(len(image_dirs) - 2, 0)


def parse_ediffg_abs(job_dir: Path) -> float | None:
    incar = job_dir / "INCAR"
    if not incar.exists():
        return None
    match = EDIFFG_RE.search(incar.read_text(errors="replace"))
    if not match:
        return None
    return abs(float(match.group(1).replace("D", "E")))


def last_energy_from_outcar(path: Path) -> float | None:
    text = read_text(path)
    matches = OUTCAR_ENERGY_RE.findall(text)
    if matches:
        return float(matches[-1])
    return None


def last_energy_from_oszicar(path: Path) -> float | None:
    matches = OSZICAR_ENERGY_RE.findall(read_text(path))
    if matches:
        return float(matches[-1].replace("D", "E"))
    return None


def endpoint_energy_from_image_dir(job_dir: Path, image_index: int) -> tuple[float | None, str]:
    image_dir = job_dir / f"{image_index:02d}"
    outcar_energy = last_energy_from_outcar(image_dir / "OUTCAR")
    if outcar_energy is not None:
        return outcar_energy, "endpoint_OUTCAR"
    oszicar_energy = last_energy_from_oszicar(image_dir / "OSZICAR")
    if oszicar_energy is not None:
        return oszicar_energy, "endpoint_OSZICAR"
    return None, "missing_endpoint"


def completed_single_point_energy(job_dir: Path) -> tuple[float | None, str]:
    outcar = job_dir / "OUTCAR"
    oszicar = job_dir / "OSZICAR"
    log = job_dir / "vasp.log"
    outcar_text = read_text(outcar)
    log_text = read_text(log)
    completed = "General timing and accounting informations for this job" in outcar_text or "Voluntary context switches" in log_text
    electronic_converged = "aborting loop because EDIFF is reached" in outcar_text
    fatal = bool(FATAL_RE.search(outcar_text + "\n" + log_text))
    if not completed or not electronic_converged or fatal:
        reason = "endpoint_SP_incomplete"
        if fatal:
            reason = "endpoint_SP_fatal"
        elif not electronic_converged:
            reason = "endpoint_SP_not_electronic_converged"
        return None, reason
    energy = last_energy_from_outcar(outcar)
    if energy is not None:
        return energy, "endpoint_SP_OUTCAR_completed"
    energy = last_energy_from_oszicar(oszicar)
    if energy is not None:
        return energy, "endpoint_SP_OSZICAR_completed"
    return None, "endpoint_SP_missing_energy"


def build_endpoint_sp_lookup(endpoint_manifest: Path) -> dict[tuple[str, int], tuple[float | None, str]]:
    lookup: dict[tuple[str, int], tuple[float | None, str]] = {}
    if not endpoint_manifest.exists():
        return lookup
    for row in read_csv(endpoint_manifest):
        job_dir = Path(row["job_dir"])
        lookup[(row["parent_job"], int(row["image_index"]))] = completed_single_point_energy(job_dir)
    return lookup


def image_energy(
    job_dir: Path,
    image_index: int,
    start_energy: float | None,
    end_energy: float | None,
    n_images: int,
) -> tuple[float | None, str]:
    if image_index == 0:
        return start_energy, "endpoint_start" if start_energy is not None else "missing_endpoint"
    if image_index == n_images + 1:
        return end_energy, "endpoint_end" if end_energy is not None else "missing_endpoint"

    image_dir = job_dir / f"{image_index:02d}"
    outcar_energy = last_energy_from_outcar(image_dir / "OUTCAR")
    if outcar_energy is not None:
        return outcar_energy, "OUTCAR"
    oszicar_energy = last_energy_from_oszicar(image_dir / "OSZICAR")
    if oszicar_energy is not None:
        return oszicar_energy, "OSZICAR"
    return None, "missing"


def parse_job_log(job_dir: Path) -> dict[str, object]:
    log = job_dir / "vasp.log"
    if not log.exists():
        return {
            "vasp_log_exists": False,
            "converged": False,
            "fatal_error": False,
            "last_ionic_step": math.nan,
            "last_brion_gf": math.nan,
        }
    text = log.read_text(errors="replace")
    ion_steps = ION_STEP_RE.findall(text)
    brion = BRION_RE.findall(text)
    return {
        "vasp_log_exists": True,
        "converged": "reached required accuracy - stopping structural energy minimisation" in text,
        "fatal_error": bool(FATAL_RE.search(text)),
        "last_ionic_step": int(ion_steps[-1][0]) if ion_steps else math.nan,
        "last_brion_gf": float(brion[-1].replace("D", "E")) if brion else math.nan,
    }


def build_path_lookup(paths_csv: Path) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    if not paths_csv.exists():
        return lookup
    for row in read_csv(paths_csv):
        key = job_key(row["family"], row["path_id"], row["path_start"], row["path_end"])
        lookup[key] = row
    return lookup


def endpoint_energies_for_job(
    job_dir: Path,
    row: dict[str, str],
    n_images: int,
    endpoint_mode: str,
    endpoint_lookup: dict[tuple[str, int], tuple[float | None, str]],
) -> tuple[float | None, float | None, str]:
    if endpoint_mode == "path_csv":
        return float(row["start_energy_ev"]), float(row["end_energy_ev"]), "endpoints from path_barriers.csv"
    if endpoint_mode == "image_outputs":
        start, start_source = endpoint_energy_from_image_dir(job_dir, 0)
        end, end_source = endpoint_energy_from_image_dir(job_dir, n_images + 1)
        return start, end, f"endpoints from image dirs ({start_source}, {end_source})"
    start, start_source = endpoint_lookup.get((job_dir.name, 0), (None, "missing_endpoint_SP_start"))
    end, end_source = endpoint_lookup.get((job_dir.name, n_images + 1), (None, "missing_endpoint_SP_end"))
    return start, end, f"endpoints from separate endpoint-SP jobs ({start_source}, {end_source})"


def collect(
    job_dirs: list[Path],
    path_lookup: dict[str, dict[str, str]],
    endpoint_mode: str,
    endpoint_lookup: dict[tuple[str, int], tuple[float | None, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    image_rows: list[dict[str, object]] = []
    barrier_rows: list[dict[str, object]] = []
    for job_dir in sorted(job_dirs):
        row = path_lookup.get(job_dir.name)
        if row is None:
            print(f"Skipping {job_dir}: no matching row in paths CSV")
            continue

        n_images = parse_images_count(job_dir)
        ediffg_abs = parse_ediffg_abs(job_dir)
        start_energy, end_energy, endpoint_note = endpoint_energies_for_job(
            job_dir, row, n_images, endpoint_mode, endpoint_lookup
        )
        energies: list[float | None] = []
        sources: list[str] = []
        for image_index in range(n_images + 2):
            energy, source = image_energy(job_dir, image_index, start_energy, end_energy, n_images)
            energies.append(energy)
            sources.append(source)
            image_rows.append(
                {
                    "job": job_dir.name,
                    "family": row["family"],
                    "path_id": row["path_id"],
                    "image": image_index,
                    "reaction_coordinate": image_index / (n_images + 1),
                    "energy_ev": energy if energy is not None else "",
                    "relative_to_start_ev": energy - start_energy if energy is not None and start_energy is not None else "",
                    "relative_to_path_min_ev": "",
                    "source": source,
                    "job_dir": str(job_dir),
                }
            )

        available = [energy for energy in energies if energy is not None]
        complete_images = len(available) == n_images + 2
        rel_to_min = []
        if available:
            min_energy = min(available)
            rel_to_min = [energy - min_energy if energy is not None else None for energy in energies]
            for candidate in image_rows[-(n_images + 2) :]:
                energy = candidate["energy_ev"]
                if isinstance(energy, float):
                    candidate["relative_to_path_min_ev"] = energy - min_energy

        log_status = parse_job_log(job_dir)
        last_brion_gf = log_status["last_brion_gf"]
        gf_below_ediffg = (
            isinstance(last_brion_gf, float)
            and not math.isnan(last_brion_gf)
            and ediffg_abs is not None
            and last_brion_gf < ediffg_abs
        )
        usable_barrier = complete_images and bool(log_status["converged"]) and not bool(log_status["fatal_error"])
        barrier_rows.append(
            {
                "job": job_dir.name,
                "family": row["family"],
                "path_id": row["path_id"],
                "path_start": row["path_start"],
                "path_end": row["path_end"],
                "n_images": n_images,
                "energies_available": len(available),
                "complete_images": complete_images,
                "converged": log_status["converged"],
                "fatal_error": log_status["fatal_error"],
                "last_ionic_step": log_status["last_ionic_step"],
                "ediffg_abs": ediffg_abs if ediffg_abs is not None else "",
                "last_brion_gf": last_brion_gf,
                "last_brion_gf_below_ediffg": gf_below_ediffg,
                "barrier_usable": usable_barrier,
                "barrier_from_start_ev": max(available) - start_energy if usable_barrier and start_energy is not None else "",
                "barrier_from_path_min_ev": max(rel_to_min) if usable_barrier and rel_to_min else "",
                "delta_e_end_minus_start_ev": end_energy - start_energy if usable_barrier and start_energy is not None and end_energy is not None else "",
                "source_note": f"{endpoint_note}; intermediate images from latest VASP image outputs",
                "job_dir": str(job_dir),
            }
        )
    return image_rows, barrier_rows


def plot_profiles(image_rows: list[dict[str, object]], output_dir: Path) -> None:
    if plt is None:
        return
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in image_rows:
        grouped.setdefault(str(row["job"]), []).append(row)

    fig, axes = plt.subplots(2, 5, figsize=(17, 6), sharey=False)
    axes_flat = axes.ravel()
    for ax, (job, rows) in zip(axes_flat, sorted(grouped.items())):
        rows = sorted(rows, key=lambda item: int(item["image"]))
        x = [float(item["reaction_coordinate"]) for item in rows if item["relative_to_start_ev"] != ""]
        y = [float(item["relative_to_start_ev"]) for item in rows if item["relative_to_start_ev"] != ""]
        ax.plot(x, y, marker="o", linewidth=1.5)
        ax.axhline(0.0, color="0.75", linewidth=0.8)
        ax.set_title(job.replace("_", " "), fontsize=8)
        ax.set_xlabel("Reaction coordinate")
        ax.set_ylabel("E - E_start (eV)")
    for ax in axes_flat[len(grouped) :]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_dir / "review_neb_profiles.png", dpi=220)
    plt.close(fig)


def write_markdown(output_dir: Path, barrier_rows: list[dict[str, object]]) -> None:
    completed = sum(bool(row["complete_images"]) for row in barrier_rows)
    converged = sum(bool(row["converged"]) for row in barrier_rows)
    fatal = sum(bool(row["fatal_error"]) for row in barrier_rows)
    lines = [
        "# Review CI-NEB Status",
        "",
        f"- Jobs with all image energies available: {completed}/{len(barrier_rows)}.",
        f"- Jobs reporting VASP ionic convergence: {converged}/{len(barrier_rows)}.",
        f"- Jobs with fatal error markers: {fatal}/{len(barrier_rows)}.",
        "- Endpoint energy source is recorded in `review_neb_barriers.csv` for each row.",
        "- Intermediate image energies are read from latest VASP OUTCAR/OSZICAR files.",
        "- Barrier values are blank until all images are present, VASP reports ionic convergence, and no fatal marker is detected.",
        "",
        "| Job | energies available | converged | fatal | barrier usable | last ionic step | last BRION g(F) | g(F)<|EDIFFG| | barrier from start (eV) | barrier from min (eV) |",
        "| --- | ---: | --- | --- | --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in barrier_rows:
        barrier_start = row["barrier_from_start_ev"]
        barrier_min = row["barrier_from_path_min_ev"]
        lines.append(
            "| {job} | {energies_available} | {converged} | {fatal_error} | {barrier_usable} | {last_ionic_step} | {last_brion_gf} | {gf_below_ediffg} | {barrier_start} | {barrier_min} |".format(
                job=row["job"],
                energies_available=row["energies_available"],
                converged=row["converged"],
                fatal_error=row["fatal_error"],
                barrier_usable=row["barrier_usable"],
                last_ionic_step=row["last_ionic_step"],
                last_brion_gf=f"{row['last_brion_gf']:.4f}" if isinstance(row["last_brion_gf"], float) and not math.isnan(row["last_brion_gf"]) else "",
                gf_below_ediffg=(
                    row["last_brion_gf_below_ediffg"]
                    if isinstance(row["last_brion_gf"], float) and not math.isnan(row["last_brion_gf"])
                    else ""
                ),
                barrier_start=f"{barrier_start:.4f}" if isinstance(barrier_start, float) else "",
                barrier_min=f"{barrier_min:.4f}" if isinstance(barrier_min, float) else "",
            )
        )
    (output_dir / "REVIEW_NEB_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    job_dirs = read_job_dirs(Path(args.job_list))
    path_lookup = build_path_lookup(Path(args.paths_csv))
    endpoint_lookup = build_endpoint_sp_lookup(Path(args.endpoint_manifest)) if args.endpoint_mode == "endpoint_sp" else {}
    image_rows, barrier_rows = collect(job_dirs, path_lookup, args.endpoint_mode, endpoint_lookup)
    write_csv(output_dir / "review_neb_images.csv", image_rows)
    write_csv(output_dir / "review_neb_barriers.csv", barrier_rows)
    write_markdown(output_dir, barrier_rows)
    plot_profiles(image_rows, output_dir)
    print(output_dir / "REVIEW_NEB_STATUS.md")
    return 0 if barrier_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())

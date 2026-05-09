#!/usr/bin/env python3
"""Merge relaxation/SP VASP labels and build deterministic MACE data splits."""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from ase.io import read, write


KNOWN_FAMILIES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create train/valid/test extxyz files from extxyz and OUTCAR inputs."
    )
    parser.add_argument(
        "--extxyz",
        nargs="*",
        default=["data/relax_all_frames.extxyz"],
        help="Existing extxyz files to include.",
    )
    parser.add_argument(
        "--outcar-glob",
        nargs="*",
        default=["dft_sp_outputs/**/OUTCAR"],
        help="OUTCAR glob patterns to parse, usually SP jobs.",
    )
    parser.add_argument("--output-dir", default="data/mace_datasets")
    parser.add_argument("--prefix", default="li_mace")
    parser.add_argument(
        "--include-outcar-all-steps",
        action="store_true",
        help="Read all frames from OUTCAR inputs. Default reads final frame only.",
    )
    return parser.parse_args()


def family_from_config(config_type: str) -> str:
    stripped = re.sub(r"^SP_", "", config_type)
    for family in KNOWN_FAMILIES:
        if stripped == family or stripped.startswith(f"{family}_"):
            return family
    return stripped.split("_site_")[0].split("_path")[0]


def split_for_group(group: str, family_counts: dict[str, int]) -> str:
    family = family_from_config(group)
    index = family_counts[family]
    family_counts[family] += 1
    mod = index % 10
    if mod == 0:
        return "test"
    if mod == 1:
        return "valid"
    return "train"


def normalize_frame(atoms, source: Path, frame_index: int, config_type: str):
    try:
        energy = float(atoms.get_potential_energy())
        forces = np.asarray(atoms.get_forces(), dtype=float)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"missing energy or forces: {exc}") from exc

    atoms = atoms.copy()
    atoms.info["energy"] = energy
    atoms.info["config_type"] = config_type
    atoms.info["source_file"] = str(source)
    atoms.info["source_frame"] = frame_index
    atoms.info["family"] = family_from_config(config_type)
    atoms.arrays["forces"] = forces
    atoms.calc = None
    return atoms


def read_extxyz(path: Path):
    frames = read(path, ":")
    if not isinstance(frames, list):
        frames = [frames]
    normalized = []
    for index, frame in enumerate(frames):
        config_type = str(frame.info.get("config_type") or path.stem)
        normalized.append(normalize_frame(frame, path, index, config_type))
    return normalized


def read_outcar(path: Path, all_steps: bool):
    index = ":" if all_steps else "-1"
    frames = read(path, index=index, format="vasp-out")
    if not isinstance(frames, list):
        frames = [frames]
    config_type = path.parent.name
    return [normalize_frame(frame, path, idx, config_type) for idx, frame in enumerate(frames)]


def collect_frames(args: argparse.Namespace):
    frames = []
    report = {"extxyz": [], "outcars": [], "failed": []}

    for item in args.extxyz:
        for match in sorted(glob.glob(item, recursive=True)):
            path = Path(match)
            if not path.exists():
                continue
            try:
                new = read_extxyz(path)
                frames.extend(new)
                report["extxyz"].append({"file": str(path), "frames": len(new)})
            except Exception as exc:  # noqa: BLE001
                report["failed"].append({"file": str(path), "error": str(exc)})

    outcar_paths: list[Path] = []
    for pattern in args.outcar_glob:
        outcar_paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    for path in sorted(set(outcar_paths)):
        try:
            new = read_outcar(path, args.include_outcar_all_steps)
            frames.extend(new)
            report["outcars"].append({"file": str(path), "frames": len(new)})
        except Exception as exc:  # noqa: BLE001
            report["failed"].append({"file": str(path), "error": str(exc)})

    return frames, report


def split_frames(frames):
    groups: dict[str, list] = defaultdict(list)
    for frame in frames:
        groups[str(frame.info.get("config_type", "Default"))].append(frame)

    family_counts: dict[str, int] = defaultdict(int)
    split_by_group: dict[str, str] = {}
    splits = {"train": [], "valid": [], "test": []}
    for group in sorted(groups):
        group_frames = sorted(
            groups[group],
            key=lambda atoms: int(atoms.info.get("source_frame", 0)),
        )
        if len(group_frames) > 1:
            split_by_group[group] = "frame_round_robin"
            for index, frame in enumerate(group_frames):
                mod = index % 10
                if mod == 0:
                    splits["test"].append(frame)
                elif mod == 1:
                    splits["valid"].append(frame)
                else:
                    splits["train"].append(frame)
        else:
            split = split_for_group(group, family_counts)
            split_by_group[group] = split
            splits[split].extend(group_frames)
    return splits, split_by_group


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frames, report = collect_frames(args)
    if not frames:
        print("No frames were collected.", file=sys.stderr)
        (output_dir / f"{args.prefix}_dataset_report.json").write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )
        return 1

    splits, split_by_group = split_frames(frames)
    all_path = output_dir / f"{args.prefix}_all.extxyz"
    write(all_path, frames, format="extxyz")

    output_paths = {"all": str(all_path)}
    for split, split_frames_list in splits.items():
        path = output_dir / f"{args.prefix}_{split}.extxyz"
        output_paths[split] = str(path)
        if split_frames_list:
            write(path, split_frames_list, format="extxyz")
        else:
            path.write_text("", encoding="utf-8")

    frame_counts = {split: len(split_frames_list) for split, split_frames_list in splits.items()}
    family_counts = Counter(str(frame.info.get("family", "unknown")) for frame in frames)
    split_family_counts = {
        split: dict(Counter(str(frame.info.get("family", "unknown")) for frame in split_frames_list))
        for split, split_frames_list in splits.items()
    }
    report.update(
        {
            "outputs": output_paths,
            "n_frames": len(frames),
            "frame_counts": frame_counts,
            "family_counts": dict(family_counts),
            "split_family_counts": split_family_counts,
            "split_by_group": split_by_group,
        }
    )
    report_path = output_dir / f"{args.prefix}_dataset_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {len(frames)} total frames to {all_path}")
    print(f"Split counts: {frame_counts}")
    print(f"Wrote report to {report_path}")
    if report["failed"]:
        print(f"Warning: skipped {len(report['failed'])} failed inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

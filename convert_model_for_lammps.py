#!/usr/bin/env python3
"""Convert a trained MACE .model file to a LAMMPS-readable TorchScript model."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run mace.cli.create_lammps_model on a trained model."
    )
    parser.add_argument("model", help="Path to trained .model file.")
    parser.add_argument(
        "--format",
        choices=("libtorch", "mliap"),
        default="libtorch",
        help="libtorch matches legacy pair_style mace; mliap is optional.",
    )
    parser.add_argument("--dtype", choices=("float64", "float32"), default="float64")
    parser.add_argument("--head", default=None)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory where a copy of the converted file is placed.",
    )
    return parser.parse_args()


def expected_output(model: Path, fmt: str) -> Path:
    suffix = "-mliap_lammps.pt" if fmt == "mliap" else "-lammps.pt"
    return Path(str(model) + suffix)


def main() -> int:
    args = parse_args()
    model = Path(args.model).resolve()
    if not model.exists():
        print(f"Model not found: {model}", file=sys.stderr)
        return 1

    command = [
        sys.executable,
        "-m",
        "mace.cli.create_lammps_model",
        str(model),
        f"--format={args.format}",
        f"--dtype={args.dtype}",
    ]
    if args.head:
        command.append(f"--head={args.head}")

    env = os.environ.copy()
    env.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
    subprocess.run(command, check=True, env=env)

    output = expected_output(model, args.format)
    if not output.exists():
        print(f"Expected converted model was not created: {output}", file=sys.stderr)
        return 1

    if args.output_dir:
        import shutil

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        copied = output_dir / output.name
        shutil.copy2(output, copied)
        print(copied)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

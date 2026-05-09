#!/usr/bin/env python3
"""Inspect a MACE model before fine-tuning.

This avoids relying on brittle numeric --freeze settings. The fine-tuning script
uses lr_params_factors to keep embedding and interaction parameters fixed while
allowing products/readouts to train.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect MACE model parameter groups.")
    parser.add_argument("model", help="Path to a .model file.")
    parser.add_argument(
        "--check-train-cli",
        action="store_true",
        help="Require mace_run_train to expose lr_params_factors.",
    )
    parser.add_argument("--json-output", default=None)
    return parser.parse_args()


def count_parameters(module) -> tuple[int, int]:
    total = 0
    trainable = 0
    for parameter in module.parameters():
        n_param = parameter.numel()
        total += n_param
        if parameter.requires_grad:
            trainable += n_param
    return total, trainable


def module_stats(model) -> dict[str, dict[str, int]]:
    groups = {
        "node_embedding": getattr(model, "node_embedding", None),
        "radial_embedding": getattr(model, "radial_embedding", None),
        "interactions": getattr(model, "interactions", None),
        "products": getattr(model, "products", None),
        "readouts": getattr(model, "readouts", None),
    }
    stats: dict[str, dict[str, int]] = {}
    for name, module in groups.items():
        if module is None:
            stats[name] = {"present": 0, "total": 0, "trainable": 0}
            continue
        total, trainable = count_parameters(module)
        stats[name] = {"present": 1, "total": total, "trainable": trainable}
    return stats


def infer_num_interactions(model) -> int | None:
    if hasattr(model, "interactions"):
        return len(model.interactions)
    if hasattr(model, "num_interactions"):
        value = model.num_interactions
        try:
            return int(value.item())
        except AttributeError:
            return int(value)
    return None


def check_train_cli() -> None:
    exe = shutil.which("mace_run_train")
    if exe is None:
        raise RuntimeError("mace_run_train is not on PATH. Activate the mace_md env.")
    completed = subprocess.run(
        [exe, "--help"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    help_text = completed.stdout
    required = ["--foundation_model", "--loss", "--lr_params_factors"]
    missing = [flag for flag in required if flag not in help_text]
    if missing:
        raise RuntimeError(
            "mace_run_train is missing required fine-tuning flags: "
            + ", ".join(missing)
        )


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Model not found: {model_path}", file=sys.stderr)
        return 1

    if args.check_train_cli:
        try:
            check_train_cli()
        except Exception as exc:  # noqa: BLE001 - produce direct action.
            print(f"Training CLI check failed: {exc}", file=sys.stderr)
            return 2

    try:
        import torch
    except ImportError as exc:
        print("PyTorch is not installed. Run setup_env.sh first.", file=sys.stderr)
        raise SystemExit(1) from exc

    model = torch.load(model_path, map_location="cpu")
    stats = {
        "model": str(model_path),
        "class": model.__class__.__name__,
        "num_interactions": infer_num_interactions(model),
        "heads": list(getattr(model, "heads", [])),
        "parameter_groups": module_stats(model),
        "recommended_lr_params_factors": {
            "embedding_lr_factor": 0.0,
            "interactions_lr_factor": 0.0,
            "products_lr_factor": 1.0,
            "readouts_lr_factor": 1.0,
        },
    }

    print(json.dumps(stats, indent=2))
    print(
        "Use lr_params_factors instead of a numeric --freeze index for this "
        "fine-tuning workflow.",
        file=sys.stderr,
    )
    if args.json_output:
        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

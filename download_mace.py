#!/usr/bin/env python3
"""Download a MACE foundation model into the local project tree.

The preferred source is Hugging Face. If the exact filename is not present in
the selected repository, the script lists repository files and chooses the best
available medium MPA model. A direct URL fallback can be supplied with
--fallback-url or MACE_MODEL_URL.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import urllib.request
from pathlib import Path


DEFAULT_REPOS = (
    "mace-foundations/mace-mpa-0",
    "ACEsuit/mace-mp",
)
DEFAULT_FILENAMES = (
    "mace-mpa-0-medium.model",
    "mace-mp-0-medium.model",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the MACE-MPA-0 medium foundation model."
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Hugging Face repository to use. Defaults to known MACE-MPA repos.",
    )
    parser.add_argument(
        "--filename",
        default=None,
        help="Exact .model filename. If omitted, choose a medium .model file.",
    )
    parser.add_argument("--revision", default="main", help="Hugging Face revision.")
    parser.add_argument(
        "--destination",
        default="models/foundation",
        help="Directory where the model should be stored.",
    )
    parser.add_argument(
        "--canonical-name",
        default="mace-mpa-0-medium.model",
        help="Stable local filename created for downstream scripts.",
    )
    parser.add_argument(
        "--fallback-url",
        default=os.environ.get("MACE_MODEL_URL"),
        help="Direct model URL used if Hugging Face download fails.",
    )
    return parser.parse_args()


def choose_model_file(api, repo_id: str, revision: str, requested: str | None) -> str:
    files = api.list_repo_files(repo_id=repo_id, revision=revision)
    model_files = [name for name in files if name.endswith(".model")]
    if requested:
        if requested in model_files:
            return requested
        raise FileNotFoundError(
            f"{requested!r} was not found in {repo_id}. Available .model files: "
            + ", ".join(model_files[:20])
        )

    for exact in DEFAULT_FILENAMES:
        if exact in model_files:
            return exact

    def score(name: str) -> tuple[int, str]:
        lower = name.lower()
        value = 0
        if "medium" in lower:
            value += 10
        if "mpa" in lower:
            value += 5
        if "mp-0" in lower or "mpa-0" in lower:
            value += 2
        return (-value, name)

    if not model_files:
        raise FileNotFoundError(f"No .model files found in {repo_id}")
    return sorted(model_files, key=score)[0]


def download_from_hf(args: argparse.Namespace, destination: Path) -> Path:
    try:
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is not installed. Run setup_env.sh first."
        ) from exc

    repos = [args.repo] if args.repo else list(DEFAULT_REPOS)
    errors: list[str] = []
    for repo_id in repos:
        try:
            api = HfApi()
            filename = choose_model_file(api, repo_id, args.revision, args.filename)
            downloaded = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=args.revision,
                local_dir=destination,
                local_dir_use_symlinks=False,
            )
            return Path(downloaded)
        except Exception as exc:  # noqa: BLE001 - keep trying known mirrors.
            errors.append(f"{repo_id}: {exc}")
    raise RuntimeError("Hugging Face download failed:\n" + "\n".join(errors))


def download_from_url(url: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    filename = Path(url.split("?")[0]).name or "mace-mpa-0-medium.model"
    output = destination / filename
    with urllib.request.urlopen(url) as response, output.open("wb") as handle:
        handle.write(response.read())
    return output


def main() -> int:
    args = parse_args()
    destination = Path(args.destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    try:
        path = download_from_hf(args, destination)
    except Exception as hf_error:  # noqa: BLE001 - report clean fallback context.
        if not args.fallback_url:
            print(str(hf_error), file=sys.stderr)
            print(
                "Set MACE_MODEL_URL or pass --fallback-url if this cluster cannot "
                "reach Hugging Face.",
                file=sys.stderr,
            )
            return 1
        print(f"Hugging Face download failed: {hf_error}", file=sys.stderr)
        print(f"Trying direct URL fallback: {args.fallback_url}", file=sys.stderr)
        path = download_from_url(args.fallback_url, destination)

    canonical = destination / args.canonical_name
    if path.resolve() != canonical.resolve():
        shutil.copy2(path, canonical)
        path = canonical

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

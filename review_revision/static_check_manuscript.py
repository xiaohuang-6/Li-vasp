#!/usr/bin/env python3
"""Static checks for the conservative reviewer-revision manuscript.

This does not replace a LaTeX compile, but it catches the common failure modes
that matter before sending the source to a machine with TeX installed:
missing figures, missing bibliography keys, missing labels, and residual
internal revision phrasing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_FORBIDDEN_PHRASES = (
    "first draft",
    "present draft",
    "current manuscript",
    "reviewer-response",
    "reviewer-follow-up",
    "before journal submission",
    "submission-ready",
    "should be added",
    "Yuran Chai",
    "Y.C.:",
    "cannot be sold",
    "publishable screening",
    "two-day computational campaign",
    "high surface area",
    "poorly suited",
    "low-barrier sampled",
    "mechanically and electronically favorable",
    "Wake Forest University",
    "migration landscapes",
)


def _split_cite_keys(cite_body: str) -> list[str]:
    return [key.strip() for key in cite_body.split(",") if key.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tex",
        type=Path,
        default=Path("manuscript/li_mace_graphene_draft.tex"),
        help="Path to the LaTeX manuscript.",
    )
    parser.add_argument(
        "--bib",
        type=Path,
        default=Path("manuscript/references.bib"),
        help="Path to the BibTeX file.",
    )
    args = parser.parse_args()

    tex_path = args.tex
    bib_path = args.bib
    if not tex_path.exists():
        print(f"ERROR: missing manuscript: {tex_path}", file=sys.stderr)
        return 2
    if not bib_path.exists():
        print(f"ERROR: missing bibliography: {bib_path}", file=sys.stderr)
        return 2

    text = tex_path.read_text(encoding="utf-8", errors="replace")
    bib = bib_path.read_text(encoding="utf-8", errors="replace")

    errors: list[str] = []

    figure_refs = re.findall(
        r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text
    )
    for figure_ref in figure_refs:
        figure_path = tex_path.parent / figure_ref
        if not figure_path.exists():
            errors.append(f"missing figure: {figure_path}")

    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", bib))
    cite_keys: set[str] = set()
    for match in re.finditer(r"\\cite[palt]?\{([^}]+)\}", text):
        cite_keys.update(_split_cite_keys(match.group(1)))
    for key in sorted(cite_keys - bib_keys):
        errors.append(f"missing bibliography key: {key}")

    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))
    for ref in sorted(refs - labels):
        errors.append(f"missing label for reference: {ref}")

    lower_text = text.lower()
    for phrase in DEFAULT_FORBIDDEN_PHRASES:
        if phrase.lower() in lower_text:
            errors.append(f"residual internal/overclaiming phrase: {phrase!r}")

    print(f"figures={len(figure_refs)}")
    print(f"cite_keys={len(cite_keys)}")
    print(f"cross_refs={len(refs)}")

    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

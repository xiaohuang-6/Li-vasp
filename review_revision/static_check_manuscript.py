#!/usr/bin/env python3
"""Static and target-journal checks for the reviewer-revision manuscript.

This does not replace a LaTeX compile, but it catches the common failure modes
that matter before sending the source to a machine with TeX installed:
missing figures, missing bibliography keys, missing labels, residual internal
revision phrasing, and Computational Materials Science submission-format drift.
"""

from __future__ import annotations

import argparse
import re
import struct
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
    "approximately",
    "about ",
    "much more strongly",
    "strongly perturb",
    "rare large-displacement events",
    "model-sensitive displacement",
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
    parser.add_argument(
        "--highlights",
        type=Path,
        default=Path("manuscript/highlights.txt"),
        help="Path to the target-journal highlights file.",
    )
    parser.add_argument(
        "--graphical-abstract",
        type=Path,
        default=Path("manuscript/graphical_abstract.png"),
        help="Path to the target-journal graphical abstract.",
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

    ai_declaration_heading = (
        r"\section*{Declaration of generative AI and AI-assisted technologies "
        r"in the manuscript preparation process}"
    )
    if ai_declaration_heading not in text:
        errors.append("missing required generative-AI declaration")

    abstract_match = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, flags=re.DOTALL
    )
    abstract_words = 0
    if abstract_match is None:
        errors.append("missing abstract")
    else:
        abstract_words = len(
            re.findall(
                r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*",
                abstract_match.group(1),
            )
        )
        if abstract_words > 250:
            errors.append(
                f"abstract exceeds Computational Materials Science limit: "
                f"{abstract_words} > 250 words"
            )

    keywords_match = re.search(
        r"\\textbf\{Keywords:\}\s*([^\n]+)",
        text,
    )
    keywords: list[str] = []
    if keywords_match is None:
        errors.append("missing Keywords line")
    else:
        keywords = [
            keyword.strip()
            for keyword in keywords_match.group(1).split(";")
            if keyword.strip()
        ]
        if not 1 <= len(keywords) <= 7:
            errors.append(f"keywords count must be 1--7, found {len(keywords)}")
        if len({keyword.lower() for keyword in keywords}) != len(keywords):
            errors.append("duplicate keywords")

    highlights: list[str] = []
    if not args.highlights.exists():
        errors.append(f"missing highlights: {args.highlights}")
    else:
        highlights = [
            line.removeprefix("- ").strip()
            for line in args.highlights.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not 3 <= len(highlights) <= 5:
            errors.append(f"highlights count must be 3--5, found {len(highlights)}")
        for index, highlight in enumerate(highlights, start=1):
            if len(highlight) > 85:
                errors.append(
                    f"highlight {index} exceeds 85 characters: {len(highlight)}"
                )

    graphical_abstract_size: tuple[int, int] | None = None
    if not args.graphical_abstract.exists():
        errors.append(f"missing graphical abstract: {args.graphical_abstract}")
    else:
        try:
            with args.graphical_abstract.open("rb") as handle:
                signature = handle.read(24)
            if signature[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError("not a PNG file")
            graphical_abstract_size = struct.unpack(">II", signature[16:24])
            if graphical_abstract_size[0] < 1200 or graphical_abstract_size[1] < 600:
                errors.append(
                    "graphical abstract is too small: "
                    f"{graphical_abstract_size[0]}x{graphical_abstract_size[1]}"
                )
        except (OSError, ValueError, struct.error) as exc:
            errors.append(f"invalid graphical abstract: {exc}")

    print(f"figures={len(figure_refs)}")
    print(f"cite_keys={len(cite_keys)}")
    print(f"cross_refs={len(refs)}")
    print(f"abstract_words={abstract_words}")
    print(f"keywords={len(keywords)}")
    print(f"highlights={len(highlights)}")
    if graphical_abstract_size is not None:
        print(
            "graphical_abstract="
            f"{graphical_abstract_size[0]}x{graphical_abstract_size[1]}"
        )

    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

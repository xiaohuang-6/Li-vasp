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
    "stability and displacement diagnostics",
    "revision runs",
    "revision training",
    "revision archive",
    "have now completed",
    "is now treated",
    "current OUTCAR files",
    "trajectory campaign",
    r"are available in the \href",
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
    parser.add_argument(
        "--cover-letter",
        type=Path,
        default=Path("manuscript/cover_letter_computational_materials_science.txt"),
        help="Path to the target-journal cover-letter draft.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--submission-ready",
        action="store_true",
        help=(
            "Also require author-controlled upload gates: a public data link, "
            "a funding statement, and removal of the cover-letter draft banner."
        ),
    )
    mode.add_argument(
        "--archive-only",
        action="store_true",
        help=(
            "Validate the extracted reproducibility archive without separately "
            "uploaded submission-administration files."
        ),
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

    credit_heading = r"\section*{CRediT authorship contribution statement}"
    if credit_heading not in text:
        errors.append("missing required CRediT contribution heading")

    competing_interest_heading = (
        r"\section*{Declaration of competing interests}"
    )
    if competing_interest_heading not in text:
        errors.append("missing required competing-interests heading")

    for snippet, label in (
        ("Yuhan Sun:", "full-name CRediT entry for Yuhan Sun"),
        ("Xiao Huang:", "full-name CRediT entry for Xiao Huang"),
        (
            "no known competing financial interests or personal relationships "
            "that could have appeared to influence the work reported in this paper",
            "standard competing-interest declaration",
        ),
        (
            "After using this tool, the authors reviewed and edited the content "
            "as needed and take full responsibility for the content of the "
            "published article",
            "standard author-responsibility wording in the AI declaration",
        ),
    ):
        if snippet not in text:
            errors.append(f"missing {label}")

    peer_review_archive_statement = (
        "version-pinned reproducibility archive supplied as supplementary "
        "material for peer review"
    )
    if peer_review_archive_statement not in text:
        errors.append("missing truthful peer-review data-access statement")

    data_section_match = re.search(
        r"\\section\*\{Data and Code Availability\}(.*?)(?=\\section|\Z)",
        text,
        flags=re.DOTALL,
    )
    data_section = (
        data_section_match.group(1) if data_section_match is not None else ""
    )
    provisional_data_statement = (
        "A public versioned release or DOI-bearing repository record will "
        "be added and cited before submission"
    )
    data_locator_pattern = r"(?:https?://|\\href\{|\\url\{|doi\s*:)"
    has_data_locator = bool(
        re.search(data_locator_pattern, data_section, flags=re.IGNORECASE)
    )
    if provisional_data_statement not in data_section and not has_data_locator:
        errors.append(
            "missing public FAIR-release commitment or deposited-data locator"
        )

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
    if not args.archive_only:
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
            width, height = graphical_abstract_size
            if width < 1328 or height < 531:
                errors.append(
                    "graphical abstract is too small: "
                    f"{width}x{height}; expected at least 1328x531"
                )
            aspect_ratio = width / height
            if not 2.45 <= aspect_ratio <= 2.55:
                errors.append(
                    "graphical abstract aspect ratio is incompatible with the "
                    f"Elsevier 500:200 format: {aspect_ratio:.3f}:1"
                )
        except (OSError, ValueError, struct.error) as exc:
            errors.append(f"invalid graphical abstract: {exc}")

    cover_letter = ""
    cover_letter_words = 0
    if not args.archive_only:
        if not args.cover_letter.exists():
            errors.append(f"missing cover letter: {args.cover_letter}")
        else:
            cover_letter = args.cover_letter.read_text(
                encoding="utf-8", errors="replace"
            )
            cover_letter_words = len(
                re.findall(
                    r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*",
                    cover_letter,
                )
            )
            if cover_letter_words > 400:
                errors.append(
                    "cover-letter draft is no longer concise: "
                    f"{cover_letter_words} > 400 words"
                )
            for snippet, label in (
                ("Computational Materials Science", "target journal"),
                (
                    "Validation-first DFT-MACE screening of",
                    "current manuscript title",
                ),
                (
                    "version-pinned code-and-data archive",
                    "peer-review archive statement",
                ),
            ):
                if snippet not in cover_letter:
                    errors.append(f"cover letter missing {label}: {snippet!r}")

    if args.submission_ready:
        if re.search(r"(?im)^\s*DRAFT\b", cover_letter):
            errors.append(
                "submission-ready gate: remove the cover-letter DRAFT banner"
            )

        funding_match = re.search(
            r"\\section\*\{Funding\}(.*?)(?=\\section|\Z)",
            text,
            flags=re.DOTALL,
        )
        if funding_match is None or not re.search(
            r"[A-Za-z]", funding_match.group(1)
        ):
            errors.append(
                "submission-ready gate: add the author-confirmed Funding section"
            )

        if not has_data_locator:
            errors.append(
                "submission-ready gate: cite and link the public Option C "
                "research-data deposit in Data and Code Availability"
            )
        else:
            if provisional_data_statement in data_section:
                errors.append(
                    "submission-ready gate: replace the provisional public-data "
                    "promise with the actual deposited-data citation"
                )
            if re.search(
                r"The final submission will cite\s+a public",
                cover_letter,
                flags=re.IGNORECASE,
            ):
                errors.append(
                    "submission-ready gate: replace the cover-letter public-data "
                    "promise with the actual deposited-data citation"
                )

    print(f"figures={len(figure_refs)}")
    print(f"cite_keys={len(cite_keys)}")
    print(f"cross_refs={len(refs)}")
    print(f"abstract_words={abstract_words}")
    print(f"keywords={len(keywords)}")
    if args.archive_only:
        print("highlights=NOT_IN_ARCHIVE")
        print("cover_letter_words=NOT_IN_ARCHIVE")
    else:
        print(f"highlights={len(highlights)}")
        print(f"cover_letter_words={cover_letter_words}")
    print(
        "submission_ready="
        f"{'CHECKED' if args.submission_ready else 'NOT_CHECKED'}"
    )
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

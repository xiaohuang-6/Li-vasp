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


def _read_tex_tree(path: Path, seen: set[Path] | None = None) -> str:
    """Read a manuscript and inline local ``\\input{...}`` files."""
    resolved = path.resolve()
    visited = set() if seen is None else seen
    if resolved in visited:
        return ""
    visited.add(resolved)

    raw = path.read_text(encoding="utf-8", errors="replace")
    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r"\\input\{([^}]+)\}", raw):
        pieces.append(raw[cursor : match.start()])
        input_path = path.parent / match.group(1)
        if input_path.suffix == "":
            input_path = input_path.with_suffix(".tex")
        if input_path.exists():
            pieces.append(_read_tex_tree(input_path, visited))
        else:
            pieces.append(match.group(0))
        cursor = match.end()
    pieces.append(raw[cursor:])
    return "".join(pieces)


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
        default=Path("manuscript/cover_letter_resubmission.txt"),
        help="Path to the target-journal cover-letter draft.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--submission-ready",
        action="store_true",
        help=(
            "Also require author-controlled upload gates: an article-linked "
            "Supplementary Data or deposited-data locator, the confirmed "
            "no-funding statement, and removal of the cover-letter draft banner."
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

    text = _read_tex_tree(tex_path)
    bib = bib_path.read_text(encoding="utf-8", errors="replace")

    errors: list[str] = []
    response_copy_path = Path("manuscript/response_to_reviewers_copy_paste.txt")
    if not args.archive_only and not response_copy_path.is_file():
        errors.append(f"missing copy-paste response file: {response_copy_path}")
    elif not args.archive_only:
        response_copy = response_copy_path.read_text(
            encoding="utf-8", errors="replace"
        )
        if "REVIEWER 2 - ACKNOWLEDGMENT" not in response_copy:
            errors.append(
                "copy-paste response file does not acknowledge satisfied Reviewer 2"
            )
        if response_copy.count("REVIEWER 3 - COMMENT") != 4:
            errors.append(
                "copy-paste response file does not contain 4 Reviewer 3 blocks"
            )
        for snippet in (
            "EDITOR / GENERAL RESPONSE",
            "clean revised manuscript",
            "red strikeout",
        ):
            if snippet not in response_copy:
                errors.append(f"copy-paste response file missing: {snippet}")

    expected_title = (
        r"\title{Machine-learning interatomic potentials for battery materials: "
        r"Defect-dependent lithium adsorption and local transferability on graphene}"
    )
    if expected_title not in text:
        errors.append("missing current machine-learning manuscript title")
    if not re.search(
        r"Message\s+Passing\s+Atomic\s+Cluster\s+Expansion\s+\(MACE\)",
        text,
    ):
        errors.append("MACE is not expanded on the manuscript first page")

    figure_refs = re.findall(
        r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text
    )
    for figure_ref in figure_refs:
        figure_path = tex_path.parent / figure_ref
        if not figure_path.exists():
            figure_path = tex_path.parent / "figures" / figure_ref
        if not figure_path.exists():
            errors.append(f"missing figure: {figure_path}")

    summary_figure_generator = Path(
        "review_revision/plot_science_strengthening_summary.py"
    )
    if not summary_figure_generator.exists():
        errors.append(
            f"missing scientific summary figure generator: "
            f"{summary_figure_generator}"
        )
    else:
        generator_text = summary_figure_generator.read_text(
            encoding="utf-8", errors="replace"
        )
        if "meV/A" in generator_text:
            errors.append(
                "summary figure generator uses ambiguous force units: replace "
                "'meV/A' with an explicit per-angstrom form"
            )
        for snippet, label in (
            ("d3_site_adsorption_energies.csv", "multi-site adsorption input"),
            ("balanced_perturbation_force_errors.csv", "balanced frame input"),
            ("balanced_perturbation_force_summary.csv", "balanced summary input"),
            ("foundation_snapshot_force_summary.csv", "foundation force input"),
            ("grouped_e0_snapshot_force_summary.csv", "fine-tuned force input"),
            ("foundation_snapshot_force_errors.csv", "foundation frame input"),
            ("grouped_e0_snapshot_force_errors.csv", "fine-tuned frame input"),
        ):
            if snippet not in generator_text:
                errors.append(f"summary figure generator missing {label}")

    graphical_abstract_generator = Path(
        "review_revision/plot_graphical_abstract_reframe.py"
    )
    if not graphical_abstract_generator.exists():
        errors.append(
            f"missing graphical abstract generator: {graphical_abstract_generator}"
        )
    else:
        graphical_generator_text = graphical_abstract_generator.read_text(
            encoding="utf-8", errors="replace"
        )
        for snippet, label in (
            ("d3_site_adsorption_energies.csv", "strict multi-site adsorption input"),
            (
                "balanced_perturbation_force_summary.csv",
                "balanced force-benchmark input",
            ),
        ):
            if snippet not in graphical_generator_text:
                errors.append(f"graphical abstract generator missing {label}")
        for stale_value in ("1149", "1107", "310", "114"):
            if stale_value in graphical_generator_text:
                errors.append(
                    "graphical abstract generator contains superseded "
                    f"snapshot value: {stale_value}"
                )

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

    for snippet, label in (
        ("In total, 16", "total converged DFT snapshot count"),
        ("Seven additional Si$_4$--graphene snapshots", "seven extended checks"),
        ("The force-error comparison uses the initial nine snapshots", "nine-frame force comparison scope"),
        (r"\section*{Supplementary Data}", "Supplementary Data section"),
    ):
        if snippet not in text:
            errors.append(f"missing {label}")

    if len(figure_refs) != 6:
        errors.append("R2 must include the two R1 main figures and all four SI figures")
    for snippet, label in (
        (r"\label{tab:si_mace_errors}", "MACE error table"),
        (r"\label{tab:si_d3_sites}", "multi-site D3 adsorption table"),
        (r"\label{tab:si_balanced_force}", "balanced-force table"),
        (r"\label{tab:si_path_scans}", "fixed-path table"),
        (r"\label{tab:si_md_runs}", "trajectory-context table"),
        (r"\label{tab:si_initial_snapshots}", "initial snapshot table"),
        (r"\label{tab:si_extended_snapshots}", "extended snapshot table"),
        (r"\label{tab:si_concurrent_learning}", "concurrent-learning comparison table"),
    ):
        if snippet not in text:
            errors.append(f"Main manuscript missing migrated {label}")

    lower_text = text.lower()
    for phrase in DEFAULT_FORBIDDEN_PHRASES:
        if phrase.lower() in lower_text:
            errors.append(f"residual internal/overclaiming phrase: {phrase!r}")

    ai_declaration_heading = (
        r"\section*{Declaration of generative AI and AI-assisted technologies "
        r"in the manuscript preparation process}"
    )
    if ai_declaration_heading not in text:
        errors.append("missing generative-AI declaration heading")
    ai_declaration_text = (
        "During the preparation of this work, the authors used OpenAI Codex to "
        "support language editing, consistency checks, and code-assisted "
        "verification of manuscript reported values. After using this tool, the "
        "authors reviewed and edited the content as needed and take full "
        "responsibility for the content of the published article."
    )
    if ai_declaration_text not in text:
        errors.append("missing or altered generative-AI declaration text")

    credit_heading = r"\section*{Credit authorship contribution statement}"
    if credit_heading not in text:
        errors.append("missing required Credit contribution heading")

    competing_interest_heading = (
        r"\section*{Declaration of competing interests}"
    )
    if competing_interest_heading not in text:
        errors.append("missing required competing-interests heading")

    for snippet, label in (
        (
            r"\author{Yuhan Sun$^{a,\dagger}$ and Xiao Huang$^{b,*,\dagger}$}",
            "equal-contribution author markers",
        ),
        (
            r"$^\dagger$These authors contributed equally to this work.",
            "first-page equal-contribution statement",
        ),
        (
            "Yuhan Sun and Xiao Huang contributed equally to Conceptualization",
            "joint equal-contribution Credit statement",
        ),
        ("Xiao Huang additionally contributed Supervision.", "supervision role"),
        (
            "no known competing financial interests or personal relationships "
            "that could have appeared to influence the work reported in this paper",
            "standard competing-interest declaration",
        ),
    ):
        if snippet not in text:
            errors.append(f"missing {label}")

    supplementary_archive_statement = (
        "A version-pinned reproducibility archive is provided with this article "
        "as Supplementary Data."
    )
    if " ".join(supplementary_archive_statement.split()) not in " ".join(text.split()):
        errors.append("missing truthful supplementary data-access statement")

    data_section_match = re.search(
        r"\\section\*\{Data and Code Availability\}(.*?)(?=\\section|\Z)",
        text,
        flags=re.DOTALL,
    )
    data_section = (
        data_section_match.group(1) if data_section_match is not None else ""
    )
    if "will make it public immediately after manuscript submission" in data_section:
        errors.append(
            "Data and Code Availability contains a submission-stage GitHub "
            "promise that is unsuitable for the published article"
        )
    provisional_data_statement = (
        "A public versioned release or DOI-bearing repository record will "
        "be added and cited before submission"
    )
    data_locator_pattern = (
        r"(?:https?://|\\href\{|\\url\{|doi\s*:|Supplementary Data)"
    )
    has_data_locator = bool(
        re.search(data_locator_pattern, data_section, flags=re.IGNORECASE)
    )
    if provisional_data_statement not in data_section and not has_data_locator:
        errors.append(
            "missing article-linked Supplementary Data or deposited-data locator"
        )
    for snippet, label in (
        ("file-level SHA256 manifest", "file-integrity record"),
        ("source-commit identifier", "source version identifier"),
        ("CC BY 4.0", "curated-data license"),
        ("licensed under MIT", "workflow-code license"),
    ):
        if snippet not in data_section:
            errors.append(f"Data and Code Availability missing {label}")

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
        if "285.2" in abstract_match.group(1) or "20.1" in abstract_match.group(1):
            errors.append("correlated same-workflow metric remains in Abstract")

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
        if not 1 <= len(keywords) <= 6:
            errors.append(f"keywords count must be 1--6, found {len(keywords)}")
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
            if "meV/A" in cover_letter:
                errors.append(
                    "cover letter uses ambiguous force units: replace 'meV/A' "
                    "with an explicit per-angstrom form"
                )
            normalized_cover_letter = " ".join(cover_letter.split())
            for snippet, label in (
                ("Computational Materials Science", "target journal"),
                (
                    "Machine-learning interatomic potentials for battery materials",
                    "current manuscript title",
                ),
                (
                    "version-pinned code-and-data archive",
                    "peer-review archive statement",
                ),
                ("Both authors contributed equally", "equal-contribution statement"),
            ):
                if snippet not in normalized_cover_letter:
                    errors.append(f"cover letter missing {label}: {snippet!r}")

    journal_facing_text = "\n".join((text, cover_letter, "\n".join(highlights)))
    normalized_journal_facing_text = " ".join(journal_facing_text.split())
    for stale_claim in (
        "-3.349 to +0.009",
        "-0.634 eV",
        "+0.009 eV",
        "2.481 eV",
        "2.715 eV",
        "0.694 eV",
        "2.481 and 2.715",
        "0.643 eV less favorable",
        "3.358 eV",
        "from 310 to 114",
        "1149 to 1107",
        "from 710 to 646",
    ):
        if stale_claim in normalized_journal_facing_text:
            errors.append(f"superseded scientific claim remains: {stale_claim!r}")

    response_letter_path = Path(
        "review_revision/RESPONSE_LETTER_SUBMISSION_DRAFT.md"
    )
    if response_letter_path.exists():
        response_letter = response_letter_path.read_text(
            encoding="utf-8", errors="replace"
        )
        for snippet, replacement in (
            ("meV/A", "meV per angstrom"),
            ("meV A^-1", "meV per angstrom"),
            ("meV atom^-1", "meV per atom"),
            (" A^2", " angstrom^2"),
            ("sub-A", "sub-angstrom"),
            ("current OUTCAR files", "checked OUTCAR files"),
        ):
            if snippet in response_letter:
                errors.append(
                    "submission response uses ambiguous or volatile wording: "
                    f"replace {snippet!r} with {replacement!r}"
                )

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
        no_funding_statement = (
            "This research did not receive any specific grant from funding "
            "agencies in the public, commercial, or not-for-profit sectors."
        )
        if (
            funding_match is None
            or no_funding_statement not in funding_match.group(1)
        ):
            errors.append(
                "submission-ready gate: add the exact author-confirmed "
                "no-funding statement"
            )

        if not has_data_locator:
            errors.append(
                "submission-ready gate: identify the article-linked Supplementary "
                "Data or a public research-data deposit in Data and Code Availability"
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

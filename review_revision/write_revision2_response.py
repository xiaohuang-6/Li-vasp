#!/usr/bin/env python3
"""Generate R2 responses with locations from the final clean TeX auxiliary file."""
from pathlib import Path
import re
from build_revision2 import ROOT, compile_tex
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--output", type=Path, default=ROOT / "resubmission/COMMAT_R2_20260913")
    args = parser.parse_args()
    aux = (ROOT / "tmp/revision2-build/Revised_Manuscript_Clean.aux").read_text()
    labels = {m[1]: (m[2], m[3]) for m in re.finditer(
        r"\\newlabel\{([^}]+)\}\{\{([^}]+)\}\{([^}]+)\}", aux
    )}
    def passage(key: str, description: str) -> str:
        first, last = labels[f"r2:{key}-start"], labels[f"r2:{key}-end"]
        pages = f"p. {first[1]}" if first[1] == last[1] else f"pp. {first[1]}-{last[1]}"
        return f"{description}, {pages}, lines {first[0]}-{last[0]}"
    def item(key: str, kind: str) -> str:
        number, page = labels[key]
        return f"{kind} {number}, p. {page}"

    abstract = passage("abstract", "Abstract, single paragraph")
    introduction = passage("concurrent", "Introduction, paragraph 3")
    conclusion = passage("conclusion", "Conclusion, paragraphs 1-2")
    workflow = passage("workflow", "Section 2.3, from the split description through the independent benchmark protocol")
    adsorption = passage("adsorption", "Section 3.1, opening three paragraphs")
    paths = passage("paths", "Section 3.2, the paragraphs before and after the path figure/table")
    dynamics = passage("dynamics", "Section 3.5, opening paragraph")
    formula_ads = passage("ads-eq", "Section 2.2, adsorption equation and the following sentence")
    formula_msd = passage("msd-eq", "Section 2.4, final paragraph and displacement equation")
    moved = [
        ("fig:si_dataset_counts", "Figure", "dataset composition"),
        ("fig:si_site_scan", "Figure", "fixed-geometry Li site energies"),
        ("fig:si_path_scan", "Figure", "all ten fixed-geometry interpolation paths"),
        ("fig:si_md_traces", "Figure", "finite-temperature displacement histories"),
    ]
    figures = "; ".join(f"{item(key, kind)} ({desc})" for key, kind, desc in moved)
    tables = "; ".join(item(key, "Table") for key in (
        "tab:si_concurrent_learning", "tab:si_d3_sites", "tab:si_path_scans",
        "tab:si_mace_errors", "tab:si_balanced_force", "tab:si_md_runs",
        "tab:si_initial_snapshots", "tab:si_extended_snapshots",
    ))
    general = (
        "Thank you for the further assessment of COMMAT-D-26-03061R1. We have revised "
        "the presentation in response to the four points raised by Reviewer 3. The "
        "submission includes a clean editable LaTeX manuscript, a clean PDF for review, "
        "and a separate marked PDF compared with the submitted R1. All locations below "
        "refer to the clean revised manuscript (Revised_Manuscript_Clean.pdf). The marked "
        "copy includes deleted text and consequently has different page and line numbers. "
        "We have moved every scientific figure and table from the previous Supporting "
        "Information into the main article and revised the discussion around them. "
        "The Supplementary Data archive retains the underlying configurations, models, "
        "and code. Highlights, the graphical abstract, competing-interest declaration, "
        "and manuscript source files accompany this resubmission."
    )
    responses = [
        ("Revision marking and traceable references",
         "We apologize for the difficulty in checking the previous revision. The marked "
         "PDF now opens with a color-code legend: blue denotes added text, red strikeout "
         "denotes deleted text, and black denotes unchanged text. Changes are generated "
         "against the R1 manuscript source, including its Results file. Scientific colors "
         "inside figures retain their original meaning. Material moved from the R1 "
         "Supporting Information is identified as an addition to the main manuscript. "
         "A separate clean revised manuscript is supplied. We rebuilt the location "
         "references from the clean manuscript's LaTeX line labels after compilation; "
         "the references do not use the marked copy's numbering.",
         "Marked manuscript, legend on its first page. All references in this response "
         "are to the clean PDF. For example: " + abstract + "; " + formula_msd + "."),
        ("Grammar, syntax, and academic language",
         "We have proofread the manuscript and revised the Abstract, Introduction, "
         "Results and Discussion, and Conclusion for grammar, sentence structure, "
         "and consistency. The Abstract now proceeds from the adsorption problem to "
         "the DFT and MACE comparison, the main numerical findings, and their implication "
         "for additional training data. We removed repetitive statements about the "
         "significance of the results and replaced them with descriptions of the measured "
         "energy and force differences. The Methods retain the training and DFT settings, "
         "while the Results explain the figures in the order used to develop the argument. "
         "We also corrected two imprecise statements: 113 meV per angstrom is not more "
         "than an order of magnitude above 20.1, and only the initial nine of the sixteen "
         "DFT snapshots enter the reported force comparison. These corrections do not "
         "change the numerical results or the conclusions. The split description is "
         "organized by the purpose of the two partitions, and repeated scope statements "
         "have been consolidated in the Methods. The final Discussion subsection now "
         "explains the contribution of configuration-resolved validation to potential "
         "development, linking each benchmark to the physical property it evaluates.",
         abstract + "; " + introduction + "; " + adsorption + "; " + conclusion + "."),
        ("Equation and symbol rendering",
         "The clean manuscript and the marked copy are generated directly from LaTeX. "
         "Equations, Greek letters, subscripts, superscripts, and units use LaTeX math "
         "commands. Negative energies now use mathematical minus signs, force and "
         "squared-length units use siunitx, and mesh dimensions use a single math "
         "environment. We retained the adsorption-energy equation and added an explicit "
         "definition of the in-plane, Li-group-relative mean-squared displacement. "
         "The latter specifies the center-of-mass subtraction used by the LAMMPS "
         "calculation. We checked the compiled PDFs for unresolved references, missing "
         "characters, and placeholder symbols, and inspected the rendered equations "
         "and table headings. The editable source ZIP contains the full main manuscript, "
         "bibliography, and all six figure assets at the archive root.",
         formula_ads + "; " + formula_msd + "; " + workflow + "."),
        ("Figures supporting the scientific argument",
         "The main manuscript now contains six figures instead of two. All four figures "
         "and all eight tables from the previous Supporting Information have been moved "
         "into the main article. The dataset figure explains the scope and correlations "
         "of the training configurations. The site-energy figure connects the original "
         "PBE ranking to the placements used for the adsorption comparison. The ten-panel "
         "path figure shows the local energy variation sampled by the training set; "
         "the Methods define the distinction between fixed-path spans and migration "
         "barriers. The displacement traces explain the finite-temperature sampling "
         "and motivate the direct DFT force tests. Each figure has a caption, is cited "
         "in the text, and is discussed in the relevant Methods or Results subsection. "
         "The site panels now have labels (a)-(e), the path panels retain labels "
         "(a)-(j), and the displacement panels retain "
         "labels (a)/(b), distinct colors, line styles, and markers.",
         figures + ". Related discussion: " + paths + "; " + dynamics + ". "
         "The transferred tables are " + tables + "."),
    ]
    reviewer2 = "Thank you for your assessment. We understand that no further changes were requested. The distinctions accepted in R1 remain explicit: the grouped split is small, the committee is a seed-sensitivity diagnostic, fixed paths are not migration barriers, no diffusion coefficient is inferred, and the DFT snapshot labels have not entered another training cycle."
    text = "COMMAT-D-26-03061R1: RESPONSE FOR SECOND RESUBMISSION\n\n"
    text += "EDITOR / GENERAL RESPONSE\n\nResponse: " + general + "\n\n"
    text += "REVIEWER 2 - ACKNOWLEDGMENT\n\nResponse: " + reviewer2 + "\n\n"
    for index, (title, response, location) in enumerate(responses, 1):
        text += f"REVIEWER 3 - COMMENT {index}: {title}\n\nResponse: {response}\n\nChanges in the clean revised manuscript: {location}\n\n"
    (ROOT / "manuscript/response_to_reviewers_copy_paste.txt").write_text(text)
    def escape(value: str) -> str:
        return "".join({"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#"}.get(c, c) for c in value)
    tex = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage{newtxtext,newtxmath}
\usepackage[margin=1in]{geometry}
\usepackage{parskip}
\usepackage[hidelinks]{hyperref}
\emergencystretch=3em
\begin{document}
\begin{center}\Large Response to the editor and reviewers\\
\normalsize COMMAT-D-26-03061R1: second resubmission\end{center}
\section*{General response}
""" + escape(general) + "\n"
    tex += r"\section*{Reviewer 2}" + "\n" + escape(reviewer2) + "\n"
    tex += r"\section*{Reviewer 3}" + "\n"
    for index, (title, response, location) in enumerate(responses, 1):
        tex += rf"\subsection*{{Comment {index}: {escape(title)}}}" + "\n"
        tex += escape(response) + "\n\n" + r"\textit{Locations in the clean revised manuscript:} " + escape(location) + "\n"
    tex += r"\section*{Closing statement}" + "\nWe thank the editor and reviewers for identifying the presentation problems and for their further consideration of this revision.\n" + r"\end{document}" + "\n"
    source = ROOT / "manuscript/response_to_reviewers.tex"
    source.write_text(tex)
    compile_tex(args.tectonic, source)
    args.output.mkdir(parents=True, exist_ok=True)
    import shutil
    for path, name in [(source.with_suffix(".pdf"), "Response_to_Reviewers.pdf"),
                       (ROOT / "manuscript/response_to_reviewers_copy_paste.txt", "Response_to_Reviewers_Copy_Paste.txt")]:
        shutil.copy2(path, args.output / name)
    print(args.output / "Response_to_Reviewers_Copy_Paste.txt")


if __name__ == "__main__":
    main()

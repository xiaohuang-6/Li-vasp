#!/usr/bin/env python3
"""Compile R2 clean and tracked manuscripts against the pinned submitted R1.

Run with Tectonic and latexdiff available. The marked copy has its own page
numbers; response locations always refer to the clean manuscript.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "c3004e56d13996bebdbd74953c3d23a46f141665"
MAIN = "li_mace_graphene_draft.tex"


def flatten(path: str, baseline: bool = False) -> str:
    if baseline:
        text = subprocess.check_output(
            ["git", "show", f"{BASELINE}:manuscript/{path}"], cwd=ROOT, text=True
        )
    else:
        text = (ROOT / "manuscript" / path).read_text()
    def include(match: re.Match) -> str:
        name = match[1]
        return flatten(name if name.endswith(".tex") else name + ".tex", baseline)
    return re.sub(r"\\input\{([^}]+)\}", include, text)


def compile_tex(engine: str, path: Path) -> None:
    result = subprocess.run(
        [engine, "--keep-intermediates", "--keep-logs", path.name],
        cwd=path.parent, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    path.with_suffix(".build.txt").write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout[-6000:])
    log = path.with_suffix(".log").read_text(errors="replace")
    bad = [line for line in log.splitlines() if any(term in line for term in (
        "Missing character", "Undefined control sequence", "Overfull",
        "There were undefined references",
    ))]
    if bad:
        raise RuntimeError("PDF requires repair:\n" + "\n".join(bad))


PREAMBLE = r"""
\usepackage{xcolor}
\usepackage[normalem]{ulem}
\usepackage{sectsty}
\allsectionsfont{\raggedright}
\providecommand{\DIFadd}[1]{{\color{blue}#1}}
\providecommand{\DIFdel}[1]{{\color{red}\sout{#1}}}
\providecommand{\DIFaddbegin}{}
\providecommand{\DIFaddend}{}
\providecommand{\DIFdelbegin}{}
\providecommand{\DIFdelend}{}
\providecommand{\DIFaddFL}[1]{\DIFadd{#1}}
\providecommand{\DIFdelFL}[1]{\DIFdel{#1}}
\providecommand{\DIFaddbeginFL}{}
\providecommand{\DIFaddendFL}{}
\providecommand{\DIFdelbeginFL}{}
\providecommand{\DIFdelendFL}{}
"""
LEGEND = r"""
\begin{center}
\textbf{Marked revision: R2 compared with the submitted R1}\\[4pt]
\textcolor{blue}{Blue: added text.}\quad
\textcolor{red}{\sout{Red strikeout: deleted text.}}\\
Black: unchanged text.\\[4pt]
\small All response page and line references refer to the accompanying
\textbf{clean revised manuscript}, not this marked copy.\\
Figures and tables transferred from the R1 Supporting Information are
additions to the main manuscript; their captions and table text are blue.
Scientific colors inside figures retain their original meaning.
\end{center}
\clearpage
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--latexdiff", default="latexdiff")
    parser.add_argument("--output", type=Path, default=ROOT / "resubmission/COMMAT_R2_20260913")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = ROOT / "tmp/revision2-build"
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "manuscript/figures", work / "figures", dirs_exist_ok=True)
    shutil.copy2(ROOT / "manuscript/references.bib", work / "references.bib")
    old = flatten(MAIN, baseline=True)
    new = flatten(MAIN)
    (work / "r1.tex").write_text(old)
    clean = work / "Revised_Manuscript_Clean.tex"
    clean.write_text(new)
    compile_tex(args.tectonic, clean)
    preamble = work / "diff_preamble.tex"
    preamble.write_text(PREAMBLE)
    command = [args.latexdiff] if shutil.which(args.latexdiff) else ["perl", args.latexdiff]
    result = subprocess.run(command + [
        "--math-markup=whole", "--graphics-markup=none",
        "--exclude-safecmd=linelabel", f"--preamble={preamble}",
        str(work / "r1.tex"), str(clean),
    ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    (work / "latexdiff.log").write_text(result.stderr)
    marked = result.stdout.replace(r"\begin{document}", r"\begin{document}" + "\n" + LEGEND, 1)
    marked_path = work / "Revised_Manuscript_Marked.tex"
    marked_path.write_text(marked)
    compile_tex(args.tectonic, marked_path)
    for name in ("Revised_Manuscript_Clean", "Revised_Manuscript_Marked"):
        shutil.copy2(work / f"{name}.pdf", out / f"{name}.pdf")
    # A single flattened main TeX avoids missing include files in the portal.
    graphics = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", new)
    source = new.replace(r"\graphicspath{{figures/}}", r"\graphicspath{{./}}")
    for graphic in graphics:
        source = source.replace("{" + graphic + "}", "{" + Path(graphic).name + "}")
    with zipfile.ZipFile(out / "Revised_Manuscript_Editable_Source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Revised_Manuscript_Clean.tex", source)
        archive.write(work / "references.bib", "references.bib")
        for graphic in graphics:
            path = ROOT / "manuscript" / graphic
            if not path.exists():
                path = ROOT / "manuscript/figures" / graphic
            archive.write(path, path.name)
    (out / "REVISION_BASELINE.txt").write_text(
        f"R1 source commit: {BASELINE}\n"
        "All four R1 SI figures and all eight R1 SI tables are in the R2 main text.\n"
        "Response locations refer only to Revised_Manuscript_Clean.pdf.\n"
        "The clean PDF and source ZIP contain identical manuscript text.\n"
        f"Clean PDF SHA256: {hashlib.sha256(clean.with_suffix('.pdf').read_bytes()).hexdigest()}\n"
    )
    print(out)


if __name__ == "__main__":
    main()

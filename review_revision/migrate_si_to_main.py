#!/usr/bin/env python3
"""Move the R1 SI floats verbatim into individually includable R2 source files.

The pinned source and label assertions prevent silent loss of tables or data.
Run only when initially preparing R2; subsequent prose edits belong in TeX.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "c3004e56d13996bebdbd74953c3d23a46f141665"
SOURCE = subprocess.check_output(
    ["git", "show", f"{BASELINE}:manuscript/supporting_information.tex"],
    cwd=ROOT, text=True,
)
blocks = re.findall(r"\\begin\{(figure|table)\}\[H\].*?\\end\{\1\}", SOURCE, re.S)
assert len(blocks) == 12
for match in re.finditer(r"\\begin\{(figure|table)\}\[H\].*?\\end\{\1\}", SOURCE, re.S):
    block = match.group(0)
    label = re.search(r"\\label\{(?:fig|tab):si_([^}]+)\}", block).group(1)
    target = ROOT / "manuscript" / f"evidence_{label}.tex"
    if target.exists():
        raise FileExistsError(target)
    block = block.replace("[H]", "[!htbp]")
    # Fixed-width SI columns must fit the narrower main manuscript text block.
    block = block.replace("p{2.5cm}p{5.0cm}p{6.0cm}", "p{2.1cm}p{5.2cm}p{7.1cm}")
    block = block.replace("\\footnotesize", "\\small").replace("\\scriptsize", "\\footnotesize")
    block = block.replace("0.75\\textwidth", "0.92\\textwidth")
    target.write_text(block + "\n", encoding="utf-8")
print("Extracted all 4 figures and 8 tables from the pinned R1 SI.")

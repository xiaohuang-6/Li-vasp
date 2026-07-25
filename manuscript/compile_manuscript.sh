#!/usr/bin/env bash
# Compile the reviewer-revision LaTeX manuscript when a TeX engine is available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEX_FILE="${1:-li_mace_graphene_draft.tex}"
BASE="${TEX_FILE%.tex}"

cd "${SCRIPT_DIR}"

if command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode -halt-on-error "${TEX_FILE}"
elif command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -halt-on-error "${TEX_FILE}"
    bibtex "${BASE}"
    pdflatex -interaction=nonstopmode -halt-on-error "${TEX_FILE}"
    pdflatex -interaction=nonstopmode -halt-on-error "${TEX_FILE}"
else
    echo "No usable LaTeX toolchain found." >&2
    echo "Install latexmk/pdflatex+bibtex or load a TeX module, then rerun:" >&2
    echo "  cd ${SCRIPT_DIR}" >&2
    echo "  bash compile_manuscript.sh" >&2
    exit 127
fi

echo "Built ${SCRIPT_DIR}/${BASE}.pdf"


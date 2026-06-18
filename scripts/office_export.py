"""Export Office documents to PDF / PNG via COM automation (Windows + MS Office).

Used to produce the PDF deliverables and per-slide PNGs for visual QA, since
LibreOffice/pandoc-pdf are not installed but PowerPoint and Word are.

Usage:
    python scripts/office_export.py pptx  HP-Bot-presentation.pptx  HP-Bot-presentation.pdf  screenshots/slides
    python scripts/office_export.py docx  HP-Bot-Report.docx        HP-Bot-Report.pdf
"""

from __future__ import annotations

import os
import sys

import win32com.client as win32

PP_SAVE_PDF = 32    # ppSaveAsPDF
WD_PDF = 17         # wdFormatPDF


def _abs(p: str) -> str:
    return os.path.abspath(p)


def pptx_export(pptx: str, pdf: str | None, png_dir: str | None, width=1920, height=1080) -> None:
    app = win32.Dispatch("PowerPoint.Application")
    app.Visible = 1
    pres = app.Presentations.Open(_abs(pptx), ReadOnly=1, WithWindow=False)
    try:
        if png_dir:
            os.makedirs(_abs(png_dir), exist_ok=True)
            pres.Export(_abs(png_dir), "PNG", width, height)
            print(f"png  -> {png_dir}/  ({pres.Slides.Count} slides)")
        if pdf:
            pres.SaveAs(_abs(pdf), PP_SAVE_PDF)  # SaveAs flips active format — do last
            print(f"pdf  -> {pdf}")
    finally:
        pres.Close()
        app.Quit()


def docx_export(docx: str, pdf: str) -> None:
    app = win32.Dispatch("Word.Application")
    app.Visible = 0
    doc = app.Documents.Open(_abs(docx), ReadOnly=1)
    try:
        doc.SaveAs(_abs(pdf), WD_PDF)
        print(f"pdf  -> {pdf}")
    finally:
        doc.Close(False)
        app.Quit()


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    kind = argv[0]
    if kind == "pptx":
        pptx = argv[1]
        pdf = argv[2] if len(argv) > 2 and argv[2] != "-" else None
        png_dir = argv[3] if len(argv) > 3 and argv[3] != "-" else None
        pptx_export(pptx, pdf, png_dir)
    elif kind == "docx":
        docx_export(argv[1], argv[2])
    else:
        print(f"unknown kind: {kind}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

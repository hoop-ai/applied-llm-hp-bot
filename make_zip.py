"""Package the project for submission.

Excludes .venv, indices, __pycache__, and the generated zip itself. Does NOT
include .env — the grader copies .env.example to .env and pastes their own
OpenRouter key (see SUBMISSION.md §2).

Usage:  python make_zip.py
Output: HP-Bot.zip in the project root.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "HP-Bot.zip"

INCLUDE_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    "REPORT.md",
    "REPORT-eval-new-corpus.md",
    "SUBMISSION.md",
    "HP-Bot-presentation.pptx",
    "HP-Bot-presentation.pdf",
    "HP-Bot-Report.docx",
    "HP-Bot-Report.pdf",
    ".env.example",
    ".gitignore",
    "make_zip.py",
]
INCLUDE_DIRS = ["src", "tests", "data", "docs", "scripts", ".streamlit", "screenshots"]
# Working/QA render folders and logs are regenerable — keep them out of the submission.
EXCLUDE_DIR_NAMES = {
    "__pycache__", ".venv", "indices", ".pytest_cache", ".git",
    "slides", "report_qa", "_flowtmp",
}
EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo", ".log"}


def main() -> None:
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name in INCLUDE_FILES:
            f = ROOT / name
            if f.is_file():
                z.write(f, arcname=name)
        for d in INCLUDE_DIRS:
            base = ROOT / d
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                    continue
                if path.suffix in EXCLUDE_FILE_SUFFIXES:
                    continue
                if path.is_file():
                    z.write(path, arcname=str(path.relative_to(ROOT)))
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"wrote {OUT.name}  ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

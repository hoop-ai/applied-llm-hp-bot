"""Package the project for submission.

Excludes .venv, indices, __pycache__, and the generated zip itself. Includes
.env (user explicitly approved — the API key has a $5 cap).

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
    ".env",
    ".env.example",
    ".gitignore",
    "make_zip.py",
]
INCLUDE_DIRS = ["src", "tests", "data", "docs", ".streamlit"]
EXCLUDE_DIR_NAMES = {"__pycache__", ".venv", "indices", ".pytest_cache", ".git"}
EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo"}


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

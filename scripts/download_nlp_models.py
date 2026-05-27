#!/usr/bin/env python3
"""Download spaCy models required for NLP analysis."""

from __future__ import annotations

import subprocess
import sys

MODEL = "en_core_web_sm"


def main() -> int:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", MODEL])
    print(f"Installed spaCy model: {MODEL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Start the Project Castle web app locally (venv, deps, Flask, browser)."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = os.environ.get("FLASK_PORT", "5000")
URL = f"http://{HOST}:{PORT}/"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _ensure_environment() -> Path:
    if sys.prefix != sys.base_prefix:
        python = Path(sys.executable)
    else:
        python = _venv_python()
        if not python.exists():
            print("Creating virtual environment in .venv …")
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("Installing dependencies …")
        subprocess.check_call(
            [str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"],
            cwd=ROOT,
        )
        subprocess.check_call(
            [str(python), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
            cwd=ROOT,
        )
        try:
            subprocess.check_call(
                [str(python), str(ROOT / "scripts" / "download_nlp_models.py")],
                cwd=ROOT,
            )
        except subprocess.CalledProcessError:
            print("Warning: spaCy model not installed; NLP will use regex fallback.")
    return python


def _open_browser() -> None:
    time.sleep(1.25)
    webbrowser.open(URL)


def main() -> int:
    os.chdir(ROOT)
    python = _ensure_environment()

    print(f"\n  Project Castle dev server\n  {URL}\n  Press Ctrl+C to stop.\n")

    threading.Thread(target=_open_browser, daemon=True).start()

    env = os.environ.copy()
    env.setdefault("FLASK_APP", "web_app")
    env.setdefault("FLASK_DEBUG", "1")

    try:
        subprocess.check_call(
            [
                str(python),
                "-m",
                "flask",
                "run",
                "--debug",
                "--host",
                HOST,
                "--port",
                PORT,
            ],
            cwd=ROOT,
            env=env,
        )
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

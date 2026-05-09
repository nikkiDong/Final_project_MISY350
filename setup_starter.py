#!/usr/bin/env python3
"""Start the Streamlit app after setup has been completed."""

from __future__ import annotations

import subprocess
import os
from pathlib import Path

import setup_script


def has_streamlit(venv_python: Path) -> bool:
    result = subprocess.run(
        [str(venv_python), "-c", "import streamlit"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main() -> int:
    # Ensure we are running from the script's directory
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    venv_python = setup_script.get_venv_python_path()
    if not venv_python.exists():
        print("Setup is not complete: .venv was not found.")
        print("Run setup first:")
        print("- macOS/Linux: python3 setup_script.py")
        print("- Windows: python setup_script.py")
        return 1

    if not has_streamlit(venv_python):
        print("Streamlit is not installed in this project's .venv.")
        print("Run setup first:")
        print("- macOS/Linux: python3 setup_script.py")
        print("- Windows: python setup_script.py")
        return 1

    app_file = Path(__file__).resolve().parent / "app.py"
    if not app_file.exists():
        print(f"Could not find app file: {app_file}")
        return 1

    print("\nStarting Streamlit app...")
    print("Press Ctrl+C to stop.")
    subprocess.run([str(venv_python), "-m", "streamlit", "run", str(app_file)], check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\nFailed to start Streamlit (exit code {exc.returncode}).")
        raise SystemExit(exc.returncode)
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(0)

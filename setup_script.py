#!/usr/bin/env python3
"""Set up a local virtual environment and install dependencies."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS_FILE = ROOT / "requirements.txt"
VSCODE_SETTINGS_FILE = ROOT / ".vscode" / "settings.json"
DEFAULT_REQUIREMENTS = ["streamlit"]


def run_command(cmd: list[str], description: str) -> None:
    print(f"\n==> {description}")
    subprocess.run(cmd, check=True)


def get_venv_python_path() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_activation_hint() -> str:
    if os.name == "nt":
        return r".\.venv\Scripts\Activate.ps1"
    return "source .venv/bin/activate"


def get_direct_streamlit_command() -> str:
    if os.name == "nt":
        return r".\.venv\Scripts\streamlit.exe run app.py"
    return "./.venv/bin/streamlit run app.py"


def load_requirements_from_file(requirements_file: Path) -> list[str]:
    if not requirements_file.exists():
        return []

    try:
        lines = requirements_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    requirements: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def get_requirements_to_install() -> tuple[list[str], str]:
    file_requirements = load_requirements_from_file(REQUIREMENTS_FILE)
    if file_requirements:
        return file_requirements, f"{REQUIREMENTS_FILE.name}"
    return DEFAULT_REQUIREMENTS, "built-in defaults"


def configure_vscode_interpreter() -> None:
    VSCODE_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    settings: dict[str, object] = {}
    if VSCODE_SETTINGS_FILE.exists():
        try:
            settings = json.loads(VSCODE_SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("Could not parse existing VS Code settings. Recreating file.")

    settings["python.defaultInterpreterPath"] = str(get_venv_python_path())
    settings["python.terminal.activateEnvironment"] = True

    VSCODE_SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Updated local VS Code settings for .venv interpreter.")


def build_venv(clear_existing: bool) -> int:
    if clear_existing:
        print("Rebuilding incomplete virtual environment at .venv ...")
    else:
        print("Creating virtual environment at .venv ...")
    print("This may take 1-2 minutes on first run. Do not press Ctrl+C.")

    try:
        venv.EnvBuilder(with_pip=True, clear=clear_existing).create(VENV_DIR)
    except KeyboardInterrupt:
        print("\nSetup interrupted while creating .venv.")
        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR, ignore_errors=True)
            print("Removed partial .venv.")
        print("Do not activate .venv yet. Rerun this command to continue.")
        return 130
    return 0


def ensure_venv() -> int:
    venv_python = get_venv_python_path()

    if VENV_DIR.exists():
        if venv_python.exists():
            print("Virtual environment already exists at .venv. Reusing it.")
            return 0

        print("Detected incomplete .venv (often caused by an interrupted setup).")
        return build_venv(clear_existing=True)

    return build_venv(clear_existing=False)


def main() -> int:
    os.chdir(ROOT)

    venv_status = ensure_venv()
    if venv_status != 0:
        return venv_status

    venv_python = get_venv_python_path()
    if not venv_python.exists():
        print(f"Could not find virtual environment Python at: {venv_python}")
        return 1

    run_command(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        "Upgrading pip",
    )
    requirements, requirements_source = get_requirements_to_install()
    print(f"Dependency source: {requirements_source}")
    run_command(
        [str(venv_python), "-m", "pip", "install", *requirements],
        "Installing dependencies",
    )
    configure_vscode_interpreter()

    print("\nSetup complete.")
    print(f"Activate environment: {get_activation_hint()}")
    print("Then run: streamlit run app.py")
    print(f"Or run directly: {get_direct_streamlit_command()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\nA setup command failed (exit code {exc.returncode}).")
        raise SystemExit(exc.returncode)
    except KeyboardInterrupt:
        print("\nSetup interrupted.")
        raise SystemExit(130)

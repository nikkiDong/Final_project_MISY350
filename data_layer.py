"""
Data Layer — All JSON file read/write operations.

This module handles persistence: loading data from and saving data to JSON files.
No UI code (Streamlit) or business logic lives here.
"""

from __future__ import annotations

import json
from pathlib import Path


# ── File paths ───────────────────────────────────────────────────────────────
PATH_PATIENTS     = Path("patients.json")
PATH_DOCTORS      = Path("doctors.json")
PATH_APPOINTMENTS = Path("appointments.json")


# ── DataManager class ────────────────────────────────────────────────────────
class DataManager:
    """Centralised read / write access for every JSON data file."""

    # ── Generic helpers ──────────────────────────────────────────────────
    @staticmethod
    def load_json(path: Path, default):
        """Load a JSON file and return its contents, or *default* on failure."""
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, (list, dict)):
                    return data
            except (OSError, json.JSONDecodeError):
                pass
        else:
            # First run: create the file with the default value
            try:
                path.write_text(json.dumps(default, indent=2), encoding="utf-8")
            except OSError:
                pass
        return default

    @staticmethod
    def save_json(path: Path, data) -> tuple[bool, str]:
        """
        Write *data* to *path* as pretty-printed JSON.

        Returns (success: bool, message: str).
        Uses a simple direct-write instead of atomic rename so it works
        reliably on every deployment platform (including Streamlit Cloud).
        """
        try:
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True, "Saved."
        except OSError as exc:
            return False, f"Could not save {path.name}: {exc}"

    # ── Domain-specific loaders ──────────────────────────────────────────
    @staticmethod
    def load_patients() -> list[dict]:
        return DataManager.load_json(PATH_PATIENTS, [])

    @staticmethod
    def load_doctors() -> list[dict]:
        return DataManager.load_json(PATH_DOCTORS, [])

    @staticmethod
    def load_appointments() -> list[dict]:
        return DataManager.load_json(PATH_APPOINTMENTS, [])

    # ── Domain-specific savers ───────────────────────────────────────────
    @staticmethod
    def save_patients(data: list[dict]) -> tuple[bool, str]:
        return DataManager.save_json(PATH_PATIENTS, data)

    @staticmethod
    def save_doctors(data: list[dict]) -> tuple[bool, str]:
        return DataManager.save_json(PATH_DOCTORS, data)

    @staticmethod
    def save_appointments(data: list[dict]) -> tuple[bool, str]:
        return DataManager.save_json(PATH_APPOINTMENTS, data)

    @staticmethod
    def save_multiple(*pairs) -> tuple[bool, str]:
        """
        Save several (path, data) pairs.  If any write fails the earlier
        writes are *not* rolled back (we accept this trade-off for
        simplicity on Streamlit Cloud).
        """
        for path, data in pairs:
            ok, msg = DataManager.save_json(path, data)
            if not ok:
                return False, msg
        return True, "Saved."

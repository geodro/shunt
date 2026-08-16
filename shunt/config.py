"""Preferințe mici, separate de reguli (care sunt o listă, nu un dicționar)."""

from __future__ import annotations

import json
from pathlib import Path

from .rules import config_path as _rules_path

DEFAULTS = {"tray_icon": False, "notifications": True}


def path() -> Path:
    return _rules_path().with_name("config.json")


def load() -> dict:
    try:
        stored = json.loads(path().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        stored = {}
    return {**DEFAULTS, **stored} if isinstance(stored, dict) else dict(DEFAULTS)


def set_value(key: str, value) -> None:
    if key not in DEFAULTS:
        raise KeyError(f"preferință necunoscută: {key}")
    current = load()
    current[key] = value
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

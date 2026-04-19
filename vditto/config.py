"""Configuration management for VDitto."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "db_path": "",
    "save_dir": "",
}


def config_path() -> Path:
    """Resolve config.json path (same directory as executable or project root)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent.parent / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from file, falling back to defaults."""
    cfg = dict(_DEFAULTS)
    path = config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Failed to load config: {e}")
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """Save config to file."""
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    logging.info(f"Config saved to {path}")


def ensure_config(db_path: str = "") -> None:
    """Create config.json with defaults if missing. Optionally persist db_path."""
    path = config_path()
    cfg = dict(_DEFAULTS)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Failed to load config: {e}")

    needs_save = not path.exists()
    if db_path:
        cfg["db_path"] = db_path
        needs_save = True

    if needs_save:
        save_config(cfg)

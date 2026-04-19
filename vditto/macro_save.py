"""Macro-based auto-save to markdown for VDitto (F7).

Detects {{SAVE}} or {{SAVE:name}} macros in clipboard text
and saves the content as a .md file.
"""
from __future__ import annotations

import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from vditto.config import load_config

_MACRO_RE = re.compile(r"\{\{SAVE(?::([^}]+))?\}\}")

logger = logging.getLogger(__name__)


def detect_macro(text: str) -> tuple[str | None, str]:
    """Detect {{SAVE}} or {{SAVE:name}} macro in text.

    Returns:
        (filename_or_None, clean_text_with_macro_line_removed)
        - {{SAVE}} → (None, text)           → caller uses auto-timestamp
        - {{SAVE:notes}} → ("notes", text)   → caller uses "notes.md"
        - No macro → (None, original text)
    """
    match = _MACRO_RE.search(text)
    if not match:
        logger.debug("No SAVE macro detected in text")
        return None, text

    # Extract name from group(1), strip whitespace
    name = match.group(1)
    if name is not None:
        name = name.strip()
    logger.debug(f"Detected SAVE macro with name={name!r}")

    # Remove the entire line containing the macro
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _MACRO_RE.search(line):
            del lines[i]
            clean_text = "\n".join(lines)
            logger.debug(f"Removed macro line {i}, remaining {len(lines)} lines")
            return name, clean_text

    # Fallback (shouldn't reach here if match found)
    return name, text


def make_filename(name: str | None) -> str:
    """Generate .md filename.

    Args:
        name: Custom name (without .md extension), or None for auto-timestamp.

    Returns:
        Filename string ending with .md
    """
    if name is None:
        # Auto-generate timestamp: yyyymmdd-hhmmss
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.md"
        logger.debug(f"Generated auto-timestamp filename: {filename}")
        return filename

    # Custom name: ensure .md extension (don't double-add)
    if name.endswith(".md"):
        filename = name
    else:
        filename = f"{name}.md"
    logger.debug(f"Generated custom filename: {filename}")
    return filename


def save_markdown(text: str, name: str | None, save_dir: Path) -> Path:
    """Save text as a markdown file.

    Creates save_dir if it doesn't exist.

    Args:
        text: Clean text content (macro already removed).
        name: Custom filename or None for auto-timestamp.
        save_dir: Target directory path.

    Returns:
        Full path to the saved file.
    """
    # Create directory if it doesn't exist
    save_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured save_dir exists: {save_dir}")

    # Generate filename
    filename = make_filename(name)
    filepath = save_dir / filename

    # Write content (overwrite if exists)
    filepath.write_text(text, encoding="utf-8")
    logger.info(f"Saved markdown to {filepath}")

    return filepath


def default_save_dir() -> Path:
    """Return default save directory (exe-adjacent /notes/)."""
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        base_dir = Path(sys.executable).parent
    else:
        # Running from source: project root
        base_dir = Path(__file__).parent.parent

    notes_dir = base_dir / "notes"
    logger.debug(f"Default save dir: {notes_dir}")
    return notes_dir


def resolve_save_dir() -> Path:
    """Resolve save directory from config, falling back to default."""
    config = load_config()
    configured_path = config.get("save_dir", "")

    if configured_path:
        save_dir = Path(configured_path)
        logger.info(f"Using configured save_dir: {save_dir}")
        return save_dir

    # Fallback to default
    default_dir = default_save_dir()
    logger.debug(f"No save_dir in config, using default: {default_dir}")
    return default_dir

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

_MACRO_RE = re.compile(r"\{\{SAVE(?::([^|}]+))?(?:\|M:([AOC]))?\}\}")
CHUNK_THRESHOLD = 20000

logger = logging.getLogger(__name__)


def detect_macro(text: str) -> tuple[str, str | None, str]:
    """Detect {{SAVE}} or {{SAVE:name}} macro in text.

    Returns:
        (mode, filename_or_None, clean_text_with_macro_line_removed)
        - mode: 'O' (overwrite), 'A' (append), 'C' (collection)
        - {{SAVE}} → ("A", None, text)           → caller uses auto-timestamp
        - {{SAVE:notes}} → ("A", "notes", text)   → caller uses "notes.md"
        - {{SAVE:notes|M:A}} → ("A", "notes", text) → append mode
        - No macro → ("O", None, original text)
    """
    match = _MACRO_RE.search(text)
    if not match:
        logger.debug("No SAVE macro detected in text")
        return "O", None, text

    # Extract mode from group(2), default to 'A' (append)
    mode = match.group(2) or "A"

    # Extract name from group(1), strip whitespace
    name = match.group(1)
    if name is not None:
        name = name.strip()
        if name == "":
            name = None
    logger.debug(f"Detected SAVE macro with mode={mode!r}, name={name!r}")

    # Remove the entire line containing the macro
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _MACRO_RE.search(line):
            del lines[i]
            clean_text = "\n".join(lines)
            logger.debug(f"Removed macro line {i}, remaining {len(lines)} lines")
            return mode, name, clean_text

    # Fallback (shouldn't reach here if match found)
    return mode, name, text


def split_text(text: str, max_len: int = CHUNK_THRESHOLD - 50) -> list[str]:
    """Split text into chunks at newline boundaries, each <= max_len.

    Default chunk size is CHUNK_THRESHOLD - 50, leaving room for the macro
    prefix so the total clipboard text stays under CHUNK_THRESHOLD.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        # Find last newline within max_len
        cut = remaining.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        else:
            cut += 1  # include newline in first chunk
        chunks.append(remaining[:cut])
        remaining = remaining[cut:]

    return chunks


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


def save_markdown(text: str, name: str | None, save_dir: Path, mode: str = "A") -> Path:
    """Save text as a markdown file.

    Creates save_dir if it doesn't exist.

    Args:
        text: Clean text content (macro already removed).
        name: Custom filename or None for auto-timestamp.
        save_dir: Target directory path.
        mode: File handling mode - 'O' (overwrite), 'A' (append), 'C' (collection).

    Returns:
        Full path to the saved file.
    """
    if mode == "O":
        # Overwrite mode (original behavior)
        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured save_dir exists: {save_dir}")

        filename = make_filename(name)
        filepath = save_dir / filename

        filepath.write_text(text, encoding="utf-8")
        logger.info(f"Saved markdown (overwrite) to {filepath}")
        return filepath

    elif mode == "A":
        # Append mode
        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured save_dir exists: {save_dir}")

        filename = make_filename(name)
        filepath = save_dir / filename

        if filepath.exists():
            # Append with separator
            old_content = filepath.read_text(encoding="utf-8")
            new_content = f"{old_content}\n---\n{text}"
            filepath.write_text(new_content, encoding="utf-8")
            logger.info(f"Appended markdown to {filepath}")
        else:
            # Create new file
            filepath.write_text(text, encoding="utf-8")
            logger.info(f"Created new markdown file (append mode) at {filepath}")
        return filepath

    elif mode == "C":
        # Collection mode: create subdirectory with timestamped files
        collection_name = name or "unnamed"
        collection_dir = save_dir / collection_name
        collection_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured collection dir exists: {collection_dir}")

        # Always use timestamp filename in collection mode
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.md"
        filepath = collection_dir / filename

        filepath.write_text(text, encoding="utf-8")
        logger.info(f"Saved markdown (collection) to {filepath}")
        return filepath

    else:
        # Fallback to overwrite mode for invalid mode
        logger.warning(f"Invalid mode {mode!r}, falling back to overwrite")
        return save_markdown(text, name, save_dir, mode="O")


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

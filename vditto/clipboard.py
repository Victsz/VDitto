"""
Clipboard data handling for VDitto (F1).
Handles format detection, preview text generation, and self-paste prevention.
"""
from __future__ import annotations

import zlib
from typing import Literal


CLIPBOARD_IGNORE_FORMAT = "Clipboard Viewer Ignore"
MTEXT_MAX_LEN = 150


def make_preview_text(text: str, max_len: int = MTEXT_MAX_LEN) -> str:
    """Create mText preview by truncating to max_len characters.
    Replaces newlines with \\n for single-line display.
    """
    # Replace all newlines and tabs with spaces for single-line display
    result = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # Truncate to max_len
    return result[:max_len]


def compute_clip_crc(data: bytes) -> int:
    """Compute CRC32 for clip data deduplication.
    Returns unsigned 32-bit CRC.
    """
    return zlib.crc32(data) & 0xFFFFFFFF


def classify_clip_type(
    has_text: bool, has_image: bool
) -> Literal["text", "image", "other"]:
    """Classify clipboard content type from available format flags."""
    if has_text:
        return "text"
    if has_image:
        return "image"
    return "other"

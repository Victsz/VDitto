"""
Text transformation functions for VDitto paste operations (F5).
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime


def to_plain(text: str) -> str:
    """Strip formatting: remove non-printable control chars, normalize whitespace."""
    # Remove non-printable control characters (0x00-0x1F except tab, newline, carriage return)
    # First replace tabs and newlines with spaces
    text = text.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    # Remove control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize whitespace: collapse multiple spaces into one, trim
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def to_upper(text: str) -> str:
    """Convert to UPPER CASE."""
    return text.upper()


def to_lower(text: str) -> str:
    """Convert to lower case."""
    return text.lower()


def to_capitalize(text: str) -> str:
    """Capitalize first letter of each word."""
    return text.title()


def to_sentence(text: str) -> str:
    """Sentence case: capitalize first letter after sentence-ending punctuation."""
    # Capitalize first character
    if not text:
        return text

    result = []
    capitalize_next = True

    for char in text:
        if capitalize_next and char.isalpha():
            result.append(char.upper())
            capitalize_next = False
        else:
            result.append(char.lower() if char.isalpha() else char)

        # Check if this character ends a sentence
        if char in ".!?":
            capitalize_next = True

    return "".join(result)


def to_invert_case(text: str) -> str:
    """Invert case of each character."""
    return text.swapcase()


def trim_whitespace(text: str) -> str:
    """Trim leading/trailing whitespace and collapse internal runs."""
    # Collapse all whitespace runs into single spaces
    text = re.sub(r"\s+", " ", text)
    # Trim leading/trailing
    return text.strip()


def remove_newlines(text: str) -> str:
    """Replace all newline sequences with a single space."""
    # Replace all newline variations with space
    text = re.sub(r"[\r\n]+", " ", text)
    # Collapse multiple spaces that may result
    text = re.sub(r" +", " ", text)
    return text


def generate_guid() -> str:
    """Generate a new GUID string."""
    return str(uuid.uuid4())


def current_datetime() -> str:
    """Return current datetime as yyyymmdd-HH:MM:SS."""
    return datetime.now().strftime("%Y%m%d-%H:%M:%S")

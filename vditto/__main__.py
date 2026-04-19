"""VDitto entry point. Run with: python -m vditto [--db PATH]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vditto.app import run


def main() -> None:
    parser = argparse.ArgumentParser(description="VDitto - Lightweight Ditto clipboard manager")
    parser.add_argument("--db", type=Path, default=None, help="Path to Ditto database file")
    args = parser.parse_args()

    sys.exit(run(args.db))


if __name__ == "__main__":
    main()

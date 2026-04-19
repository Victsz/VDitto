"""
DIB image conversion for VDitto (F1 image support).
Handles CF_DIB data from Ditto DB.
"""
from __future__ import annotations

import io
import logging
import struct

logger = logging.getLogger(__name__)


def _validate_dib_header(dib_data: bytes) -> None:
    """Validate DIB header integrity.

    Args:
        dib_data: Raw DIB bytes (BITMAPINFOHEADER + pixel data)

    Raises:
        ValueError: If data is too short or header size is invalid
    """
    if len(dib_data) < 40:
        raise ValueError(f"DIB data too short: {len(dib_data)} bytes, expected at least 40 bytes for BITMAPINFOHEADER")

    biSize = struct.unpack_from("<I", dib_data, 0)[0]
    if biSize != 40:
        raise ValueError(f"Invalid BITMAPINFOHEADER size: {biSize}, expected 40")


def dib_dimensions(dib_data: bytes) -> tuple[int, int]:
    """Read width and height from DIB header. Returns (width, height).

    Args:
        dib_data: Raw DIB bytes (BITMAPINFOHEADER + pixel data)

    Returns:
        Tuple of (width, height) in pixels

    Raises:
        ValueError: If data is too short or header is invalid
    """
    _validate_dib_header(dib_data)

    biWidth, biHeight = struct.unpack_from("<ii", dib_data, 4)
    logger.debug(f"DIB dimensions: {biWidth}x{biHeight}")

    return (biWidth, biHeight)


def dib_to_png(dib_data: bytes) -> bytes:
    """Convert DIB (BITMAPINFOHEADER + pixels) to PNG bytes.

    Args:
        dib_data: Raw DIB bytes (BITMAPINFOHEADER + pixel data)

    Returns:
        PNG image as bytes

    Raises:
        ValueError: If data is too short or header is invalid
        Exception: If Pillow cannot process the image
    """
    _validate_dib_header(dib_data)

    # Parse BITMAPINFOHEADER for logging
    biSize, biWidth, biHeight, biPlanes, biBitCount = struct.unpack_from("<iiiHH", dib_data, 0)
    biCompression = struct.unpack_from("<I", dib_data, 16)[0]
    logger.debug(f"DIB header: {biWidth}x{biHeight}, {biBitCount}bit, compression={biCompression}")

    # DIB lacks BMP file header, need to construct one
    # BMP = BM header (14 bytes) + DIB data
    bmp_header_size = 14
    dib_offset = bmp_header_size

    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",
        dib_offset + len(dib_data),  # file size
        0,  # reserved1
        0,  # reserved2
        dib_offset,  # pixel data offset
    )

    bmp_data = bmp_header + dib_data

    # Use Pillow to convert BMP to PNG
    from PIL import Image

    img = Image.open(io.BytesIO(bmp_data))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    logger.info(f"DIB to PNG conversion: {biWidth}x{biHeight} → {len(png_bytes)} bytes")

    return png_bytes

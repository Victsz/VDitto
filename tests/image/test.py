"""
DIB image conversion test suite.
Run: python tests/image/test.py

Zero external dependencies - uses only stdlib unittest + struct + Pillow.
"""
import __future__

import io
import struct
import unittest
from pathlib import Path

from vditto.image import dib_to_png, dib_dimensions


def make_dib(width: int, height: int, bit_count: int) -> bytes:
    """Construct a minimal valid DIB (BITMAPINFOHEADER + pixel data)."""
    # BITMAPINFOHEADER: 40 bytes
    row_size = ((width * bit_count + 31) // 32) * 4  # 4-byte aligned
    pixel_size = row_size * height
    header = struct.pack(
        "<IiiHHIIiiII",
        40,           # biSize
        width,        # biWidth
        height,       # biHeight (positive = bottom-up)
        1,            # biPlanes
        bit_count,    # biBitCount
        0,            # biCompression (BI_RGB)
        pixel_size,   # biSizeImage
        0,            # biXPelsPerMeter
        0,            # biYPelsPerMeter
        0,            # biClrUsed
        0,            # biClrImportant
    )
    pixels = b"\xFF" * pixel_size  # all-white pixels
    return header + pixels


# --- Pre-built fixtures ---
DIB_2x2_24 = make_dib(2, 2, 24)
DIB_2x2_32 = make_dib(2, 2, 32)
DIB_1x1_24 = make_dib(1, 1, 24)
DIB_INVALID_SHORT = b"\x00" * 10
DIB_INVALID_HEADERSIZE = struct.pack(
    "<IiiHHIIiiII",
    99,   # wrong biSize
    2, 2, 1, 24, 0, 0, 0, 0, 0, 0,
) + b"\x00" * 16


class TestImage(unittest.TestCase):
    """Test DIB image conversion functions."""

    # ---- dib_to_png ----

    def test_dib_to_png_24bit(self):
        png = dib_to_png(DIB_2x2_24)
        self.assertTrue(png[:4] == b"\x89PNG", "Output should start with PNG magic")

        from PIL import Image
        img = Image.open(io.BytesIO(png))
        self.assertEqual(img.size, (2, 2))

    def test_dib_to_png_32bit(self):
        png = dib_to_png(DIB_2x2_32)
        self.assertTrue(png[:4] == b"\x89PNG")

        from PIL import Image
        img = Image.open(io.BytesIO(png))
        self.assertEqual(img.size, (2, 2))

    def test_dib_to_png_1x1(self):
        png = dib_to_png(DIB_1x1_24)
        self.assertTrue(png[:4] == b"\x89PNG")

        from PIL import Image
        img = Image.open(io.BytesIO(png))
        self.assertEqual(img.size, (1, 1))

    def test_dib_to_png_invalid_short(self):
        with self.assertRaises(Exception):
            dib_to_png(DIB_INVALID_SHORT)

    def test_dib_to_png_invalid_header_size(self):
        with self.assertRaises(Exception):
            dib_to_png(DIB_INVALID_HEADERSIZE)

    # ---- dib_dimensions ----

    def test_dib_dimensions_normal(self):
        w, h = dib_dimensions(DIB_2x2_24)
        self.assertEqual(w, 2)
        self.assertEqual(h, 2)

    def test_dib_dimensions_1x1(self):
        w, h = dib_dimensions(DIB_1x1_24)
        self.assertEqual(w, 1)
        self.assertEqual(h, 1)

    def test_dib_dimensions_too_short(self):
        with self.assertRaises(Exception):
            dib_dimensions(DIB_INVALID_SHORT)

    # ---- roundtrip integrity ----

    def test_dib_roundtrip_integrity(self):
        w_dib, h_dib = dib_dimensions(DIB_2x2_24)
        png = dib_to_png(DIB_2x2_24)

        from PIL import Image
        img = Image.open(io.BytesIO(png))
        self.assertEqual(img.size[0], w_dib)
        self.assertEqual(img.size[1], h_dib)


if __name__ == "__main__":
    unittest.main(verbosity=2)

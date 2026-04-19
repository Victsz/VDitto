"""
Clipboard data handling test suite.
Run: python tests/clipboard/test.py
"""
import __future__

import unittest

from vditto.clipboard import make_preview_text, compute_clip_crc, classify_clip_type


class TestMakePreviewText(unittest.TestCase):

    def test_short_text_unchanged(self):
        self.assertEqual(make_preview_text("hello"), "hello")

    def test_truncation_at_max_len(self):
        text = "a" * 200
        result = make_preview_text(text, max_len=50)
        self.assertEqual(len(result), 50)

    def test_newlines_replaced(self):
        result = make_preview_text("line1\nline2\r\nline3")
        self.assertNotIn("\n", result)
        self.assertNotIn("\r", result)

    def test_default_max_len_150(self):
        text = "x" * 300
        result = make_preview_text(text)
        self.assertEqual(len(result), 150)

    def test_empty_string(self):
        self.assertEqual(make_preview_text(""), "")

    def test_exact_max_len_not_truncated(self):
        text = "a" * 150
        result = make_preview_text(text)
        self.assertEqual(len(result), 150)

    def test_tabs_replaced(self):
        result = make_preview_text("hello\tworld")
        self.assertNotIn("\t", result)


class TestComputeClipCrc(unittest.TestCase):

    def test_same_data_same_crc(self):
        data = b"test data"
        self.assertEqual(compute_clip_crc(data), compute_clip_crc(data))

    def test_different_data_different_crc(self):
        self.assertNotEqual(compute_clip_crc(b"aaa"), compute_clip_crc(b"bbb"))

    def test_returns_unsigned_int(self):
        crc = compute_clip_crc(b"test")
        self.assertGreaterEqual(crc, 0)
        self.assertIsInstance(crc, int)

    def test_empty_data(self):
        crc = compute_clip_crc(b"")
        self.assertIsInstance(crc, int)


class TestClassifyClipType(unittest.TestCase):

    def test_text_only(self):
        self.assertEqual(classify_clip_type(has_text=True, has_image=False), "text")

    def test_image_only(self):
        self.assertEqual(classify_clip_type(has_text=False, has_image=True), "image")

    def test_both_prefers_text(self):
        """If both text and image, prefer text (more common case)."""
        self.assertEqual(classify_clip_type(has_text=True, has_image=True), "text")

    def test_neither(self):
        self.assertEqual(classify_clip_type(has_text=False, has_image=False), "other")


if __name__ == "__main__":
    unittest.main(verbosity=2)

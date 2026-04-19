"""
Text transformation test suite.
Run: python tests/transform/test.py

Zero external dependencies - uses only stdlib unittest.
"""
import __future__

import json
import re
import unittest
from pathlib import Path

from vditto.transform import (
    to_plain,
    to_upper,
    to_lower,
    to_capitalize,
    to_sentence,
    to_invert_case,
    trim_whitespace,
    remove_newlines,
    generate_guid,
    current_datetime,
)


class TestTransform(unittest.TestCase):
    """Test all text transform functions."""

    # ---- to_plain ----

    def test_to_plain_normal(self):
        self.assertEqual(to_plain("  hello   world  \x00\x01  "), "hello world")

    def test_to_plain_tabs_and_newlines(self):
        self.assertEqual(to_plain("line1\t\tline2\n\nline3"), "line1 line2 line3")

    def test_to_plain_empty(self):
        self.assertEqual(to_plain(""), "")

    # ---- to_upper ----

    def test_to_upper_normal(self):
        self.assertEqual(to_upper("Hello World"), "HELLO WORLD")

    def test_to_upper_unicode(self):
        self.assertEqual(to_upper("café résumé"), "CAFÉ RÉSUMÉ")

    def test_to_upper_already_upper(self):
        self.assertEqual(to_upper("ALREADY"), "ALREADY")

    # ---- to_lower ----

    def test_to_lower_normal(self):
        self.assertEqual(to_lower("Hello WORLD"), "hello world")

    def test_to_lower_unicode(self):
        self.assertEqual(to_lower("CAFÉ"), "café")

    # ---- to_capitalize ----

    def test_to_capitalize_normal(self):
        self.assertEqual(to_capitalize("hello world"), "Hello World")

    def test_to_capitalize_mixed(self):
        self.assertEqual(to_capitalize("hELLO wORLD"), "Hello World")

    # ---- to_sentence ----

    def test_to_sentence_normal(self):
        self.assertEqual(to_sentence("hello. world! yes? no"), "Hello. World! Yes? No")

    def test_to_sentence_single(self):
        self.assertEqual(to_sentence("hello world"), "Hello world")

    # ---- to_invert_case ----

    def test_to_invert_case_normal(self):
        self.assertEqual(to_invert_case("Hello World"), "hELLO wORLD")

    def test_to_invert_case_mixed(self):
        self.assertEqual(to_invert_case("ABC 123 xyz!"), "abc 123 XYZ!")

    # ---- trim_whitespace ----

    def test_trim_whitespace_normal(self):
        self.assertEqual(trim_whitespace("  hello   world  "), "hello world")

    def test_trim_whitespace_newlines(self):
        self.assertEqual(trim_whitespace("\n\n  hello \n world \t \n"), "hello world")

    # ---- remove_newlines ----

    def test_remove_newlines_normal(self):
        self.assertEqual(remove_newlines("line1\nline2\r\nline3\rline4"), "line1 line2 line3 line4")

    def test_remove_newlines_consecutive(self):
        self.assertEqual(remove_newlines("a\n\n\nb"), "a b")

    # ---- generate_guid ----

    def test_generate_guid_format(self):
        guid = generate_guid()
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        self.assertRegex(guid, pattern)

    def test_generate_guid_unique(self):
        g1 = generate_guid()
        g2 = generate_guid()
        self.assertNotEqual(g1, g2)

    # ---- current_datetime ----

    def test_current_datetime_format(self):
        dt = current_datetime()
        pattern = r"^\d{8}-\d{2}:\d{2}:\d{2}$"
        self.assertRegex(dt, pattern)


if __name__ == "__main__":
    unittest.main(verbosity=2)

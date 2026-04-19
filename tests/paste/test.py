"""
Paste simulation test suite.
Run: python tests/paste/test.py
"""
import __future__

import struct
import sys
import unittest


class TestPaste(unittest.TestCase):
    """Test paste simulation structures and logic."""

    def test_sendinput_input_struct_size_64bit(self):
        """INPUT struct must be 40 bytes on 64-bit (MOUSEINPUT is largest union member)."""
        from vditto.paste import _build_sendinput_structs

        if sys.platform != "win32":
            self.skipTest("SendInput only on Windows")

        inputs = _build_sendinput_structs()
        import ctypes
        for inp in inputs:
            self.assertEqual(ctypes.sizeof(inp), 40,
                f"INPUT struct must be 40 bytes, got {ctypes.sizeof(inp)}")

    def test_sendinput_build_returns_four_inputs(self):
        """_build_sendinput_structs should return 4 INPUT structs (Ctrl↓ V↓ V↑ Ctrl↑)."""
        if sys.platform != "win32":
            self.skipTest("SendInput only on Windows")

        from vditto.paste import _build_sendinput_structs
        inputs = _build_sendinput_structs()
        self.assertEqual(len(inputs), 4)

    def test_send_input_paste_returns_int(self):
        """_send_input_paste returns int (0 on non-Windows)."""
        from vditto.paste import _send_input_paste
        result = _send_input_paste()
        self.assertIsInstance(result, int)

    def test_send_input_paste_zero_on_linux(self):
        """On non-Windows, _send_input_paste should return 0."""
        if sys.platform == "win32":
            self.skipTest("Only for non-Windows")

        from vditto.paste import _send_input_paste
        self.assertEqual(_send_input_paste(), 0)

    def test_sendkeys_paste_returns_bool(self):
        """_sendkeys_paste returns bool."""
        from vditto.paste import _sendkeys_paste
        result = _sendkeys_paste()
        self.assertIsInstance(result, bool)

    def test_send_ctrl_v_returns_bool(self):
        """send_ctrl_v returns bool indicating success."""
        from vditto.paste import send_ctrl_v
        result = send_ctrl_v()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)

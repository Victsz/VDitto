"""
Paste simulation for VDitto (F3).
ctypes SendInput (primary) + PowerShell SendKeys (fallback).
"""
from __future__ import annotations

import logging
import sys
import subprocess


def send_ctrl_v() -> bool:
    """Send Ctrl+V keystroke to foreground window.
    Primary: ctypes SendInput. Fallback: PowerShell SendKeys.
    Returns True if paste was sent successfully.
    """
    if sys.platform != "win32":
        return False

    try:
        sent_count = _send_input_paste()
        if sent_count > 0:
            return True
        logging.debug(f"SendInput returned {sent_count}, trying SendKeys fallback")
    except Exception:
        logging.exception("SendInput failed, trying SendKeys fallback")

    return _sendkeys_paste()


def _build_sendinput_structs() -> tuple:
    """Build INPUT structures for Ctrl+V sequence.
    Returns (ctrl_down, v_down, v_up, ctrl_up) tuple of INPUT structs.
    Only available on Windows.
    """
    import ctypes
    import ctypes.wintypes

    # Constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_V = 0x56

    # 64-bit Windows: ULONG_PTR is 64-bit (c_uint64)
    # This is critical for INPUT struct to be 40 bytes
    ULONG_PTR = ctypes.c_uint64

    # Define INPUT structures matching Windows API
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.wintypes.DWORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.wintypes.WORD),
            ("wScan", ctypes.wintypes.WORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", ctypes.wintypes.DWORD),
            ("wParamL", ctypes.wintypes.WORD),
            ("wParamH", ctypes.wintypes.WORD),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.wintypes.DWORD),
            ("union", INPUT_UNION),
        ]

    # Build the 4 INPUT structs for Ctrl+V sequence
    ctrl_down = INPUT()
    ctrl_down.type = INPUT_KEYBOARD
    ctrl_down.union.ki.wVk = VK_CONTROL
    ctrl_down.union.ki.dwFlags = 0
    ctrl_down.union.ki.dwExtraInfo = 0

    v_down = INPUT()
    v_down.type = INPUT_KEYBOARD
    v_down.union.ki.wVk = VK_V
    v_down.union.ki.dwFlags = 0
    v_down.union.ki.dwExtraInfo = 0

    v_up = INPUT()
    v_up.type = INPUT_KEYBOARD
    v_up.union.ki.wVk = VK_V
    v_up.union.ki.dwFlags = KEYEVENTF_KEYUP
    v_up.union.ki.dwExtraInfo = 0

    ctrl_up = INPUT()
    ctrl_up.type = INPUT_KEYBOARD
    ctrl_up.union.ki.wVk = VK_CONTROL
    ctrl_up.union.ki.dwFlags = KEYEVENTF_KEYUP
    ctrl_up.union.ki.dwExtraInfo = 0

    return (ctrl_down, v_down, v_up, ctrl_up)


def _send_input_paste() -> int:
    """Send Ctrl+V via ctypes SendInput.
    Returns number of successfully sent events (0 = failure).
    """
    if sys.platform != "win32":
        return 0

    import ctypes
    import ctypes.wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_V = 0x56
    ULONG_PTR = ctypes.c_uint64

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.wintypes.DWORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.wintypes.WORD),
            ("wScan", ctypes.wintypes.WORD),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", ctypes.wintypes.DWORD),
            ("wParamL", ctypes.wintypes.WORD),
            ("wParamH", ctypes.wintypes.WORD),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.wintypes.DWORD),
            ("union", INPUT_UNION),
        ]

    # Create contiguous array of 4 INPUT structs (zero-initialized)
    inputs = (INPUT * 4)()

    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki.wVk = VK_CONTROL

    inputs[1].type = INPUT_KEYBOARD
    inputs[1].union.ki.wVk = VK_V

    inputs[2].type = INPUT_KEYBOARD
    inputs[2].union.ki.wVk = VK_V
    inputs[2].union.ki.dwFlags = KEYEVENTF_KEYUP

    inputs[3].type = INPUT_KEYBOARD
    inputs[3].union.ki.wVk = VK_CONTROL
    inputs[3].union.ki.dwFlags = KEYEVENTF_KEYUP

    user32 = ctypes.windll.user32
    sent = user32.SendInput(4, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    return sent


def _sendkeys_paste() -> bool:
    """Send Ctrl+V via PowerShell SendKeys (fallback).
    Returns True if PowerShell exited successfully.
    """
    if sys.platform != "win32":
        return False

    result = subprocess.run(
        ["powershell", "-Command", "[System.Windows.Forms.SendKeys]::SendWait('^v')"],
        capture_output=True,
        timeout=5,
    )
    return result.returncode == 0

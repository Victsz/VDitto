"""
T3: 验证 ctypes SendInput 能模拟 Ctrl+V
运行: python tests/feasi/test_sendinput.py
操作: 先复制文字到剪贴板，打开记事本，切换到记事本后按 Enter
"""
import sys
import time

if sys.platform != "win32":
    print("[SKIP] SendInput only works on Windows")
    sys.exit(0)

import ctypes
import ctypes.wintypes

# 常量
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_CONTROL = 0x11
VK_V = 0x56

# Windows API
user32 = ctypes.windll.user32

# 正确的 64-bit 结构体定义
# dwExtraInfo 在 Win64 是 ULONG_PTR = 8 bytes
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


def send_key(vk, flags=0):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    return result


def paste():
    r1 = send_key(VK_CONTROL, 0)
    time.sleep(0.05)
    r2 = send_key(VK_V, 0)
    time.sleep(0.05)
    r3 = send_key(VK_V, KEYEVENTF_KEYUP)
    time.sleep(0.05)
    r4 = send_key(VK_CONTROL, KEYEVENTF_KEYUP)
    print(f"  SendInput results: Ctrl↓={r1} V↓={r2} V↑={r3} Ctrl↑={r4}")
    print(f"  INPUT struct size: {ctypes.sizeof(INPUT)} bytes")


def set_clipboard_text(text):
    """通过 PowerShell 设置剪贴板内容"""
    import subprocess
    # 用 Base64 编码避免转义问题
    import base64
    encoded = base64.b64encode(text.encode('utf-16-le')).decode('ascii')
    ps_script = (
        f'$bytes = [Convert]::FromBase64String("{encoded}"); '
        f'$text = [System.Text.Encoding]::Unicode.GetString($bytes); '
        f'[Windows.Forms.Clipboard]::SetText($text)'
    )
    subprocess.run([
        'powershell', '-Command',
        'Add-Type -AssemblyName System.Windows.Forms; ' + ps_script
    ], capture_output=True)


def sendkeys_paste():
    """通过 PowerShell SendKeys 模拟 Ctrl+V"""
    import subprocess
    subprocess.run([
        'powershell', '-Command',
        'Add-Type -AssemblyName System.Windows.Forms; '
        '[System.Windows.Forms.SendKeys]::SendWait("^v")'
    ], capture_output=True)


def main():
    print("=== SendInput Ctrl+V test ===")
    print("Will test 2 methods with different clipboard content.")
    print("Open Notepad and keep it visible.")
    print()
    input("Press Enter when ready...")

    # ---- Method 1: SendInput ----
    print("\n--- Test 1: ctypes SendInput ---")
    set_clipboard_text("[A] SendInput works!")
    print("[INFO] Clipboard set to '[A] SendInput works!'")
    print("[INFO] Switching to Notepad in 3s...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print("[INFO] Pasting via SendInput...")
    paste()
    time.sleep(1)

    # ---- Method 2: PowerShell SendKeys ----
    print("\n--- Test 2: PowerShell SendKeys ---")
    set_clipboard_text("[B] SendKeys works!")
    print("[INFO] Clipboard set to '[B] SendKeys works!'")
    print("[INFO] Pasting via PowerShell SendKeys in 2s...")
    time.sleep(2)

    print("[INFO] Pasting via SendKeys...")
    sendkeys_paste()
    time.sleep(1)

    # ---- Result ----
    print()
    print("=== RESULT ===")
    print("Check Notepad content:")
    print("  Only [A] -> SendInput works, SendKeys failed")
    print("  Only [B] -> SendKeys works, SendInput failed")
    print("  Both [A]+[B] -> Both methods work!")
    print("  Nothing -> Neither worked (check focus?)")


if __name__ == "__main__":
    main()

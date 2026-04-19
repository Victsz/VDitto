"""
T4: 验证 pynput 能注册全局热键 Ctrl+`
运行: python tests/feasi/test_hotkey.py
操作: 在任意窗口按 Ctrl+` 观察是否打印事件
按 Ctrl+Shift+Q 退出
"""
import sys

from pynput import keyboard


def main():
    print("=== Global Hotkey test ===")
    print("Press Ctrl+` (backtick) to test...")
    print("Press Ctrl+Shift+Q to exit\n")

    triggered = [False]

    def on_activate():
        triggered[0] = True
        print(f"[OK] Ctrl+` triggered! (count: {triggered[0]})")

    def on_quit():
        print("\n[OK] Quit hotkey received, exiting...")
        return False  # stop listener

    with keyboard.GlobalHotKeys({
        '<ctrl>+`': on_activate,
        '<ctrl>+<shift>+q': on_quit,
    }) as h:
        h.join()

    print(f"\n=== T4 Hotkey: triggered={triggered[0]} ===")


if __name__ == "__main__":
    main()

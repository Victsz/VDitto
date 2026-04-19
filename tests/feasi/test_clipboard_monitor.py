"""
T2: 验证 QClipboard.dataChanged 能否监听到剪贴板变化
运行: python tests/feasi/test_clipboard_monitor.py
操作: 复制一些文字或图片，观察是否打印变化事件
按 Ctrl+C 退出
"""
import sys
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    clipboard = app.clipboard()

    counter = [0]

    def on_changed():
        counter[0] += 1
        mime = clipboard.mimeData()
        has_text = mime.hasText()
        has_image = mime.hasImage()
        text_preview = ""
        if has_text:
            text_preview = clipboard.text()[:80].replace("\n", "\\n")

        content_type = "text" if has_text else ("image" if has_image else "other")
        print(f"[{counter[0]}] type={content_type} text_preview='{text_preview}'")

    clipboard.dataChanged.connect(on_changed)

    print("=== Clipboard monitor started ===")
    print("Copy some text or image from any app...")
    print("Press Ctrl+C to exit\n")

    # 保持事件循环
    timer = app.startTimer(100)
    app.exec()


if __name__ == "__main__":
    main()

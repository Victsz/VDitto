"""Clipboard monitor for VDitto (F1). Watches QClipboard.dataChanged signal."""
from __future__ import annotations

import logging
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QBuffer, QIODevice

from vditto.clipboard import (
    classify_clip_type,
    CLIPBOARD_IGNORE_FORMAT,
    make_preview_text,
    compute_clip_crc,
)


def start_clipboard_monitor(app: QApplication, on_clip_callback: callable) -> QClipboard:
    """Start monitoring clipboard for changes.

    Args:
        app: QApplication instance
        on_clip_callback: Callback function receiving (clip_type, data, preview)

    Returns:
        QClipboard object that was set up
    """
    clipboard = app.clipboard()

    def on_changed():
        mime = clipboard.mimeData()
        # Skip self-paste by checking for ignore format
        if CLIPBOARD_IGNORE_FORMAT in mime.formats():
            return

        clip_type = classify_clip_type(mime.hasText(), mime.hasImage())
        logging.debug(f"Clip detected: type={clip_type}")

        if clip_type == "text":
            text = clipboard.text()
            if len(text) > 100:
                logging.debug(f"Clip text len={len(text)}, first100={text[:100]!r}")
            # Ditto stores CF_UNICODETEXT as UTF-16LE (wchar_t)
            on_clip_callback("text", text.encode("utf-16-le"), text)

        elif clip_type == "image":
            image = clipboard.image()
            if not image.isNull():
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buf, "BMP")  # saves as BMP (14-byte header + DIB)
                bmp_data = buf.data().data()  # QByteArray → bytes
                dib_data = bmp_data[14:]  # strip 14-byte BMP file header
                buf.close()
                on_clip_callback("image", dib_data, "[image]")

        # "other" type is skipped

    clipboard.dataChanged.connect(on_changed)
    logging.info("Clipboard monitor started")
    return clipboard


def stop_clipboard_monitor(clipboard: QClipboard) -> None:
    """Stop monitoring clipboard.

    Args:
        clipboard: QClipboard object to disconnect from
    """
    clipboard.dataChanged.disconnect()
    logging.info("Clipboard monitor stopped")

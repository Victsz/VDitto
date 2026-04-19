"""Main window for VDitto. PySide6 QMainWindow with clip list, search, and paste actions."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QMimeData, QEvent
from PySide6.QtGui import QCursor, QKeyEvent, QImage
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vditto import config, db, paste
from vditto.clipboard import make_preview_text, CLIPBOARD_IGNORE_FORMAT


class ClipWindow(QMainWindow):
    """Main window for VDitto clipboard manager."""

    def __init__(self, db_path: Path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.conn = db.open_db(db_path)
        self._clips: list[dict] = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._on_search_debounced)
        self._current_keyword = ""
        self._search_mode = "like"
        self._drag_pos = None

        self.setWindowTitle("VDitto")
        self.setFixedSize(600, 400)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Search bar row with menu button
        search_row = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self._on_search)
        self.search_bar.installEventFilter(self)

        self.menu_btn = QPushButton("\u22ef")  # ⋯ vertical ellipsis
        self.menu_btn.setFixedSize(24, 24)
        self.menu_btn.setFlat(True)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.clicked.connect(self._show_menu)

        search_row.addWidget(self.search_bar)
        search_row.addWidget(self.menu_btn)

        self.clip_list = QListWidget()
        self.clip_list.itemDoubleClicked.connect(self._on_paste_selected)
        self.clip_list.keyPressEvent = self._list_key_press_event

        self.status_label = QLabel("Ready")
        self.status_label.setCursor(Qt.CursorShape.OpenHandCursor)

        layout.addLayout(search_row)
        layout.addWidget(self.clip_list)
        layout.addWidget(self.status_label)

        self.load_clips()
        logging.info(f"ClipWindow initialized, db={db_path}")

    def eventFilter(self, obj, event):
        """Intercept key events in search bar for list navigation and actions."""
        if obj is self.search_bar and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                row = self.clip_list.currentRow()
                if row > 0:
                    self.clip_list.setCurrentRow(row - 1)
                return True
            elif key == Qt.Key.Key_Down:
                row = self.clip_list.currentRow()
                if row < self.clip_list.count() - 1:
                    self.clip_list.setCurrentRow(row + 1)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._on_paste_selected()
                return True
            elif key == Qt.Key.Key_Escape:
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def load_clips(self, keyword: str = "", mode: str = "like") -> None:
        """Load clips from database, optionally filtered by keyword."""
        if keyword:
            clips = db.search_clips(self.conn, keyword, mode)
        else:
            clips = db.load_recent(self.conn)

        self._clips = clips
        self.clip_list.clear()

        for clip in clips:
            preview = clip.get("mText", "")
            if len(preview) > 50:
                preview = preview[:47] + "..."
            self.clip_list.addItem(preview or "<empty>")

        if clips:
            self.clip_list.setCurrentRow(0)

        self.status_label.setText(f"{len(clips)} clips")
        logging.info(f"Loaded {len(clips)} clips")

    def _on_search(self) -> None:
        """Handle search text change with debounce."""
        self._current_keyword = self.search_bar.text()
        self._search_timer.start(150)

    def _on_search_debounced(self) -> None:
        """Execute debounced search."""
        self.load_clips(self._current_keyword, self._search_mode)

    def _on_paste_selected(self, item=None) -> None:
        """Paste the selected clip."""
        current_row = self.clip_list.currentRow()
        if current_row < 0 or current_row >= len(self._clips):
            return

        clip = self._clips[current_row]
        clip_id = clip["lID"]
        self._do_paste(clip_id)

    def _do_paste(self, clip_id: int) -> None:
        """Load clip data, write to clipboard, hide window, and send Ctrl+V."""
        data_rows = db.load_clip_data(self.conn, clip_id)
        if not data_rows:
            logging.warning(f"No data for clip {clip_id}")
            return

        app_clipboard = QApplication.clipboard()
        mime_data = QMimeData()

        for row in data_rows:
            fmt = row.get("strClipBoardFormat", "")
            raw = row.get("ooData", b"")
            if not raw:
                continue

            if fmt == "CF_UNICODETEXT":
                if isinstance(raw, bytes):
                    # Ditto stores CF_UNICODETEXT as UTF-16LE (wchar_t)
                    try:
                        text = raw.decode("utf-16-le").rstrip("\x00")
                    except UnicodeDecodeError:
                        text = raw.decode("utf-8", errors="replace")
                else:
                    text = str(raw)
                mime_data.setText(text)
            elif fmt == "CF_DIB":
                # Convert DIB to QImage: prepend 14-byte BMP file header
                bmp_header = b"BM" + len(raw + 14).to_bytes(4, "little") + b"\x00\x00\x00\x00" + b"\x36\x00\x00\x00"
                img = QImage.fromData(bmp_header + raw)
                if not img.isNull():
                    mime_data.setImageData(img)

        # Set "Clipboard Viewer Ignore" format to prevent self-paste
        mime_data.setData(CLIPBOARD_IGNORE_FORMAT, b"")
        app_clipboard.setMimeData(mime_data)

        self.hide()
        QTimer.singleShot(50, lambda: paste.send_ctrl_v())
        logging.info(f"Pasting clip {clip_id}")

    def show_at_cursor(self) -> None:
        """Position window near cursor and show it."""
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen:
            screen_geometry = screen.availableGeometry()
            x = max(0, min(cursor_pos.x() - 300, screen_geometry.width() - 600))
            y = max(0, min(cursor_pos.y() - 200, screen_geometry.height() - 400))
        else:
            x = cursor_pos.x() - 300
            y = cursor_pos.y() - 200

        self.move(x, y)
        self.load_clips()
        self.show()
        self.activateWindow()
        self.search_bar.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self._on_paste_selected()
        elif key == Qt.Key.Key_Escape:
            self.hide()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            index = key - Qt.Key.Key_0
            if 1 <= index <= 9 and index <= len(self._clips):
                clip = self._clips[index - 1]
                self._do_paste(clip["lID"])

    def _list_key_press_event(self, event: QKeyEvent) -> None:
        """Handle key press events in the clip list."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_J or key == Qt.Key.Key_Down:
            current_row = self.clip_list.currentRow()
            if current_row < self.clip_list.count() - 1:
                self.clip_list.setCurrentRow(current_row + 1)
        elif key == Qt.Key.Key_K or key == Qt.Key.Key_Up:
            current_row = self.clip_list.currentRow()
            if current_row > 0:
                self.clip_list.setCurrentRow(current_row - 1)
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self._on_paste_selected()
        elif key == Qt.Key.Key_Escape:
            self.hide()
        elif modifiers == Qt.KeyboardModifier.ControlModifier and Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            index = key - Qt.Key.Key_0
            if 1 <= index <= 9 and index <= len(self._clips):
                clip = self._clips[index - 1]
                self._do_paste(clip["lID"])
        else:
            QListWidget.keyPressEvent(self.clip_list, event)

    @property
    def search_mode(self) -> str:
        """Return current search mode."""
        return self._search_mode

    def set_search_mode(self, mode: str) -> None:
        """Set search mode and re-run search."""
        if mode in ("like", "regex"):
            self._search_mode = mode
            self.load_clips(self._current_keyword, self._search_mode)

    def _show_menu(self) -> None:
        """Show context menu from the menu button."""
        menu = QMenu(self)
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._show_settings)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        menu.exec(QCursor.pos())

    def _show_settings(self) -> None:
        """Show settings dialog."""
        cfg = config.load_config()

        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setFixedSize(420, 100)

        layout = QVBoxLayout(dialog)

        # DB path row
        row = QHBoxLayout()
        row.addWidget(QLabel("DB Path:"))
        db_input = QLineEdit()
        db_input.setText(cfg.get("db_path", ""))
        db_input.setPlaceholderText("Path to Ditto database file")
        row.addWidget(db_input)
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(30, 24)
        browse_btn.clicked.connect(lambda: self._browse_db(db_input))
        row.addWidget(browse_btn)
        layout.addLayout(row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = db_input.text().strip()
            cfg["db_path"] = new_path
            config.save_config(cfg)
            if new_path:
                self._reconnect_db(new_path)

    def _browse_db(self, input_field: QLineEdit) -> None:
        """Open file dialog to select database file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Ditto Database", "",
            "Database Files (*.db);;All Files (*)",
        )
        if path:
            input_field.setText(path)

    def _reconnect_db(self, db_path_str: str) -> None:
        """Close current DB and reconnect to a new one."""
        new_path = Path(db_path_str)
        if not new_path.exists():
            logging.warning(f"DB not found: {new_path}")
            self.status_label.setText(f"DB not found: {new_path}")
            return
        self.conn.close()
        self.db_path = new_path
        self.conn = db.open_db(new_path)
        self.load_clips()
        logging.info(f"Reconnected to {new_path}")

    def mousePressEvent(self, event):
        """Start window drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Move window while dragging."""
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """Stop window drag."""
        self._drag_pos = None

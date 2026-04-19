"""Application coordinator for VDitto. Ties together hotkey, monitor, window, and DB."""
from __future__ import annotations

import logging
import logging.handlers
import os
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from vditto import clipboard, config, db, hotkey, monitor
from vditto.main_window import ClipWindow
from vditto.macro_save import detect_macro, save_markdown, resolve_save_dir

_listener = None
_window = None
_app = None
_tray = None


class _Bridge(QObject):
    """Thread bridge: emits signals from pynput thread to Qt main thread."""
    toggle_window = Signal()


_bridge = _Bridge()


def _icon_path() -> Path:
    """Resolve path to Ditto.ico for system tray."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "res" / "Ditto.ico"
    return Path(__file__).parent.parent / "res" / "Ditto.ico"


def _on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
    """Handle tray icon activation (double-click to toggle window)."""
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        _on_toggle_window()


def _resolve_db_path(db_path: Path | None) -> Path:
    if db_path is not None:
        return db_path
    cfg = config.load_config()
    cfg_path = cfg.get("db_path", "")
    if cfg_path:
        return Path(cfg_path)
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Ditto" / "Ditto.db"
    return Path.home() / ".ditto.db"


def _on_hotkey() -> None:
    """Called from pynput thread. Emit signal to marshal to Qt main thread."""
    _bridge.toggle_window.emit()


def _on_toggle_window() -> None:
    """Called on Qt main thread via signal."""
    if _window is None:
        return
    if _window.isVisible():
        _window.hide()
    else:
        _window.show_at_cursor()


def _on_clip(clip_type: str, data: bytes, preview: str) -> None:
    """Handle clipboard change - save to database."""
    if _window is None:
        return

    # F7: Macro auto-save (independent from DB)
    if clip_type == "text":
        try:
            name, clean_text = detect_macro(preview)
            if name is not None or clean_text != preview:
                # Macro was detected and removed
                if not clean_text.strip():
                    logging.debug("Macro content empty after strip, skipping save")
                    return
                save_dir = resolve_save_dir()
                saved_path = save_markdown(clean_text, name, save_dir)
                if _tray is not None:
                    _tray.showMessage(
                        "VDitto",
                        f"已保存: {saved_path.name}",
                        QSystemTrayIcon.MessageIcon.Information,
                        2000,
                    )
                logging.info(f"Macro save: {saved_path}")
        except Exception:
            logging.exception("Macro save failed")

    # F1: Save to DB (always runs, independent of macro save)
    conn = _window.conn
    mtext = clipboard.make_preview_text(preview) if clip_type == "text" else preview
    lid = db.save_clip(conn, mtext, clip_type, data)
    logging.debug(f"Clip saved: id={lid}, type={clip_type}")


def _setup_logging() -> None:
    """Configure root logger with rotating file handler."""
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).parent / "logs"
    else:
        log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.handlers.RotatingFileHandler(
        log_dir / "vditto.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)


def run(db_path: Path | None = None) -> int:
    global _listener, _window, _app, _tray

    _setup_logging()

    # Ensure config.json exists; persist CLI db_path if provided
    config.ensure_config(str(db_path) if db_path else "")

    db_path = _resolve_db_path(db_path)
    logging.info(f"VDitto starting, db={db_path}")

    if not db_path.exists():
        logging.warning(f"DB not found: {db_path}")

    _app = QApplication.instance() or QApplication(sys.argv)
    _app.setQuitOnLastWindowClosed(False)

    _window = ClipWindow(db_path)

    # System tray icon
    icon_file = _icon_path()
    if icon_file.exists():
        tray_icon = QIcon(str(icon_file))
    else:
        from PySide6.QtWidgets import QStyle
        tray_icon = _app.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
    _tray = QSystemTrayIcon(tray_icon, _app)
    _tray.setToolTip("VDitto - Ctrl+` to toggle")
    tray_menu = QMenu()
    quit_action = tray_menu.addAction("Quit")
    quit_action.triggered.connect(_app.quit)
    _tray.setContextMenu(tray_menu)
    _tray.activated.connect(_on_tray_activated)
    _tray.show()

    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda *_: _app.quit())

    # Connect signal bridge (cross-thread: pynput → Qt main thread)
    _bridge.toggle_window.connect(_on_toggle_window)

    clip_obj = monitor.start_clipboard_monitor(_app, _on_clip)
    _listener = hotkey.start_hotkey_listener(_on_hotkey)

    exit_code = _app.exec()

    monitor.stop_clipboard_monitor(clip_obj)
    hotkey.stop_hotkey_listener(_listener)

    logging.info("VDitto shutdown")
    return exit_code

"""Global hotkey listener for VDitto (F2). Registers Ctrl+` via pynput."""
from __future__ import annotations

import logging
from pynput import keyboard


def start_hotkey_listener(callback: callable) -> keyboard.GlobalHotKeys:
    """Create and start a global hotkey listener.

    Args:
        callback: Function to call when Ctrl+` is pressed

    Returns:
        The GlobalHotKeys listener object (caller responsible for joining/stopping)
    """
    listener = keyboard.GlobalHotKeys({
        '<ctrl>+`': callback,
    })
    listener.start()
    logging.info("Hotkey listener started (Ctrl+`)")
    return listener


def stop_hotkey_listener(listener: keyboard.GlobalHotKeys) -> None:
    """Stop a running hotkey listener.

    Args:
        listener: The GlobalHotKeys listener object to stop
    """
    listener.stop()
    logging.info("Hotkey listener stopped")

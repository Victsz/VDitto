@echo off
chcp 65001 >nul

echo ============================================
echo   T3: SendInput Ctrl+V
echo ============================================
echo Install deps...
uv run --with pynput --with pyside6 --with pillow python -c "print('deps ok')"
echo.
echo Please: copy some text, open Notepad, then press Enter
echo.
pause
uv run --with pynput --with pyside6 --with pillow python "%~dp0test_sendinput.py"

echo.
echo ============================================
echo   T4: Global Hotkey
echo ============================================
echo Press Ctrl+` to test, Ctrl+Shift+Q to exit
echo.
uv run --with pynput --with pyside6 --with pillow python "%~dp0test_hotkey.py"

echo.
pause

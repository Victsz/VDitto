@echo off
chcp 65001 >nul
echo ============================================
echo   VDitto Feasibility Tests
echo ============================================
echo.

set "UV=%USERPROFILE%\.local\bin\uv.exe"
set "PY=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"

where uv >nul 2>&1
if %errorlevel% neq 0 (
    where %UV% >nul 2>&1
    if %errorlevel% neq 0 (
        echo [FAIL] uv not found. Install: pip install uv
        pause
        exit /b 1
    )
    set "UV=%UV%"
) else (
    set "UV=uv"
)

echo [INFO] Using uv: %UV%

REM Create temp project
set "TMPDIR=%TEMP%\vditti-feasi"
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
mkdir "%TMPDIR%"

echo [INFO] Setting up test env...
%UV% init --name vditto_test --python 3.11 --directory "%TMPDIR%" >nul 2>&1
%UV% add pyside6 pynput pillow --directory "%TMPDIR%" >nul 2>&1

REM Copy test files
set "SCRIPT_DIR=%~dp0"
copy "%SCRIPT_DIR%test_clipboard_monitor.py" "%TMPDIR%\" >nul
copy "%SCRIPT_DIR%test_sendinput.py" "%TMPDIR%\" >nul
copy "%SCRIPT_DIR%test_hotkey.py" "%TMPDIR%\" >nul

echo.
echo ============================================
echo   T2: Clipboard Monitor
echo ============================================
echo Copy some text/image from any app...
echo Press Ctrl+C to stop this test
echo.
%UV% run --directory "%TMPDIR%" python "%TMPDIR%\test_clipboard_monitor.py"

echo.
echo ============================================
echo   T3: SendInput Ctrl+V
echo ============================================
echo Please open Notepad and copy some text first
echo.
pause
%UV% run --directory "%TMPDIR%" python "%TMPDIR%\test_sendinput.py"

echo.
echo ============================================
echo   T4: Global Hotkey
echo ============================================
echo Press Ctrl+` to test, Ctrl+Shift+Q to exit
echo.
%UV% run --directory "%TMPDIR%" python "%TMPDIR%\test_hotkey.py"

echo.
pause

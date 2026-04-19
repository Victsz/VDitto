@echo off
chcp 65001 >nul 2>&1
title VDitto

REM === Resolve project directory (must be on Windows native path) ===
set "PROJ_DIR=%~dp0"
REM Remove trailing backslash
set "PROJ_DIR=%PROJ_DIR:~0,-1%"

REM Detect UNC path (\\wsl$\ or \\wsl.localhost\)
echo %PROJ_DIR% | findstr /r "^\\\\wsl" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [ERROR] Project is on WSL filesystem, Windows cannot run Python from here.
    echo.
    echo Copy project to a Windows native path first:
    echo   xcopy /E /I "%PROJ_DIR%" "C:\storage\LINK_SRC\VDitto"
    echo   Then run: C:\storage\LINK_SRC\VDitto\run.bat
    echo.
    echo Or run from Windows PowerShell:
    echo   wsl -d Ubuntu -- bash -c "cd /home/victor/workspace_local/VDitto ^&^& uv run python -m vditto"
    pause
    exit /b 1
)

cd /d "%PROJ_DIR%"
echo === VDitto Launch ===
echo Project: %PROJ_DIR%
echo.

REM Check uv
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv not found. Install: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

REM Remove Linux .venv if present (incompatible with Windows)
if exist ".venv\bin\python3" (
    echo [INFO] Removing Linux .venv (incompatible with Windows^)
    rmdir /s /q .venv
)

REM Install dependencies
echo [1/3] Installing dependencies...
uv sync
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv sync failed
    pause
    exit /b 1
)

REM Run unit tests (non-GUI)
echo [2/3] Running unit tests...
uv run python -m unittest discover -s tests -p test.py -v
if %ERRORLEVEL% neq 0 (
    echo [WARN] Some unit tests failed
    echo.
)

REM Launch GUI
echo [3/3] Starting VDitto...
echo Press Ctrl+` to open clip list
echo Close this window to exit
echo.
uv run python -m vditto --db "C:\storage\LINK_SRC\Ditto.db"

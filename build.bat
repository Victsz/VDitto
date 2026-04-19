@echo off
chcp 65001 >nul 2>&1
title VDitto Build

set "PROJ_DIR=%~dp0"
set "PROJ_DIR=%PROJ_DIR:~0,-1%"
set "BUILD_DIR=%TEMP%\vditto-build"
set "DEST=%USERPROFILE%\Downloads\VDitto"

echo =============================
echo   VDitto Build
echo =============================
echo.

REM === Handle UNC path (WSL filesystem) ===
echo %PROJ_DIR% | findstr /r "^\\\\wsl" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] WSL UNC path detected, copying source to temp...
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
    mkdir "%BUILD_DIR%"
    robocopy "%PROJ_DIR%\vditto" "%BUILD_DIR%\vditto" /S /NFL /NDL /NJH /NJS /NC /NS >nul
    copy /Y "%PROJ_DIR%\pyproject.toml" "%BUILD_DIR%\" >nul
    if exist "%PROJ_DIR%\README.md" copy /Y "%PROJ_DIR%\README.md" "%BUILD_DIR%\" >nul
    mkdir "%BUILD_DIR%\res" 2>nul
    copy /Y "%PROJ_DIR%\res\Ditto.ico" "%BUILD_DIR%\res\" >nul
    cd /d "%BUILD_DIR%"
) else (
    cd /d "%PROJ_DIR%"
)

REM === Clean Linux .venv if present ===
if exist ".venv\bin\python3" (
    echo [INFO] Removing Linux .venv...
    rmdir /s /q .venv
)

REM === Check uv ===
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv not found. Install: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

REM === Install dependencies + pyinstaller ===
echo [1/3] Installing dependencies...
uv sync
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv sync failed
    pause
    exit /b 1
)
uv pip install pyinstaller >nul 2>&1

REM === Build ===
echo [2/3] Building VDitto.exe...
uv run pyinstaller ^
    --name VDitto ^
    --onedir ^
    --noconfirm ^
    --windowed ^
    --icon res/Ditto.ico ^
    --add-data "res/Ditto.ico;res" ^
    --hidden-import=pynput.keyboard._win32 ^
    --hidden-import=pynput.mouse._win32 ^
    vditto/__main__.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

REM === Deploy to Downloads ===
echo [3/3] Deploying to %DEST%...
if exist "%DEST%" rmdir /s /q "%DEST%"
xcopy /E /I /Q "dist\VDitto" "%DEST%"

REM === Create launcher ===
echo @echo off > "%DEST%\run-vditto.bat"
echo cd /d "%%~dp0" >> "%DEST%\run-vditto.bat"
echo VDitto.exe --db "C:\storage\LINK_SRC\Ditto.db" >> "%DEST%\run-vditto.bat"

echo.
echo =============================
echo   Build complete!
echo   %DEST%\VDitto.exe
echo.
echo   Run:  double-click run-vditto.bat
echo   Or:   VDitto.exe --db "C:\storage\LINK_SRC\Ditto.db"
echo =============================
echo.
pause

@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "APP_VERSION=1.0.0"
set "PYTHON_EXE=.venv\Scripts\python.exe"

echo ========================================
echo   123Mark v%APP_VERSION% - Windows standalone build
echo ========================================

if not exist "%PYTHON_EXE%" (
    echo [1/5] Creating build environment...
    python -m venv .venv
    if errorlevel 1 goto :failed
)

echo [2/5] Installing build dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :failed

echo [3/5] Generating application icon...
"%PYTHON_EXE%" create_icon.py
if errorlevel 1 goto :failed

echo [4/5] Running tests...
"%PYTHON_EXE%" -m unittest discover -s tests -v
if errorlevel 1 goto :failed

echo [5/5] Building standalone executable...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean 123Mark.spec
if errorlevel 1 goto :failed

if not exist "release" mkdir "release"
copy /Y "dist\123Mark-v%APP_VERSION%.exe" "release\123Mark-v%APP_VERSION%.exe" >nul

echo.
echo Build complete: release\123Mark-v%APP_VERSION%.exe
echo The EXE runs directly on Windows 10/11 without Python.
exit /b 0

:failed
echo.
echo Build failed. Review the error output above.
exit /b 1

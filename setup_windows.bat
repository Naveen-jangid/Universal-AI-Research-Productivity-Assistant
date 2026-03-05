@echo off
REM ─── Fresh Environment Setup for Windows ──────────────────────────────────
REM Run this from the project root directory.
REM Requires Python 3.11+ installed and available on PATH.

setlocal enabledelayedexpansion

echo.
echo  ============================================================
echo   Universal AI Research ^& Productivity Assistant
echo   Windows Fresh Environment Setup
echo  ============================================================
echo.

REM ── Check Python ───────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Download from https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% found

REM ── Remove old venv if exists ──────────────────────────────────────────────
if exist .venv (
    echo  [INFO] Removing old .venv...
    rmdir /s /q .venv
)

REM ── Create fresh venv ─────────────────────────────────────────────────────
echo  [INFO] Creating fresh virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause & exit /b 1
)
echo  [OK] Virtual environment created at .venv\

REM ── Activate venv ─────────────────────────────────────────────────────────
call .venv\Scripts\activate.bat
echo  [OK] Virtual environment activated

REM ── Upgrade pip ───────────────────────────────────────────────────────────
echo  [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  [OK] pip upgraded

REM ── Install PyTorch CPU (separate step, uses PyTorch index) ───────────────
echo  [INFO] Installing PyTorch CPU (this may take a few minutes)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
if errorlevel 1 (
    echo  [WARN] PyTorch install failed. Continuing without it.
    echo         HuggingFace local models will not work, but OpenAI features will.
) else (
    echo  [OK] PyTorch installed
)

REM ── Install main requirements ──────────────────────────────────────────────
echo  [INFO] Installing project dependencies...
pip install -r requirements-windows.txt
if errorlevel 1 (
    echo  [ERROR] Some packages failed. See output above.
    echo         Try running manually: pip install -r requirements-windows.txt
    pause & exit /b 1
)
echo  [OK] All dependencies installed

REM ── Create .env if missing ─────────────────────────────────────────────────
if not exist .env (
    copy .env.example .env >nul
    echo  [INFO] Created .env from template.
)

REM ── Create runtime dirs ────────────────────────────────────────────────────
for %%d in (uploads\documents uploads\images uploads\audio uploads\data vectorstore memory logs) do (
    if not exist %%d mkdir %%d
)
echo  [OK] Runtime directories created

REM ── Done ──────────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   Setup complete!
echo  ============================================================
echo.
echo   Next steps:
echo   1. Edit your API key:   notepad .env
echo      Set: OPENAI_API_KEY=sk-your-key-here
echo.
echo   2. Start the app:       start.bat
echo.
echo   The .venv is already active in this window.
echo   To activate later:  .venv\Scripts\activate
echo.
pause

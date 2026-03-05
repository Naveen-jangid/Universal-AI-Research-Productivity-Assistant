@echo off
REM ─── Universal AI Research & Productivity Assistant ───────────────────────
REM Windows startup script. Run from project root with venv activated.

echo.
echo  Universal AI Research ^& Productivity Assistant
echo  ================================================
echo.

REM Check .env exists
if not exist .env (
    echo  [INFO] .env not found. Copying from .env.example...
    copy .env.example .env >nul
    echo  [ACTION] Please edit .env and add your OPENAI_API_KEY, then re-run.
    echo           Open with: notepad .env
    pause
    exit /b 1
)

REM Check OPENAI_API_KEY is set
findstr /C:"OPENAI_API_KEY=sk-" .env >nul 2>&1
if errorlevel 1 (
    echo  [WARN] OPENAI_API_KEY does not appear to be set in .env
    echo         Some features will use local fallback models.
    echo.
)

REM Create runtime directories
if not exist uploads\documents mkdir uploads\documents
if not exist uploads\images    mkdir uploads\images
if not exist uploads\audio     mkdir uploads\audio
if not exist uploads\data      mkdir uploads\data
if not exist vectorstore       mkdir vectorstore
if not exist memory            mkdir memory
if not exist logs              mkdir logs

echo  Starting Backend  ^(FastAPI^)  on http://localhost:8000
echo  Starting Frontend ^(Streamlit^) on http://localhost:8501
echo  API Docs at http://localhost:8000/docs
echo.
echo  Press Ctrl+C in each window to stop.
echo.

REM Start backend in a new window
start "AI Assistant - Backend" cmd /k "uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait 4 seconds for backend to initialise
timeout /t 4 /nobreak >nul

REM Start frontend in a new window
start "AI Assistant - Frontend" cmd /k "streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false"

echo  Both services launched in separate windows.
echo  Open http://localhost:8501 in your browser.
echo.
pause

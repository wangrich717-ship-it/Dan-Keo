@echo off
cd /d "%~dp0"
echo.
echo   Dan Koe Knowledge Base
echo   ─────────────────────────────────────
echo.

REM Build data if not exists
if not exist "data\index.json" (
    echo   Building article data...
    python build_data.py
    if errorlevel 1 (
        echo.
        echo   ERROR: Python not found. Please install Python 3 from python.org
        pause
        exit /b 1
    )
    echo.
)

REM Open browser and start server
echo   Starting server at http://localhost:8080
echo   Press Ctrl+C to stop.
echo.
start "" "http://localhost:8080"
python -m http.server 8080
pause

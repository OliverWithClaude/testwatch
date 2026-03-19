@echo off
echo ========================================
echo   TestWatch Server
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting TestWatch...
echo Open your browser at: http://127.0.0.1:5050
echo.
echo Log file: testwatch.log
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

python app.py

pause

@echo off
echo ========================================
echo   TestWatch Server
echo ========================================
echo.

cd /d "%~dp0"

echo Killing any existing processes on port 5050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050" ^| findstr "LISTENING"') do (
    echo   Killing PID %%a
    taskkill /F /PID %%a 2>nul
)
echo.

echo Clearing Python cache...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
del /s /q *.pyc 2>nul
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Starting TestWatch (waitress)
echo   Log file: testwatch.log
echo   Press Ctrl+C to stop the server.
echo ========================================
echo.

python app.py

pause

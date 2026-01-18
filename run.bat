@echo off
REM Football Team Manager - Quick Start Script for Windows

echo ⚽ Football Team Manager - Starting...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP:~1%

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🚀 Starting Football Team Manager...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📱 Access the app from:
echo    Local:   http://localhost:5000
echo    Network: http://%LOCAL_IP%:5000
echo.
echo 💡 Tips:
echo    - Add players first before scheduling games
echo    - Check Statistics page before each game for fairness
echo    - Use Substitution Recommendations during games
echo.
echo Press Ctrl+C to stop the server
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Run the application
python app.py

pause

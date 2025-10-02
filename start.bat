@echo off
echo Starting AI Executive Panel Simulator...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo No .env file found!
    echo Copying template...
    copy .env.template .env
    echo.
    echo Please edit .env and add your OpenAI API key:
    echo    OPENAI_API_KEY=sk-your-actual-api-key-here
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

REM Start the application
echo Starting the application...
echo Open your browser to: http://localhost:5000
echo.
python app.py
pause

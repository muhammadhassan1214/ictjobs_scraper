@echo off
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH. Please install Python first.
    pause
    exit /b 1
)

echo Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies. Please check your internet connection and try again.
    pause
    exit /b 1
)

echo Running the program...
python main.py
if errorlevel 1 (
    echo Program execution failed.
    pause
    exit /b 1
)

echo Program completed successfully.
pause
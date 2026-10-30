@echo off
chcp 65001 >nul
title Workforce Attendance System - Automated Setup & Launch
color 0b

echo ========================================================================
echo    WORKFORCE ATTENDANCE & BIOMETRIC SYSTEM - ONE-CLICK SETUP
echo ========================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH!
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
python -m pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b %errorlevel%
)

echo Initializing database...
python -c "import database as db; db.init_db(); db.seed_default_data(); print('[OK] Database ready.')"

echo.
echo Launching default web browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5000

echo.
echo Starting application server at http://localhost:5000...
cd /d "%~dp0"
python app.py

pause

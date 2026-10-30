@echo off
chcp 65001 >nul
title Workforce Attendance System - Server Launcher
color 0a

echo ========================================================================
echo    WORKFORCE ATTENDANCE SYSTEM - FAST LAUNCHER
echo ========================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH!
    pause
    exit /b 1
)

echo Starting application server at http://localhost:5000...
timeout /t 2 /nobreak >nul
start http://localhost:5000

cd /d "%~dp0"
python app.py

pause

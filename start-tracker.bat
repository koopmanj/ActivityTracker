@echo off
title Activity Tracker
echo ============================================
echo   Windows Activity Tracker
echo   Press Ctrl+C to stop tracking
echo ============================================
echo.
cd /d "%~dp0"
python tracker.py
pause

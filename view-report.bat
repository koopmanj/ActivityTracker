@echo off
echo ============================================
echo   Activity Report Generator
echo ============================================
echo.
cd /d "%~dp0"

if "%1"=="--week" (
    echo Generating weekly report...
    python report.py --week
) else if "%1"=="" (
    echo Generating today's report...
    python report.py
) else (
    echo Generating report for %1...
    python report.py %1
)
pause

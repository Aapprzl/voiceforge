@echo off
setlocal EnableDelayedExpansion

echo ======================================
echo VoiceForge - Starting (Hardened Mode)
echo ======================================
echo.

echo [1] Environment Setup...
:: Ensure working directory is correct
cd /d "%~dp0"

:: Set base environment variables if not already set in main.py
set QT_QPA_PLATFORM=windows

echo [2] Launching Application...
C:\Python313\python.exe main.py
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================
echo [Exit Code: %EXIT_CODE%]
if %EXIT_CODE% neq 0 (
    echo [ERROR] Application crashed on exit or startup.
    echo Please check debug_log.txt for details.
) else (
    echo Application closed normally.
)
echo ======================================
echo.
pause
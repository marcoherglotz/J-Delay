@echo off
title J-Delay Launcher
echo ===================================================
echo   J-DELAY: JACK Input Latency Compensator
echo ===================================================
echo.
echo Checking and installing dependencies (numpy, JACK-Client)...
pip install -r requirements_j_delay.txt
echo.
echo Starting J-Delay...
echo (Ensure that JACK / QJackCtl is already running!)
echo.
python J-Delay.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while starting.
    pause
)

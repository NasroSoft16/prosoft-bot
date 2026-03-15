@echo off
setlocal enabledelayedexpansion
title PROSOFT QUANTUM PRIME - SOVEREIGN ENGINE
color 0b
cls

:: Force local directory execution
cd /d "%~dp0"

echo.
echo  =============================================================
echo    PROSOFT QUANTUM PRIME - SOVEREIGN PORTABLE V7
echo    * FULLY CONTAINED ZERO-INSTALL ENGINE *
echo  =============================================================
echo.

set LOCAL_PY="%~dp0python\python.exe"

if exist %LOCAL_PY% (
    echo  [*] STARTING SOVEREIGN ENGINE...
    echo  [*] DASHBOARD: http://localhost:5000
    echo.
    echo  [SYSTEM IS LIVE] - DO NOT CLOSE UNLESS TERMINATING
    echo  -------------------------------------------------------------
    echo.
    %LOCAL_PY% main.py
    if %errorlevel% neq 0 (
        echo.
        echo  [!] SYSTEM STOPPED WITH ERROR CODE %errorlevel%
    )
) else (
    echo  [X] ERROR: Local Sovereign Engine NOT FOUND.
    echo  [!] Action: Run prepare_dist.py on the developer PC first.
)
echo.
pause

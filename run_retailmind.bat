@echo off
title RetailMind-X AI Command Center
cd /d "%~dp0"
echo ============================================================
echo   RETAILMIND-X — RETAIL SALES FORECASTING & INVENTORY SYSTEM
echo   Vaidsys Technologies Data Science Internship Project 1
echo ============================================================
echo.
echo Starting application server and opening web browser...
python scripts/launcher.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while launching RetailMind-X.
    pause
)

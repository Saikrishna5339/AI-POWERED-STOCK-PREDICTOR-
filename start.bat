@echo off
title StockAI Pro - Indian Stock Market Platform
color 0A

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║       StockAI Pro - Indian Market Platform          ║
echo ║    LSTM + Technical Analysis + Sentiment AI         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import fastapi, uvicorn, yfinance, pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [2/3] Checking VADER sentiment...
python -c "from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing vaderSentiment...
    pip install vaderSentiment
)

echo [3/3] Starting StockAI Pro...
echo.
echo [INFO] Dashboard will open at: http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server
echo.

:: Start the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause

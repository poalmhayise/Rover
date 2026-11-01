@echo off
title Hired - CV and Application Letter Website
cd /d "%~dp0"
echo =======================================
echo         HIRED - WEBSITE SERVER
echo =======================================
echo.
echo Please ensure Python and requirements.txt dependencies are installed.
echo Your website will be at http://127.0.0.1:8080
start "" "http://127.0.0.1:8080"
python server.py
pause

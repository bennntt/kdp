@echo off
echo ========================================
echo    KdpToolHub - Starting Application
echo ========================================
echo.
echo Starting XAMPP MySQL (if not running)...
net start mysql > nul 2>&1

echo Starting Flask Application with Virtual Environment...
cd /d "%~dp0"
python run_venv.py

pause
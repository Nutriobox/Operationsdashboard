@echo off
cd /d "%~dp0"
echo Running NutrioBox vehicle report...
python vehicle_report.py %*
if errorlevel 1 ( echo. & echo Report FAILED - see messages above. & pause )

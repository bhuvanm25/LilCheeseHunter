@echo off
cd /d "%~dp0code"

:: Install requirements if missing
echo Checking requirements...
python -m pip install -r requirements.txt >nul 2>&1

:: Launch silently with pythonw.exe (no console)
start "" pythonw.exe navigation.pyw
exit

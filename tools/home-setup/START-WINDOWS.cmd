@echo off
cd /d "%~dp0"
python setup.py
if errorlevel 1 pause

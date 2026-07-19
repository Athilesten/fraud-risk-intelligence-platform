@echo off
cd /d "%~dp0\.."
.\venv\Scripts\python.exe streaming\read_delta_tables.py

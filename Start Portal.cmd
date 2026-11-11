@echo off
cd /d "%~dp0"
set "OBE_WORD_PDF=1"
if exist "private-data\connection.cmd" call "private-data\connection.cmd"
if exist "private-data\report-connection.cmd" call "private-data\report-connection.cmd"
if exist "private-data\live-session.cmd" call "private-data\live-session.cmd"
if not defined OBE_DB_PATH if exist "private-data\real.sqlite3" set "OBE_DB_PATH=%~dp0private-data\real.sqlite3"
.venv\Scripts\python.exe tools\launch_workspace.py
if errorlevel 1 pause

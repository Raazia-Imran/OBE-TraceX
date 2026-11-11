@echo off
cd /d "%~dp0"
set "OBE_WORD_PDF=1"
if exist "private-data\report-connection.cmd" call "private-data\report-connection.cmd"
if exist "private-data\google-reader.json" set "GOOGLE_APPLICATION_CREDENTIALS=%~dp0private-data\google-reader.json"
if exist "private-data\connection.cmd" call "private-data\connection.cmd"
if not defined OBE_DB_PATH if exist "private-data\expo.sqlite3" set "OBE_DB_PATH=%~dp0private-data\expo.sqlite3"
if exist "private-data\live-session.cmd" start "OBE-TraceX Live Sync" /min cmd /c call "%~dp0Start Live Updates.cmd"
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause

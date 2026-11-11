@echo off
cd /d "%~dp0"
if exist "private-data\connection.cmd" call "private-data\connection.cmd"
set "OBE_DB_PATH=%~dp0private-data\expo.sqlite3"
set "OBE_WORD_PDF=1"
if not exist "private-data\expo.sqlite3" (
 echo Expo database is missing. The original local database has not been changed.
 pause
 exit /b 1
)
echo Starting OBE-TraceX Expo workspace. Original local database is preserved.
start "" "http://127.0.0.1:8000/?session=3"
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause

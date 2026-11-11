@echo off
cd /d "%~dp0"
if exist "private-data\connection.cmd" call "private-data\connection.cmd"
if exist "private-data\live-session.cmd" call "private-data\live-session.cmd"
if not defined OBE_LIVE_SESSION_ID (
 echo Configure OBE_LIVE_SESSION_ID and OBE_SYNC_COORDINATOR in private-data\live-session.cmd first.
 pause
 exit /b 1
)
if not defined OBE_SYNC_COORDINATOR (
 echo Configure OBE_SYNC_COORDINATOR in private-data\live-session.cmd first.
 pause
 exit /b 1
)
if not defined OBE_DB_PATH if exist "private-data\expo.sqlite3" set "OBE_DB_PATH=%~dp0private-data\expo.sqlite3"
.venv\Scripts\python.exe manage.py watch_master --session %OBE_LIVE_SESSION_ID% --coordinator %OBE_SYNC_COORDINATOR% --interval 60
pause

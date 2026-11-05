@echo off
cd /d "%~dp0"
set "OBE_WORD_PDF=1"
if exist "private-data\google-reader.json" set "GOOGLE_APPLICATION_CREDENTIALS=%~dp0private-data\google-reader.json"
if exist "private-data\connection.cmd" call "private-data\connection.cmd"
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause

# OBE TraceX setup and operations

## Existing installation

[VERIFIED FROM REPOSITORY] Use `D:\ALL PROJECTS\OBE-TraceX`. Double-click `Start Portal.cmd`; sign in at http://127.0.0.1:8000/login/. n8n normally uses http://127.0.0.1:5678/. The launcher can start installed n8n and a configured live reader. An already-running portal causes the launcher to return early, so it does not prove the live worker is running.

The launcher loads private `connection.cmd`, `report-connection.cmd` and `live-session.cmd` when present. Settings choose `OBE_DB_PATH`, otherwise `private-data/real.sqlite3` when it exists, otherwise `local.sqlite3`. `POSTGRES_HOST` overrides SQLite; production refuses SQLite. Explicitly identify the database before any import or account work. Do not assume every launcher or database viewer uses the same database.

Initial login details are private in the existing local `private-data/LOCAL-LOGIN.txt`. Do not copy passwords into team documentation. Give each maintainer their own development login.

## Fresh Windows setup

[VERIFIED FROM REPOSITORY] Requirements: Git, Python compatible with the pinned requirements (CI specifies Python 3.12), and a PDF renderer if PDFs are needed. The existing laptop has its own working virtual environment. Exact requirements pins were preserved, not upgraded during the wording cleanup.

Run in Windows CMD:

```bat
cd /d "D:\ALL PROJECTS"
git clone https://github.com/Raazia-Imran/OBE-TraceX.git
cd OBE-TraceX
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py provision_account coordinator --role coordinator --name "FYDP Coordinator"
.venv\Scripts\python.exe manage.py provision_account hod --role hod --name "Head of Department"
"Start Portal.cmd"
```

Choose individual passwords at the prompts. Clone downloads source and blank templates. It does not transfer real students, local databases, Form links, n8n credentials or private configuration. A fresh empty portal is expected. Do not run `seed_demo` in the real workspace. If a synthetic demo is useful, use an explicitly separate database.

The `.env.example` file is for Docker Compose. Ordinary `manage.py` does not automatically read a `.env`; use shell variables or the existing local CMD configuration. Do not place production secrets into the example file.

## Updating a teammate clone

```bat
git status
git pull --ff-only
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
```

Resolve local changes first. Do not discard work with a hard reset. Restart the web process after source changes because the launcher uses `--noreload`. Database migrations should run only on the intended database with a recoverable backup.

## Manual read and background reader

After the official roster and authorized Google reader are configured, the Coordinator can use Data connections → Read Google Sheets. It performs one fresh source read. Refreshing a browser alone does not fetch Google data.

The current managed local worker uses a numeric session ID:

```bat
.venv\Scripts\python.exe manage.py watch_master --session SESSION_NUMERIC_ID --coordinator coordinator --interval 60
```

Replace `SESSION_NUMERIC_ID` with the verified live database ID. Do not run this on a saved faculty-reference or rehearsal session. The worker refuses these sources and uses a lease to reduce overlapping readers. One managed worker per live session is the intended server setup.

`sync_master` is an older alternative using a session label and `--watch`. It does not populate SyncState in the same way. Prefer `watch_master` for the status page; do not run both continuously for one source.

The worker's nominal interval is 60 seconds and the UI polls portal revision state every 10 seconds. Reads can take longer or fail. This is near-live polling, with no guaranteed instant delivery time.

## Reports and operation

Original templates are `report_templates/D1.docx` through `D7.docx`. Preview output is labelled. Official exports require approved session rules, all six valid frozen stages, a final approval and the exact verified template hash. Preserve signatures as source blank areas; never invent them.

PDFs use LibreOffice headless. The existing Windows launcher allows an installed Microsoft Word fallback through `OBE_WORD_PDF=1`; that fallback is not a Linux deployment strategy. Follow `docs/DEPLOYMENT.md` and visually verify on the department renderer.

## Troubleshooting

| Symptom | Check and action |
|---|---|
| No students after cloning | Import official roster; private data is intentionally absent |
| Wrong records or counts | Identify OBE_DB_PATH and POSTGRES_HOST, then confirm selected session |
| Old source code after updating | Restart the running web process |
| Workbook read fails | Check Google ownership, token health, n8n bridge executable and exact tabs; preserve last data |
| New marks not appearing | Check Form response row, formulas, worker process and selected session in that order |
| Freeze button blocked | Review criteria, roster completeness, session policy and pending corrections |
| PDF fails | Check LibreOffice path or installed Windows Word; DOCX can be inspected separately |
| Empty archive | No reports received/generated in this database; previews do not prove n8n archive delivery |
| Database viewer disagrees | `tools/db_viewer.py` currently hardcodes local.sqlite3; active portal may use real.sqlite3 |

The viewer inconsistency is a documented remaining issue, not silently fixed by this content change.

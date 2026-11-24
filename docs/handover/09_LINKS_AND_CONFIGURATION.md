# OBE TraceX links and configuration

## Known project links

| Destination | Link and status |
|---|---|
| Public repository | https://github.com/Raazia-Imran/OBE-TraceX |
| Current handover in repository | docs/handover/00_START_HERE.md |
| Existing local portal | http://127.0.0.1:8000/ |
| Direct local login | http://127.0.0.1:8000/login/ |
| Existing local n8n | http://127.0.0.1:5678/ |
| University server/domain | Not established in accessible current materials |
| Canonical Form URLs | Six saved locally; owner/destination verification pending; private backup only |
| Master workbook link | Configured privately; inspect owner-approved connection files, not a public placeholder |

Localhost links refer to the computer running the services. They are not remotely accessible deployments or a teammate's running server. This project has no Sanity dashboard or Vercel deployment identified; do not copy those from unrelated website projects.

## Configuration reference

[VERIFIED FROM REPOSITORY] Variable names are listed without secret values.

| Variable | Purpose |
|---|---|
| OBE_ENV | development by default; production enables stricter requirements |
| OBE_DB_PATH | Explicit local SQLite path |
| POSTGRES_HOST, POSTGRES_PORT | PostgreSQL address; presence of host selects PostgreSQL |
| POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD | Department database connection |
| DJANGO_SECRET_KEY | Long random production signing secret |
| OBE_MFA_KEY | Production MFA encryption key |
| DJANGO_ALLOWED_HOSTS | Approved hostnames |
| DJANGO_CSRF_ORIGINS | Approved HTTPS origins |
| TRUST_PROXY | Enable only behind the intended trusted proxy |
| GOOGLE_WORKBOOK_ID | Exact intended source workbook |
| GOOGLE_APPLICATION_CREDENTIALS | Direct read-only Google credential file |
| OBE_N8N_BRIDGE | Local bridge script path; takes precedence over direct reader |
| OBE_MASTER_SNAPSHOT | Private fresh bridge output file |
| OBE_N8N_CLI | Optional installed n8n CLI path |
| OBE_GOOGLE_ACCESS_TOKEN_FILE | Separate authorized token file for Form respondent management |
| N8N_WEBHOOK_SECRET | Optional raw-evaluation signing secret |
| OBE_REPORT_WEBHOOK_SECRET | Individual-report signing secret; receiver has fallback |
| OBE_DEFAULT_SESSION_ID | Default displayed academic session |
| OBE_LIVE_SESSION_ID | Numeric session ID loaded by local launcher for worker |
| OBE_SYNC_COORDINATOR | Authorized portal identity used by local worker |
| SOFFICE_PATH | LibreOffice executable path |
| OBE_WORD_PDF | Installed Windows Word fallback switch |

Do not confuse n8n's own credential encryption key with a portal webhook secret. They protect different data and must remain recoverable through authorized owners. Review the current settings and launcher before editing; environment values can differ across shells and processes.

## Templates supplied for continuation

`stage_mapping_template.csv` has one row per D1–D6 Form and a D7 consolidation row. Fill IDs/URLs and approval references privately. Empty values mean unresolved, not false or completed.

`acceptance_results_template.csv` is an empty evidence sheet. Add actual records with expected/actual criteria, totals, response/execution IDs, file hashes and pass/fail. It contains no invented test results.

`department_decisions_template.md` lists the exact academic, Google ownership and server decisions still needed. Use named decision references only after they exist.

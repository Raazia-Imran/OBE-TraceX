# OBE-TraceX

**Automated Outcome-Based Education Evaluation & Grading Portal**

OBE-TraceX means Outcome-Based Education Tracking, Analysis, and Execution. This portal extends the existing Google Forms → Google Sheets → n8n assessment system for NED University's Department of Software Engineering.

**Current release: tested local pilot.** It includes Coordinator/HOD workspaces, assigned-evaluator validation, correction review, immutable approved snapshots, final approval, original-template Word/PDF generation, source imports and a signed integration endpoint. University deployment, live credential binding and faculty acceptance are still required.

## Corrected master-workbook flow

The existing spreadsheet remains the source of marks. Excel/Google imports now read D7 totals and supporting criterion tabs. Portal records hold approvals and frozen copies; they do not replace the tested spreadsheet grading pipeline. Evaluator assignments are only part of the legacy raw-event path, not a prerequisite for the master-workbook route.

[Read the corrected real-group test, PostgreSQL and live connection guide](docs/REAL_GROUP_END_TO_END.md). No synthetic students are added automatically.

## Start here

- [Simple form-to-final-report scenario](docs/START_TO_FINISH_GUIDE.md)
- [Complete Windows CMD cloning and demo guide](docs/CLONE_AND_RUN_WINDOWS.md)

- [Full development plan](docs/DEVELOPMENT_PLAN.md)
- [Baseline inspection and known differences](docs/BASELINE_REVIEW.md)
- [Testing and acceptance](docs/ACCEPTANCE.md)
- [Verification record and limits](docs/VERIFICATION.md)
- [NED server deployment and recovery](docs/DEPLOYMENT.md)
- [n8n and Google integration](integrations/README.md)
- [Preserved artifact hashes](docs/baseline-manifest.json)

## Architecture

Python / Django 5.2 LTS with HTML, CSS and progressive JavaScript. PostgreSQL is required in production; SQLite supports isolated local development. LibreOffice renders the supplied Word templates to PDF. This avoids depending on a third-party document converter for student data. n8n remains a separate service and its existing reporting workflows are not replaced.

The repository is public. It intentionally excludes student workbooks, Google credentials, n8n databases, personal recipient addresses, raw workflow exports and generated reports. The seven original blank rubric templates are included, with their original bytes recorded in the manifest.

## Local setup (Windows PowerShell)

Requires Python 3.12+ and LibreOffice for PDF downloads. The web portal uses port **8000**; your n8n can stay on **5678**.

```powershell
git clone https://github.com/Raazia-Imran/OBE-TraceX.git
cd OBE-TraceX
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py provision_account coordinator --role coordinator --name "FYDP Coordinator"
.\.venv\Scripts\python.exe manage.py provision_account hod --role hod --name "Head of Department"
$env:SOFFICE_PATH = 'C:\Program Files\LibreOffice\program\soffice.exe'
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. Choose unique passwords interactively; **there are no default usernames/passwords or public registration**. The example account names above are the names you create, not pre-existing accounts. Keep LibreOffice's path aligned with the actual installation.

For Linux/macOS replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` and use `python3 -m venv .venv`.

## First use with real records

1. Create an academic session and import its official group roster.
2. Read the existing master workbook through XLSX upload or the configured read-only Google connection.
3. Review source reconciliation issues. No evaluator re-entry is required for this route.
4. Coordinator freezes reviewed stages; HOD approves the final result and exact template versions.
5. Download D1–D7 group records. For a controlled historical test and optional continuous reads, follow the real-group guide above.

## Verify

```powershell
.\.venv\Scripts\python.exe manage.py test evaluations
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py template_sample --output .\private-samples
```

`template_sample` generates clearly named synthetic verification files and does not change the original templates. Review them in Word and the target server's PDF renderer. Production must run PostgreSQL integration tests and a backup/restore drill in addition to these checks.

## Important boundaries

- This release does not change, activate, import or delete the existing seven n8n workflows or write to Google Sheets.
- The current individual n8n HTML templates still contain QEC references. Their removal is a separately reviewed follow-up change to copies, not silently applied to the tested originals.
- A source import is not a final approval. Frozen snapshots are authoritative for official portal exports.
- The proposed pilot rounding policy preserves calculation precision and displays two decimals; HOD policy approval is required before freezing. There is no automatic 200→100 conversion.
- No deployment has been made to NED servers. Docker configuration is supplied for IT to validate in staging.

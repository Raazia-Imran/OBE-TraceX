# OBE-TraceX

**Automated Outcome-Based Education Evaluation & Grading Portal**

OBE-TraceX means Outcome-Based Education Tracking, Analysis, and Execution. This portal extends the existing Google Forms → Google Sheets → n8n assessment system for NED University's Department of Software Engineering.

**Current release: tested local pilot.** It includes Coordinator/HOD workspaces, assigned-evaluator validation, correction review, immutable approved snapshots, final approval, original-template Word/PDF generation, source imports and a signed integration endpoint. University deployment, live credential binding and faculty acceptance are still required.

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

## First use

1. Coordinator: create a session with the official course code.
2. Import a CSV roster with authoritative seat numbers, names, project IDs/titles and expected membership (1–4 in the supplied templates).
3. Import assigned evaluator emails for each student and stage. A format-valid seat still needs roster membership.
4. Read an XLSX workbook or configure the optional read-only Google Sheets connection.
5. Review import issues; ambiguous evaluator identity and duplicate responses do not silently enter averages.
6. HOD: approve the academic policy only after faculty confirms criteria, weights, averaging, rounding and report units.
7. Coordinator: review and freeze each of D1–D6 for a group. Missing work and pending corrections block freezing.
8. HOD: approve the final result after all six stages are frozen.
9. HOD: compare synthetic populated document samples against originals, then verify template hashes in QEC documents.
10. Download each group's D1–D7 Word/PDF records from the final result. PDF export requires LibreOffice.

CSV samples under `examples/` contain synthetic identities only. Never upload them to the live university source workbook.

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

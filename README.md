# OBE-TraceX

**Automated Outcome-Based Education Evaluation & Grading Portal**

OBE-TraceX means Outcome-Based Education Tracking, Analysis, and Execution. This portal extends the existing Google Forms → Google Sheets → n8n assessment system for NED University's Department of Software Engineering.

**Current release: tested local pilot.** It includes Coordinator/HOD workspaces, assigned-evaluator validation, correction review, immutable approved snapshots, final approval, original-template Word/PDF generation, source imports and a signed integration endpoint. University deployment, live credential binding and faculty acceptance are still required.

## Corrected master-workbook flow

The existing spreadsheet remains the source of marks. Excel/Google imports now read D7 totals and supporting criterion tabs. Portal records hold approvals and frozen copies; they do not replace the tested spreadsheet grading pipeline. Evaluator assignments are only part of the legacy raw-event path, not a prerequisite for the master-workbook route.

[Read the corrected real-group test, PostgreSQL and live connection guide](docs/REAL_GROUP_END_TO_END.md). No synthetic students are added automatically.

## Local trial role update

[Current local setup and role policy](docs/LOCAL_TRIAL.md): Coordinator manages all academic actions; HOD views and downloads. SQLite is used for the laptop trial.

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

## Clone and run locally (Windows CMD)

Anyone can clone the public repository. You do not need a GitHub invitation while the repository remains public.

**Requirements**

- Git
- Python 3.12 or a compatible newer version
- Windows Command Prompt (CMD)
- VS Code (recommended, but not required)
- LibreOffice is optional for PDF rendering; the local launcher can use the installed Microsoft Word PDF fallback.

Check that Git and Python are available:

```bat
git --version
py -3 --version
```

**1. Clone the repository**

Choose a folder where you keep projects. The example below uses `D:\\ALL PROJECTS`; replace it with your own folder if needed.

```bat
if not exist "D:\\ALL PROJECTS" mkdir "D:\\ALL PROJECTS"
cd /d "D:\\ALL PROJECTS"
git clone https://github.com/Raazia-Imran/OBE-TraceX.git
cd OBE-TraceX
```

If you have already cloned the project, do not clone it again into the same folder. Update the existing copy instead:

```bat
cd /d "D:\\ALL PROJECTS\\OBE-TraceX"
git status
git pull --ff-only
```

If Git reports local changes, preserve and resolve them before pulling. Do not use `git reset --hard` to discard work.

**2. Create the virtual environment and install dependencies**

```bat
py -3 -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```

**3. Set up the local database**

```bat
.venv\\Scripts\\python.exe manage.py migrate
.venv\\Scripts\\python.exe manage.py check
```

This creates a separate local SQLite database named `local.sqlite3`. It is not your teammate's database, the university workbook or n8n's database.

**4. Create your own local login accounts**

Run these commands once for a fresh local database:

```bat
.venv\\Scripts\\python.exe manage.py provision_account coordinator --role coordinator --name "FYDP Coordinator"
.venv\\Scripts\\python.exe manage.py provision_account hod --role hod --name "Head of Department"
```

Enter a unique password of at least 14 characters when prompted. The password will not appear on screen while you type. There are no shared default passwords and no public registration. If the accounts already exist, do not create them again.

**5. Start the portal**

From the repository folder, run:

```bat
"Start Portal.cmd"
```

You can also double-click **Start Portal.cmd** in the project folder. Keep its CMD window open while using the portal.

Open this address in your browser:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

**Important notes**

- Cloning downloads the source code only. It does not copy another person's local database, student records, passwords, Google authorization or n8n credentials.
- Each teammate has a separate local database and must create their own local passwords.
- Google Sheets and n8n connections require separate, authorized configuration. Follow [the integration guide](integrations/README.md); never commit credential files, passwords or real student data to GitHub.
- No synthetic students are added automatically. If you want to explore the clearly labelled synthetic demo, follow the [complete Windows CMD guide](docs/CLONE_AND_RUN_WINDOWS.md).
- Do not expose Django's local development server to the public internet. This setup is for local development and demonstration, not university production deployment.

For troubleshooting, updating an existing clone, the optional demo walkthrough, and further setup details, see [docs/CLONE_AND_RUN_WINDOWS.md](docs/CLONE_AND_RUN_WINDOWS.md).

## First use with real records

1. Create an academic session and import its official group roster.
2. Read the existing master workbook through XLSX upload or the configured read-only Google connection.
3. Review source reconciliation issues. No evaluator re-entry is required for this route.
4. Coordinator freezes reviewed stages; HOD approves the final result and exact template versions.
5. Download D1–D7 group records. For a controlled historical test and optional continuous reads, follow the real-group guide above.

## Verify

```powershell
.\\venv\\Scripts\\python.exe manage.py test evaluations
.\\venv\\Scripts\\python.exe manage.py check
.\\venv\\Scripts\\python.exe manage.py template_sample --output .\\private-samples
```

`template_sample` generates clearly named synthetic verification files and does not change the original templates. Review them in Word and the target server's PDF renderer. Production must run PostgreSQL integration tests and a backup/restore drill in addition to these checks.

## Important boundaries

- This release does not change, activate, import or delete the existing seven n8n workflows or write to Google Sheets.
- The current individual n8n HTML templates still contain QEC references. Their removal is a separately reviewed follow-up change to copies, not silently applied to the tested originals.
- A source import is not a final approval. Frozen snapshots are authoritative for official portal exports.
- The proposed pilot rounding policy preserves calculation precision and displays two decimals; HOD policy approval is required before freezing. There is no automatic 200→100 conversion.
- No deployment has been made to NED servers. Docker configuration is supplied for IT to validate in staging.

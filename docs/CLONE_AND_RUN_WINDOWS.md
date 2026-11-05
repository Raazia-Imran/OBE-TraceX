# Clone and Try OBE-TraceX on Windows

These instructions use **Command Prompt (CMD)**. Your existing n8n remains on port 5678. The new portal runs on port 8000 in its own CMD window.

## 1 Install prerequisites

You need Git, Python 3.12 or a compatible newer version, and an internet connection for the first dependency installation. Install LibreOffice if you want PDF downloads. Word downloads and most portal screens work without LibreOffice.

In CMD check:

```bat
git --version
py -3 --version
```

If a command is not recognized, install that application from its official provider and reopen CMD. You do not need Node.js or Docker for this local demonstration.

## 2 Clone the repository

Use an existing projects directory. For example:

```bat
if not exist "D:\ALL PROJECTS" mkdir "D:\ALL PROJECTS"
cd /d "D:\ALL PROJECTS"
git clone https://github.com/Raazia-Imran/OBE-TraceX.git
cd OBE-TraceX
```

If you have already cloned it, do not clone over the same folder:

```bat
cd /d "D:\ALL PROJECTS\OBE-TraceX"
git status
git pull --ff-only
```

If Git reports local modifications, keep them and resolve the update before continuing. Do not use `git reset --hard` to discard work.

## 3 Create the Python environment

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Commands use the environment's full Python path, so you do not need to change PowerShell execution policy or activate anything.

## 4 Create the local portal database

```bat
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py check
```

This creates `local.sqlite3` in the portal folder. It is separate from n8n's database and your Excel workbook. Do not commit or delete it casually; it contains your local portal records.

## 5 Create the two login accounts

```bat
.venv\Scripts\python.exe manage.py provision_account coordinator --role coordinator --name "FYDP Coordinator"
.venv\Scripts\python.exe manage.py provision_account hod --role hod --name "Head of Department"
```

Enter a unique password of at least 14 characters for each when prompted. CMD will not display the characters while you type; that is expected. The two usernames are the names you just chose in these commands. There is no shared default password.

If an account already exists, do not recreate it. Authorized local recovery is:

```bat
.venv\Scripts\python.exe manage.py changepassword coordinator
```

Use the actual account name. This changes that portal account's password only.

## 6 Load the safe demo

For a first look, use the isolated synthetic demo:

```bat
.venv\Scripts\python.exe manage.py seed_demo --coordinator coordinator --confirm-synthetic
```

It creates a clearly labelled DEMO ONLY session, seven fake students and two groups. It does not open Google Forms, write to your real workbook, change n8n or create account passwords. Running it again preserves the existing demo instead of replacing your decisions.

Use a separate clone/local database for real session work later so demo data is not confused with departmental records. Synthetic seeding is disabled in production mode.

## 7 Configure PDF rendering

If LibreOffice is installed in its usual Windows location, run this in the **same CMD window** that will start the portal:

```bat
set "SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe"
```

If installed elsewhere, replace the path with its actual `soffice.exe`. This setting applies to the current CMD session; set it again when starting from a new window.

## 8 Start the portal

```bat
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000 in your browser. Keep this CMD window open. Leave your existing n8n CMD window alone.

Local development does not require an authenticator code unless you have enrolled MFA. Production requires MFA. Do not expose Django's development server to the internet.

## 9 Try the Coordinator screen

Sign in as `coordinator` with the password you created.

You should see seven registered demo students and two project groups. Open DEMO-001. It contains complete synthetic evaluation data but does not start with approved academic policy or frozen stages.

DEMO-002 deliberately has missing later assessments. It demonstrates that the portal blocks incomplete final results.

The Coordinator sees Data connections, Correction review, sessions, QEC documents and activity history. HOD-only actions are enforced by the server.

## 10 Approve the demo policy as HOD

Sign out using the page button. Sign in as `hod`.

Open Academic sessions. Find DEMO ONLY — Synthetic session. Read the policy, check the confirmation box, and enter a note of at least 20 characters, for example `Synthetic demo policy approved for local testing only.` Click Approve session policy.

This approves only the synthetic demo. Do not use a demo approval as evidence of faculty acceptance for real students.

## 11 Freeze the demo stages as Coordinator

Sign out and return as `coordinator`. Open DEMO-001.

For each D1–D6 card, read its marks and enter a review note such as `Synthetic stage reviewed for demonstration.` Click Freeze. Each successful action reloads the group with the new version. Repeat for the six stages.

Do not change browser roles in two tabs sharing the same browser session; signing in/out changes that browser's account. Use separate browser profiles/private windows if you want two simultaneous role sessions.

## 12 Approve the final result as HOD

Sign out and return as `hod`. Open DEMO-001. At D7 final consolidation, enter `Synthetic final result approved for demonstration.` and approve the final result.

The final table now shows the students' six-stage totals out of 200. This is the point where official group exports can become available, subject to template verification.

## 13 Check and verify the template samples

As HOD, open QEC documents. For each required D1–D7 template:

1. Download its original Word document.
2. Download its Synthetic sample Word or PDF.
3. Compare the layout, headings, references, member rows, signature areas and page boundaries.
4. For this synthetic demo only, record a test verification reference and confirm the checkbox.

Real departmental verification must be performed against the approved sources and approved cell units by the responsible staff. The software cannot approve its own QEC acceptability.

## 14 Download a complete group report

Open DEMO-001 and go to final consolidation. Choose D7 PDF or Word. Save the file to your computer. Repeat with D1–D6 to inspect their group summary tables and retained rubric pages.

If PDF conversion fails, verify the LibreOffice path in the CMD window that started the portal. Restart the development server after setting the correct variable. Word download remains available.

You can also generate all seven synthetic samples from CMD:

```bat
.venv\Scripts\python.exe manage.py template_sample --output private-samples
```

That folder is ignored by Git. Its files are labelled SAMPLE_ONLY and do not represent approved student results.

## 15 Try importing your own test workbook

Start a **new test session**, separate from the demo.

As Coordinator, create the session and prepare its official roster CSV. The headers are:

```text
seat,name,project_id,project_title,expected_members,attempt
```

Use the template in `examples\roster.csv`, replacing the sample values with authorized test data. Save as CSV UTF-8. For a real roster, use the official student name and project details, not an arbitrary form spelling.

In Data connections choose your new session, select Official student roster and upload the file. This pilot imports the roster once per session; it does not provide a roster editing screen yet.

Prepare evaluator assignment CSV with:

```text
seat,stage,evaluator,attempt,opens_at,closes_at
```

List each authorized evaluator for each student/stage. Example stage values are D1, D2, D3, D4, D5, D6. Use the evaluator's actual authorized email. Schedule fields may be blank for a controlled local test; if supplied they need full ISO timestamps with time zones.

Then select Evaluation workbook and upload an `.xlsx` export containing the raw D1–D6 response tabs. The parser reads the original tab/header schema. It does not require Excel installed on the portal machine. Your local workbook is not modified.

Read Import history. Accepted means an evaluation was admitted, Held means a change needs review, and Issues means missing/ambiguous data prevented import. Shared evaluator emails in the earlier test workbook will be flagged; do not invent accounts to silence those issues.

## 16 Connect Google Sheets later

Excel uploads work without Google authentication. For a direct Google read, university IT must provision a read-only server credential and viewer access to the verified workbook.

After receiving that authorized credential file through a secure channel, keep it outside the repository. In the CMD that starts the portal, set its actual paths/ID:

```bat
set "GOOGLE_APPLICATION_CREDENTIALS=C:\PRIVATE-LOCATION\university-google-credential.json"
set "GOOGLE_WORKBOOK_ID=YOUR_VERIFIED_WORKBOOK_ID"
```

Restart the portal. Data connections then provides Read Google Sheets. This is a manual read, not an automatic scheduled sync. Never paste private credential JSON into chat or commit it to Git.

See `integrations\README.md` for the signed n8n alternative. Do not connect a live sidecar until its isolated tests pass.

## 17 Stop and restart safely

Press Ctrl+C in the portal's CMD to stop the development server. The local database remains saved. Your other n8n process is separate.

To restart later:

```bat
cd /d "D:\ALL PROJECTS\OBE-TraceX"
set "SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe"
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Set Google variables again only if using that connection. Do not run migrations or create accounts every time; those are needed for initial setup or after an update introduces migrations.

## 18 Update and verify

Stop the server and preserve a private backup of your local database before updates.

```bat
git status
git pull --ff-only
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test evaluations
```

Restart the server. Tests use an isolated test database, not your live n8n database. SQLite local success is not a substitute for PostgreSQL staging tests.

## 19 NED server deployment

Docker is not needed for your laptop demonstration. It is one proposed deployment method for IT, with PostgreSQL, a production application server, HTTPS reverse proxy, private credentials, MFA, backups and monitoring.

Follow `docs\DEPLOYMENT.md` only after IT confirms its environment. This repository has not been deployed to NED. Live adoption also requires historical reconciliation, form settings review, exact-template acceptance and institutional ownership of the Google/n8n connections.

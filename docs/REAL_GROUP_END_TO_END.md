# Connect the Existing Master Workbook and Test One Real Group

## Corrected architecture

Google Forms → existing response tabs → existing spreadsheet formulas → D7 consolidated results.

The same workbook feeds two outputs: existing n8n individual reports, and OBE-TraceX official group documents. The portal now imports the existing D7 marks rather than requiring a second set of evaluator submissions. It preserves D7's reported final total, including source whole-total rounding. Source disagreements are flagged; the portal does not repair Excel formulas or silently substitute another mark.

D7 alone contains six stage totals, not every criterion required on D1–D6. Therefore the reader also imports the existing D1/D3/D5/D6 averaged criterion tabs. D2/D4 have no equivalent averaged tabs in the supplied workbook, so their supervisor response details are read to populate and cross-check criteria. A mismatch or ambiguous repeated supervisor response blocks the affected official report until the source is reconciled. The original workbook remains unchanged.

## Why PostgreSQL exists

Excel/Google Sheets remains the source of marks. PostgreSQL stores portal logins, the official group roster, imports, frozen copies, approvals and audit records. It prevents conflicting approval operations when both staff members use the system. It is not a new grading spreadsheet.

For a first laptop test, SQLite is already configured: run the migration command and no PostgreSQL installation is needed. For the NED server, use PostgreSQL and the supplied deployment runbook.

## PostgreSQL setup with Docker Desktop on a test laptop

Docker is optional for local development. If installed and running, create a dedicated local test database. Choose a private database password yourself:

```bat
docker run --name obe-postgres -e POSTGRES_DB=obe_tracex -e POSTGRES_USER=obe_portal -e POSTGRES_PASSWORD=YOUR_PRIVATE_DATABASE_PASSWORD -p 127.0.0.1:5432:5432 -v obe_pgdata:/var/lib/postgresql/data -d postgres:16-bookworm
set "POSTGRES_HOST=127.0.0.1"
set "POSTGRES_DB=obe_tracex"
set "POSTGRES_USER=obe_portal"
set "POSTGRES_PASSWORD=YOUR_PRIVATE_DATABASE_PASSWORD"
.venv\Scripts\python.exe manage.py migrate
```

Run these settings in the same CMD window that starts the portal. This is a different database from local.sqlite3; create the authorized portal accounts in it using provision_account. Database credentials are distinct from Coordinator/HOD login passwords. Never use the placeholder password literally or commit credentials. Avoid entering secrets into a shared terminal. If Docker is not supported by NED IT, they can provision an ordinary PostgreSQL service instead.

## What a live Google connection means

The running application needs its own authorized connection. A Google Drive connection in ChatGPT does not automatically grant your laptop application access.

University IT should create a Google Cloud service account, enable Google Sheets API, and give that identity viewer access only to the intended test workbook. Keep its credential JSON outside the repository. These steps require the account owner/IT to grant that access; this development has not done so.

In the CMD window that starts the portal, set:

```bat
set "GOOGLE_APPLICATION_CREDENTIALS=C:\PRIVATE-LOCATION\google-reader.json"
set "GOOGLE_WORKBOOK_ID=YOUR_TEST_WORKBOOK_ID"
```

Restart the portal. The Coordinator can use Data connections → Read Google Sheets. The reader requests only spreadsheet read access and includes D7 and supporting criterion tabs. It does not require a Google Sheets write permission.

For unattended synchronization, run this in a second CMD window with the same Google/database variables:

```bat
.venv\Scripts\python.exe manage.py sync_master --session "YOUR SESSION LABEL" --coordinator coordinator --watch --interval 60
```

Keep the process running; press Ctrl+C to stop. On NED, IT should supervise it as a service. Failed reads are retried and reported; a failed read is not a successful sync. Browser pages need refreshing to show the latest read. The existing n8n process remains separate.

## One-group test using actual historical data

1. Obtain permission to use one historical group's existing records. Use all its actual members, official project title/ID and known approved results. Do not invent marks.
2. Preserve the working workbook and seven workflow exports. Make an isolated TEST copy of the workbook. If replaying form submissions, use TEST form copies explicitly connected to that TEST workbook. Do not submit repeated historical marks into the working live source.
3. Identify the six actual form URLs and their destination tabs. The Forms homepage and the screenshots containing original/copied forms cannot establish which six are authoritative.
4. Create a separate portal session. Import the official group roster with seat,name,project_id,project_title,expected_members,attempt. The master-workbook path does not require re-entering evaluator assignments into the portal.
5. Point the read-only Google connection to the TEST workbook. Alternatively, upload its XLSX export first to verify extraction without setting up Google credentials.
6. Enter the actual approved historical assessments through the corresponding TEST forms. After each submission verify: the response row arrived, the existing formulas updated the averaged tabs and D7, and any TEST n8n workflow used the TEST destination/recipient. Existing release checkbox requirements still apply.
7. Run Read Google Sheets, or let sync_master perform its next read. Verify every student's imported stage total against the same D7 row. Confirm that form name/project spelling variations map through the official seat roster.
8. Review discrepancies in Import history. For the supplied older workbook, D4's unequal weighting and some repeated supervisor test responses require reconciliation. Do not delete a response or change a formula just to make the test pass. Obtain the approved correction and retain evidence.
9. After all six stages and criterion details are complete, the Coordinator reviews/freezes the group stages. The Coordinator approves the final result and exact original-template versions; the HOD can review and download.
10. Download the group's D1–D7 Word/PDF outputs. Compare every seat, official name, group ID/title, criterion, stage total, final total, QEC reference, signature area and page boundary with the approved sources. Supplementary blank evaluator masters are retained; signatures are not invented.
11. Change one response in the TEST source through an approved correction. Check that the working sheet updates while an already frozen portal result remains protected. Reopen through the Coordinator process, reread, review and reapprove. Verify the historical approval remains in history.
12. Record expected/actual marks and results. This is the evidence needed to claim that one whole group passed end-to-end. No such live one-group run has been claimed or completed by the code changes alone.

## Design references and identity

The interface uses an original dimensional purple/navy/cyan design, layered animated stage cards, reduced-motion support, the supplied unchanged NED emblem, and an original vector OBE-TraceX mark. PNG/ICO assets and social metadata are provided. The Framer education catalogue and SVGator examples were reviewed as design references. This is a self-hosted Django interface; it has not been imported into, purchased from, or published as a Framer template.

Social preview images need a public HTTPS deployment reachable by the sharing service. A localhost URL cannot provide a public preview. Private student data is not included in the share image, and authenticated pages remain marked noindex.

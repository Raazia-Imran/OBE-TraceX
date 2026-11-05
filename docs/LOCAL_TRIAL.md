# Local trial setup and current roles

SQLite is used for the laptop trial. The portal database is local.sqlite3 and is separate from n8n's database and the master workbook. PostgreSQL is not required to run this trial; revisit it with NED IT for production concurrency and backups.

Coordinator: manage sessions, imports, corrections, stage and final freezing, reopening, template verification and downloads. HOD: view records/history and download approved documents. Both can change their own passwords. Earlier documents assigning final approval to the HOD are superseded by this role policy requested on 5 November 2026.

Double-click Start Portal.cmd, then open http://127.0.0.1:8000. Double-click View Database.cmd to inspect the SQLite records in a read-only desktop window. Account password hashes/MFA secrets are excluded from that viewer. No synthetic students are required.

Accounts use usernames for login. An email can be recorded later; email-based login/reset is not configured. Initial passwords are private local setup values; use Account security to replace them with individual passwords. No password should be posted in chat or Git.

The local launcher enables a Microsoft Word PDF fallback if LibreOffice is absent. This uses the installed desktop Word for the laptop trial; use the supported LibreOffice/server rendering path on NED's deployment.

The full live Google read still needs an authorized source connection, either a university read-only credential or a separately verified bridge through existing n8n authentication. A shared file in ChatGPT is not itself an application credential. The source workbook must never be made public to work around authentication.

## Existing n8n connection on this laptop

The local setup can reuse the Google authorization already stored inside n8n. The separate inactive workflow `OBE-TraceX read-only master connection` contains only a manual start and a Google Sheets HTTP GET. It never calls email nodes or writes to Sheets. The portal runs this reader when **Read Google Sheets** is clicked; this does not execute the seven grading workflows. n8n keeps the Google tokens, and the portal receives worksheet values only. The credential itself may have broader permissions from existing n8n use; the reader's operation is GET-only.

`private-data/connection.cmd` configures the workbook and local reader. Do not publish this folder. No public spreadsheet link is required. If authorization expires, reconnect the existing Google credential in n8n and retry. A failed read never imports the previous snapshot as a new successful synchronization.

Clicking Read Google Sheets performs one fresh read. Continuous synchronization requires the separate `sync_master --watch` process described in REAL_GROUP_END_TO_END.md; a browser refresh alone does not fetch Google. Register the real session and official seat/group roster before reading student marks. Initial local usernames are `coordinator` and `hod`; their generated passwords are in the private local LOCAL-LOGIN.txt file. Open each in separate browser profiles or use an Incognito window to test both roles simultaneously.

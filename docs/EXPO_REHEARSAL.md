# Mid evaluation rehearsal
Real faculty roster and marks remain in a separate reference session. Workbook reconciliation holds are intentional and do not change source grades.
Use the Rehearsal session to demonstrate submissions, held corrections, freezing and final approval. Its criterion scores are generated for demonstration, not faculty results.
Evaluator access: authorize/revoke emails per group and stage; windows are enforced at ingestion. Reopen frozen groups before changing assignments. Existing revisions remain auditable.
Configure six canonical Form responder URLs/editor IDs under Evaluator access. OBE_GOOGLE_ACCESS_TOKEN_FILE must point to a private authorized-user Google token with Drive permission scope and Form ownership access. Restrict Google respondent general access before syncing. The portal only modifies published respondent permissions, never file editor/workbook permissions. No notifications are sent.
Google master reads are manual on demand, not automatic realtime synchronization. The local launcher loads private-data/connection.cmd. Offline faculty snapshots are explicitly recorded as saved-source imports.
Rounding/D4 reconciliation and faculty template approval remain required for official exports. Use preview documents during rehearsal.

## Start on this laptop
Run Start Expo Portal.cmd from the project folder D:/ALL PROJECTS/OBE-TraceX.
The launcher uses private-data/expo.sqlite3, a separate local database copy. Original account passwords are unchanged. If the server is already running, open http://127.0.0.1:8000/?session=3 directly.
- Session 2: Faculty reference: 3 groups, 10 students, exact saved workbook names, criterion details and reported marks. Official rounding confirmation remains pending.
- Session 3: Rehearsal: copies of those names with explicitly generated evaluations. Cognitia final approved; Scholar Sphere three stages frozen and one correction pending; InsightChat incomplete.
- Session 4: Live Google pilot: refreshed Google source is separate. Only Ahmed's row matched; missing rows and D4 detail remain validation issues.
- Legacy synthetic session is retained; excluded from the default overview.

## Suggested walkthrough
1. Open Overview with session 3. Show populated progress and audit activity.
2. Open Cognitia to show all frozen stages and the final consolidated result.
3. Download the labelled D7 preview as Word or PDF.
4. Open Scholar Sphere and Correction review to explain held changes.
5. Open InsightChat to explain why missing evaluations block freezing.
6. Open Evaluator access. Assign a rehearsal email to InsightChat D6, then revoke it.
7. Open session 2 to compare the actual faculty marks.
8. Open Data connections, select session 4 and use Read Google Sheets for a live read if connected. Reads are manual, not background realtime polling.

## Verification
57 automated tests passed. Browser walkthrough covered the overview, sessions, imports, evaluator access, corrections, audit, templates and group view; grant/revoke actions and D7 Word/PDF downloads succeeded with no JavaScript page errors.
The document-download loading overlay was fixed after browser verification found it blocking the next action.
The six canonical Google Form IDs/respondent links and an owner-authorized Google token with Drive and Forms permissions remain required for live respondent enforcement. No new Google Form restrictions have been claimed as verified, no evaluation workflow was activated and no official template approval was fabricated.

# OBE TraceX change log and validation

## Changes on 24 November 2026

The user requested removal of unnecessary dashboard text, repository updates, complete multi-file documentation and collection of project media for teammate/AI continuity.

This delivery:

- Replaced promotional page headlines with direct task labels across overview, imports, sessions, group, reports, templates, corrections and history.
- Removed the overview promotional hero and routine recent-activity sidebar. Activity records remain available in Activity history.
- Removed the misleading linear pipeline graphic from Integration hub and documented the actual parallel workbook/report paths.
- Made the worker status distinguish no completed read from an actual successful read.
- Changed report-archive copy to describe saved items rather than imply all live reports are already connected.
- Clarified master-workbook import instructions and moved detailed policy/hash information into expandable sections.
- Corrected stale HOD reopening/policy messages to Coordinator, consistent with server permissions.
- Scoped the overview's pending raw-response correction count to the displayed groups/session/search.
- Added current handover Markdown, configuration/mapping/acceptance templates, PDF and editable reading copy, asset inventory and private local backups.

No schema migration is introduced. Code behavior changes are limited to the displayed correction count scope and truthful connection/status text. Original source calculations, Google permissions, live workflow state and report-template bytes are preserved.

## Validation and evidence

67 automated Django tests passed on the isolated SQLite test database on 24 November 2026. Django system checks, migration drift checks and git diff --check also passed. PostgreSQL was not exercised during this run.

Use `08_Evidence/validation.txt` and the release receipt in the delivered pack for the actual commands, test count, source revision and publication result. Do not quote older 33/47-test claims as validation of this change.

The repository CI requires Django system checks, migration drift checks and automated evaluations tests; these checks are run on an isolated local test database for this delivery. A visual sample of the populated overview is inspected. The generated handover Word/PDF is rendered and reviewed for layout.

No fresh live Google submission/read, email delivery, Google allowlist grant, full historical replay or department production deployment is included in these checks. PostgreSQL CI results, actual faculty/template sign-off and a restore drill remain release acceptance work.

## Maintaining this pack

After every substantive continuation, record the date, exact source revision, changed files, expected/actual result and remaining blockers. Replace stale status tables rather than appending contradictory green claims. Keep evidence labels explicit: VERIFIED FROM CURRENT FILE, VERIFIED FROM REPOSITORY, USER-PROVIDED NOTE, INFERENCE or UNRESOLVED.

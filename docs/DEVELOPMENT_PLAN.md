# OBE-TraceX Development Plan

**Workflow correction:** Use [the current real-group integration guide](REAL_GROUP_END_TO_END.md). The primary importer now reads the existing D7 master totals and supporting criterion tabs; re-entering evaluator assignments or regrading raw submissions is not required for this route. Older raw-event/demo sections below describe the optional legacy path.

## Purpose and confirmed requirements

Extend Raazia's tested assessment automation into a department-owned portal. Preserve the six forms, raw response history, master workbook and seven n8n workflows. Keep individual n8n reports as additional summaries. Create official group-based D1–D7 documents from the supplied original layouts after all evaluations and final approvals are complete.

Rameen's FYDP_STRATEGY is the requirements starting point: group consolidation, controlled corrections, centralized management, traceable assignments, schedules, reports and role-based security. Raazia subsequently specified Coordinator and HOD access, final group QEC documents, stage/result freezing, a Python or JavaScript implementation, a polished accessible interface, and eventual NED server deployment. These later requirements take precedence over the strategy's proposed Apps Script stack and additional evaluator dashboards. Forms remain the evaluator interface in this release.

## Selected implementation

- Python Django 5.2 LTS for application, authentication, permissions, server-side validation and transactional workflows.
- Server-rendered HTML/CSS with small JavaScript enhancements. No mandatory Node build or separate frontend API is needed to run this pilot.
- PostgreSQL for production consistency and row locking. SQLite only for local testing.
- Read-only Google Sheets API connection and XLSX upload adapter into a separate portal database.
- Existing n8n reporting continues independently; optional signed events can feed portal assessments after isolated testing.
- Original Word templates populated by field mapping, followed by local LibreOffice PDF rendering. No re-created HTML approximation of the official forms.
- Docker Compose packages the portal, PostgreSQL and reverse proxy. The existing n8n instance is not migrated or enabled by this repository.

This stack preserves Rameen's functional proposal while fitting a university-owned Python server. Apps Script remains an alternative if IT later mandates Google-only hosting; that would be a separate architecture decision.

## Roles and authority

| Action | Coordinator | HOD |
|---|---|---|
| View groups, results, reports and history | Yes | Yes |
| Create session / import official roster | Yes | View |
| Assign evaluators and evaluation periods | Yes | View |
| Import/read evaluations | Yes | View |
| Review held corrections | Yes, after reopening if frozen | View |
| Approve academic rules and rounding | View | Yes |
| Freeze each complete rubric stage | Yes | View |
| Approve/freeze final group results | View | Yes |
| Reopen a frozen stage with a reason | No | Yes |
| Verify official template version | View | Yes |
| Export approved group records | Yes | Yes |
| Provision/recover accounts | University IT terminal | University IT terminal |

This is an implemented proposed policy for faculty confirmation, not evidence of an existing signed departmental approval. Each session begins with rules unapproved.

## Data identity

Use seat number to link a response to the official student roster, normalize letters to uppercase and trim whitespace, and retain source response identity separately. The format `AA-00000` detects malformed values; a roster lookup prevents a valid-looking number belonging to someone else.

An academic record belongs to session + student + project attempt. An evaluation belongs to that student record + rubric + assigned evaluator. A revision belongs to that evaluation. A project group provides official ID, title and expected membership. Name/project spelling variations in form responses do not define identity or overwrite official roster values.

Imported response project IDs are not used as the matching key. The official roster is authoritative. Repeated academic attempts require explicit assignments; ambiguous workbook histories are held rather than combined.

## Calculation rules and faculty decisions

| Rubric | Criterion maxima | Stage maximum |
|---|---|---:|
| D1 | 3, 3, 3, 3 | 12 |
| D2 | 5, 5, 5, 5 | 20 |
| D3 | 12, 12, 12, 12 | 48 |
| D4 | 16, 8, 8, 8, 8 | 48 |
| D5 | 4, 4, 4, 4, 4, 4, 4, 4 | 32 |
| D6 | 8, 8, 8, 8, 8 | 40 |
| D7 | Six stage totals | 200 |

Criterion earned marks = approved percentage × criterion maximum / 100. Average eligible evaluator marks per criterion, then sum criteria. The pilot supports equal weighting of assigned evaluators. Any role-specific weights need a revised approved ruleset and tests.

Preserve Decimal calculation precision; display two decimals with half-up rounding. Faculty must confirm whether official totals instead require whole marks and at which point rounding occurs. The session approval explicitly records this decision. Do not reapply final percentage weights to stage marks that are already scaled.

D4 timely report submission is binary (0/100%). Missing or invalid criteria cannot become ordinary assessed zero. A stage cannot freeze until every registered student has every assigned evaluation, and pending corrections have been resolved.

The originals label some criterion subheaders as PLO percentages while their headings show mark maxima. Confirm whether populated cells contain earned criterion marks or attainment percentages. The pilot maps earned marks; do not approve a template before faculty confirms those units.

## Freeze and correction lifecycle

1. A signed event or source read is matched to an existing assignment and validated.
2. An identical response replay produces no new score. A first valid response is accepted if its schedule permits.
3. A changed response, a late response, or a response to a frozen stage is held as a pending change.
4. Coordinator records approval/rejection of a correction. A frozen stage must first be reopened by the HOD.
5. Coordinator reviews a complete group stage and freezes a snapshot with its hash, revision IDs, actor and time.
6. Later source edits cannot overwrite this snapshot. The review-version check rejects stale approvals.
7. HOD final approval requires six active stage snapshots, matching roster identities and no unresolved changes.
8. Reopening preserves previous snapshots and supersedes any active final result. It never erases historical results.
9. New correction decisions require new stage and final approvals before official exports become available again.

Production row locking is provided by PostgreSQL. A normal spreadsheet checkbox is not used as the authoritative freeze lock. Group stages can be frozen separately; cohort-wide one-click moderation/freeze requires an explicit faculty decision and is listed as follow-up work.

## Synchronization ownership

| Information | Authority | Direction |
|---|---|---|
| Submitted assessment | Forms response source | Sheets → portal read/import |
| Official student/group identity | Approved roster | Coordinator → portal |
| Assigned evaluator/session window | Approved assignment register | Coordinator → portal |
| Unapproved calculation | Portal's validated rubric rules | Responses → calculated preview |
| Frozen/final result | Approved portal snapshot | Snapshot → official reports |
| Individual n8n HTML report | Existing n8n pipeline | Existing workflow unchanged |
| Official QEC group report | Verified original template + final snapshot | Portal → Word/PDF download |

This is controlled synchronization, not uncontrolled bidirectional spreadsheet editing. The pilot supplies manual Google reads, workbook imports and a signed n8n receiver. Automatic scheduled reads, production n8n event delivery, and report-link writeback remain integration work. No credentials are bound or live sheet cells changed by this development session.

## Implementation phases

| Phase | Deliverables | Exit evidence | Current state |
|---|---|---|---|
| 0 Baseline preservation | Inventory, source hashes, approved original templates, separation of private workbooks | Original hashes unchanged | Implemented |
| 1 Secure portal foundation | Accounts, two roles, MFA, session protection, responsive interface, audit events | Permission/authentication/security tests | Implemented locally |
| 2 Roster and source integration | Session setup, CSV roster/assignments, XLSX and Google read adapters, signed event contract | Synthetic import and replay tests; live connection review | Local adapter implemented; live setup pending |
| 3 Approval workflow | Complete-stage validation, correction queue, stage snapshots, HOD final freeze/reopen | Missing/duplicate/stale/frozen-change tests | Implemented locally |
| 4 Official documents | Original-template population, Word/PDF downloads, template verification gate | Structural preservation tests and rendered samples | Implemented; faculty/Word visual acceptance pending |
| 5 Reconcile existing system | Historical full-group comparison, D4 discrepancy resolution, QEC removal from individual report copies | Independent expected/actual register and reviewed n8n copies | Pending |
| 6 Department staging | PostgreSQL concurrency tests, live Google account binding, scheduled sync policy, account ownership, backup/restore | Staging run and restored system | Pending IT information |
| 7 Pilot and launch | Controlled defense session, faculty UAT, security review, handover and cutover | Coordinator/HOD/IT acceptance | Pending |

## Detailed remaining work before next year's live use

1. Identify the six actual production form URLs. The screenshots show original and copied forms; the Forms home URL is not a unique form reference.
2. Inspect required fields, collected identity, edit response behavior, response destinations and school account restrictions. Test edited responses rather than relying on timestamps alone.
3. Resolve historical test submissions made with one shared email but different evaluator names. Do not invent separate verified evaluator accounts from display names.
4. Obtain official roster, project titles, supervisor/evaluator assignments, academic session and course code.
5. Reconcile all students in a known historical group criterion by criterion. Include an uneven D4 case, zero, missing and corrected response scenarios.
6. Confirm session policy: rounding, evaluator eligibility/weights, correction authority, moderation meaning, group size and whole-cohort controls.
7. Make separate inactive copies of the seven n8n workflows, remove QEC references from individual summaries, retain safe filenames/seat association, and test two students together. Never patch the existing live workflows blindly.
8. Compare all populated official templates with the supplied originals in Word and the target PDF renderer. Include long names/titles, 1–4 members, page boundaries, signatures, original artwork and reference numbers.
9. Agree report distribution and retention. The portal downloads private reports; automatic Drive archiving, expiry/retention and scheduled exports require a separate approved connection.
10. Bind Google/n8n under department ownership with no personal student account dependency. Configure the signed event secret outside source control.
11. Decide and implement scheduled synchronization frequency/alerts. The local pilot's manual synchronization does not imply unattended production sync is running.
12. Validate NED server OS, resources, domain, HTTPS, network access, storage, LibreOffice/fonts, supported PostgreSQL and service ownership.
13. Run concurrency, failure/retry, permission, restore and acceptance tests in PostgreSQL staging.
14. Freeze migration scope, back up n8n database + encryption key, avoid overlapping senders, and run one controlled session before wider adoption.

## UI direction

An emerald/ivory academic workspace with restrained lime accents, readable tables, clear approval statuses, short optional splash animation and separate role actions. Mobile navigation is accessible, reduced-motion preferences are respected, and success is shown only after a server result. No placeholder student names or fake statistics appear in an empty real workspace.

## Security and operational design

No public registration or hardcoded passwords. Passwords use Argon2id, with minimum-length and common-password checks. Database-backed sessions expire after inactivity and at browser close. Login throttles are stored in the database. TOTP secrets are encrypted using a separate server key; production refuses sign-in for accounts without enrollment.

CSRF protects browser mutations; POST is required for approvals and exports. The signed n8n endpoint has its own HMAC authentication, freshness check and replay record. Server permissions are checked for actions, not only hidden UI buttons. Security headers, private no-store responses and production HTTPS settings are included.

Audit history is application append-only; a database administrator can still change storage. A production security review must consider DB permissions, off-host log retention and tamper evidence. Do not describe this pilot as a compliance certificate or promise zero defects.

## Official technical references

- Django deployment checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Django password management: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/
- Google Sheets values batchGet: https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGet

These references support implementation choices; departmental approval governs academic rules and document acceptance.

The official group summary table is populated. Supplementary evaluator rubric pages are retained as blank masters; the portal does not fabricate completed evaluator forms or signatures.

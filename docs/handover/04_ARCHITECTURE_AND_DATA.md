# OBE TraceX architecture and data

## Source map

[VERIFIED FROM REPOSITORY] Django serves HTML templates with progressive JavaScript. The repository pins Django 5.2.19 in requirements; CI targets Python 3.12. Do not infer dependency security or upgrade compatibility from these pins. SQLite is for the existing laptop; PostgreSQL is required by production settings.

| File or directory | Responsibility |
|---|---|
| config/settings.py | Database choice, secrets, auth, security and timezone Asia/Karachi |
| config/urls.py | UI and integration route definitions |
| evaluations/models.py | Accounts, sessions, roster, imports, results and document storage |
| evaluations/rubrics.py | Stage maxima, criterion weights, seat validation and decimal display |
| evaluations/importers.py | Roster/assignment imports and legacy raw-response parsing |
| evaluations/master_sync.py | Primary calculated workbook reconciliation |
| evaluations/google_sync.py | Fresh direct Google read or private n8n bridge |
| evaluations/services.py | Role enforcement, revisions, freeze/reopen and final approval |
| evaluations/access.py | Form links, evaluator grants/revokes and respondent sync |
| evaluations/archive.py | Saved reports, signed report receiver and reference comparison |
| evaluations/reports.py | Original-template Word population and PDF rendering |
| evaluations/previews.py | Nonofficial preview generation |
| evaluations/views.py | Login and main workflow views, import and evaluation endpoint |
| evaluations/templates | Dashboard and workspace page wording/layout |
| evaluations/static | Branding, CSS, animations and portal revision polling |
| tools/launch_workspace.py | Existing local launch and configured worker startup |
| report_templates | Seven preserved original DOCX rubric templates |
| integrations/n8n | Evaluation/report signing fragments |
| media-src | Editable promo renderer and wordmark generator |
| docs | Earlier development, deployment, acceptance and run guides |

## Data model

AcademicSession identifies the academic cycle and approved rules. ProjectGroup belongs to a session and attempt. Student links official seat/name to a group and session. The import roster schema is `seat,name,project_id,project_title,expected_members,attempt`; canonical seat format is AA-00000, for example the synthetic seat SE-99001.

Assignment ties an evaluator email and stage/window to one student. Evaluation stores revisioned raw-event criterion marks. PendingChange stores held raw corrections. This path is optional: master imports use MasterRecord and do not require evaluator re-entry.

MasterRecord stores imported stage criteria, D7 final value, source digest and errors per student. ImportBatch records import summaries. FrozenResult stores immutable approval snapshots; reopening supersedes the active snapshot without deleting history. TemplateApproval binds verification to exact source bytes. Report stores export metadata, while StoredDocument stores downloadable binary content and its hash. StageForm stores per-session Form links and last allowlist verification timestamp. SyncState records background read attempts, success, errors and lease. AuditEvent records actions retained in the dedicated history page.

## Marks and approval rules

| Stage | Criterion maxima | Total |
|---|---|---:|
| D1 | 3, 3, 3, 3 | 12 |
| D2 | 5, 5, 5, 5 | 20 |
| D3 | 12, 12, 12, 12 | 48 |
| D4 | 16, 8, 8, 8, 8 | 48 |
| D5 | Eight criteria at 4 | 32 |
| D6 | Five criteria at 8 | 40 |
| Final | Sum of six stage maxima | 200 |

Decimal arithmetic is used; display uses two decimals with half-up rounding. The master path preserves a reported D7 final total that agrees either with exact stage sums within 0.005 or with whole-total half-up rounding. There is no automatic conversion from 200 to 100. Department approval is still needed for the intended official rounding/units policy.

For D2 and D4, repeated supervisor response rows are ambiguous and block affected report criteria. Missing or duplicate consolidated rows invalidate freshness rather than silently leaving an old mark looking current. Criterion totals must reconcile within 0.005. A final frozen group is held on import until Coordinator reopening. Changes conflicting with a frozen stage produce review errors; the original frozen result remains unchanged.

Do not confuse raw response corrections with master-workbook reconciliation errors: the first uses PendingChange and Correction review; the second appears in import/workbook issues. A dashboard raw-correction count is not the number of all workbook discrepancies.

## Roles enforced by the current code

| Action | Coordinator | HOD |
|---|---|---|
| View records, history, archive | Yes | Yes |
| Import data or read Google | Yes | No |
| Manage Forms and evaluators | Yes | No |
| Approve session policy and templates | Yes | No |
| Freeze, reopen and approve final | Yes | No |
| Download authorized reports | Yes | Yes |
| Change own password/profile | Yes | Yes |

Faculty sign-off remains an academic responsibility outside a code permission check. Do not expand HOD write rights to match an older PDF.

## Routes and integration contracts

| Route | Purpose |
|---|---|
| /login/ | Direct sign-in |
| / | Overview after intro/login routing |
| /sessions/ | Academic cycles and policy |
| /imports/ | Source import and validation history |
| /evaluators/ | Coordinator Form/evaluator management |
| /connections/ | Saved Form links and worker read state |
| /workbook/ | Imported marks |
| /comparison/ | Saved faculty-reference comparison |
| /documents/ | Stored document downloads |
| /templates/ | Original and approved template versions |
| /audit/ | Recorded activity |
| /healthz/ | Web process health; not Google/n8n connectivity proof |
| /workspace/state/ | Portal revision and worker states for UI polling |
| /integrations/n8n/evaluation/ | Optional signed raw-evaluation event |
| /integrations/n8n/report/ | Signed individual-report archive |

The optional raw-evaluation endpoint requires a UUID event_id, current issued_at, matching assignment/session/seat/attempt/stage/evaluator and a stable source_id. It returns accepted, unchanged or held. HMAC covers the exact raw UTF-8 JSON body. A changed serialization breaks the signature. Response identities and event identities have different purposes: do not replace a source response identity on every reread. See `integrations/README.md` for the full example and error statuses.

## Known implementation limitations

[UNRESOLVED] Browser state polling observes global audit revisions, so routine events can cause refreshes. The current change removes routine logs from the overview but does not redesign global polling.

[UNRESOLVED] Database viewer targets local.sqlite3 while active settings prefer real.sqlite3. Worker startup returns early if the web process is already healthy. Review these before relying on the desktop tools as monitoring.

[UNRESOLVED] Form permission sync has no automatic schedule for future evaluation windows and an allowlist timestamp is not continuous external verification. Live corrected responses still need tested ownership/routing policies.

[UNRESOLVED] Final snapshot metadata uses a display-only rounding label even when a workbook whole-total is retained. Preserve actual values; review metadata clarity with faculty before institutional release.

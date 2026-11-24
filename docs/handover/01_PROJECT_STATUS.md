# OBE TraceX project status

## Purpose and success criteria

[VERIFIED FROM REPOSITORY] OBE-TraceX supports FYDP assessment in NED University of Engineering and Technology, Department of Software Engineering. It adds roster matching, review, frozen results and group D1–D7 documents to an existing Google Forms, Sheets and n8n process. The workbook remains the source of calculated marks.

Success means an authorized evaluator's submission reaches the correct response tab, calculations reconcile, the intended individual report is produced, the portal displays the same student and marks, and the Coordinator can approve and export the correct group documents. Department ownership, Google access and a recoverable server deployment are part of operational completion.

[USER-PROVIDED NOTE] Raazia has worked on this alone and now wants teammates and another AI to continue. Teammate names and formal responsibilities have not been provided for this project. Do not copy people or assignments from ReThread or other projects. No current submission deadline, page limit or new documentation template was supplied.

## Sources reviewed

| Source | Role and status |
|---|---|
| GitHub `Raazia-Imran/OBE-TraceX`, main | Code baseline `794d340d70fc1c02db382cef036ba1df5c33f874` before this delivery |
| Installed `D:\ALL PROJECTS\OBE-TraceX` | Same baseline commit; one untracked promo MP4 at initial inspection |
| `private-data/real.sqlite3` | Actual local workspace selected by settings/launcher when present |
| `D:\ALL PROJECTS\n8n dept automation` | Seven original workflow JSON exports and existing backup folders |
| Local n8n SQLite database | Read-only current workflow activation inventory |
| Earlier guides and media retrieved for OBE-TraceX | Historical documents and promotional assets; older status claims may be stale |
| Uploaded Pasted text.txt | General continuity requirements; its MMSL example does not define this project's facts |

[VERIFIED FROM CURRENT FILE] The read-only inventory of `real.sqlite3` on 24 November 2026 found the following. Counts are across both sessions; they do not mean a whole live group has passed.

| Record | Count |
|---|---:|
| Academic sessions | 2 |
| Groups | 6 |
| Students | 20 |
| Imported master records | 11 |
| Saved stage Forms | 6 |
| Forms with verified allowlist timestamp | 0 |
| Stored documents | 13 |
| Stored document kind preview | 13 |
| Frozen result records | 0 |
| Raw Evaluation records | 0 |

The 20 roster rows and 11 master records measure different tables. They must not be described as 20 fully evaluated students. Zero raw Evaluation records is compatible with the master-workbook import route. The saved documents are previews, so they are not evidence of official final exports or connected individual-report archiving.

## Implemented in source

[VERIFIED FROM REPOSITORY]

- Django login with Coordinator and HOD roles, password changes, throttling and optional MFA handling.
- Academic sessions, roster and assignment imports; no automatic synthetic student seeding.
- XLSX master import, Google read adapter and optional local n8n credential-preserving read bridge.
- Stage criteria and D7 reconciliation, missing/duplicate source detection and protected frozen records.
- Coordinator stage/final freeze, reopening and correction decisions, with version/history records.
- D1–D7 original Word templates, document generation, labelled previews and saved document downloads.
- Signed raw-evaluation and report-receiver endpoints, replay/integrity checks and archive storage.
- Form link management and a respondent allowlist adapter that refuses broad public/domain/group respondent access.
- Background workbook reader, UI polling, deployment configuration and media renderer source.

Implementation is evidence that code exists. It is not evidence of current Google authorization, successful production setup or faculty approval.

## Remaining work and blockers

[VERIFIED FROM CURRENT FILE] All seven grading workflows were inactive in the local n8n database at inspection. The manual read utility and archive acceptance workflow were also inactive; a manual utility can still be invoked by its CLI bridge while inactive. Activation state alone does not prove credential health.

[UNRESOLVED] Six Form records exist, but owner-verified Form title, destination and respondent controls are not established by those rows. No allowlist verification timestamp exists in the active real database. A fresh external Google read was not triggered during this documentation task.

[VERIFIED FROM REPOSITORY] `docs/CONNECTED_WORKSPACE.md` records a previous isolated report-archive acceptance test. The active real database currently contains only previews. That historical test must not be presented as all seven production archive branches being connected.

[UNRESOLVED] Full replay for the supplied three historical groups, disputed D4 weighting, repeated supervisor responses, final policy sign-off, individual-template QEC wording and institution deployment remain acceptance work. No actual live evaluation or email was submitted by this handover task.

## Superseded and conflicting material

- [VERIFIED FROM CURRENT FILE] The older setup PDF describes zero sessions/students and commit 492995a. The current inventory and newer source supersede those figures.
- [VERIFIED FROM REPOSITORY] Current server permissions give academic mutation rights to the Coordinator. HOD views/downloads. Older README/runbook text assigning final approval or reopening to the HOD is stale; prominent current text and related error messages were corrected in this delivery. Older documents remain historical.
- [UNRESOLVED] The historical test guide says QEC references were removed from individual reports, while repository integration notes still say this is pending. Preserve baseline exports and compare the canonical live workflow HTML before making a new claim.
- [USER-PROVIDED NOTE] Earlier conversation mentions 47 passing tests; repository VERIFICATION.md records 33 on 5 November. Neither is a current test count. Use the dated validation evidence delivered with this pack for this change.
- [INFERENCE] The user's spoken “Anytime” refers to n8n given the existing project. No separate Anytime product was configured.

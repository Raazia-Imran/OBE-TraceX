# OBE TraceX team and department roadmap

## People and proposed ownership

[USER-PROVIDED NOTE] Raazia is the existing maintainer and wants teammates to join. No named teammates, supervisor approval or department hosting owner were established in this session. The following allocation is a proposal, not an assigned commitment.

| Workstream | Proposed owner | First concrete output |
|---|---|---|
| Portal and document generation | Raazia with developer teammate | Reviewed UI change and one group's D1–D7 comparison |
| Forms, Sheets and n8n | Integration teammate with Google owner | Verified stage mapping and isolated replay evidence |
| Quality and documentation | Another teammate or rotating reviewer | Acceptance sheet with expected/actual values and defects |
| Academic policy and roster | Authorized Coordinator/faculty | Approved roster, criteria, rounding and correction decisions |
| Record review | HOD | Review/download acceptance under current permissions |
| Department infrastructure | Named IT owner | HTTPS staging, PostgreSQL, supervised workers and restore evidence |

Use feature branches and small pull requests. Agree ownership before simultaneous editing of the same file. Include the trigger, resulting behavior and validation in each change description. Share sanitized source and documentation first; provide private access only through the department's approved channels.

## Priority order

**Priority 1 — canonical data and access.** Confirm six canonical Form/destination pairs and all seven workflow targets. Decide owner accounts and fill the private mapping. Confirm the actual marking policy, especially D4 weights and repeated supervisor responses. Expected deliverable: an owner-reviewed map and unresolved-decision list.

**Priority 2 — isolated end-to-end test.** Connect TEST workbook reads, test allowed and denied respondents, replay one historical group, compare criteria/D7/portal and generate reports. Expected deliverable: completed acceptance CSV and private evidence with no unapproved live emails.

**Priority 3 — individual report archive.** Add/test a separate archive branch to copies of each canonical workflow, with stable retries and correct student/session mapping. Resolve QEC wording using actual canonical HTML. Expected deliverable: intended reports saved byte-for-byte and downloadable by the correct roles.

**Priority 4 — three-group acceptance.** Extend the same procedure across all historical groups. Resolve every discrepancy with faculty, then approve policy/templates/results through the current Coordinator flow. Expected deliverable: traceable expected/actual marks and report layout approval.

**Priority 5 — department staging and handover.** Provision PostgreSQL, HTTPS, private secrets, department Google ownership and supervised workers. Verify concurrency, backup/restore and failure recovery. Activate live senders only after designated owners approve the tested target/recipient configuration. Expected deliverable: staging sign-off and scheduled operating responsibility.

## Department questions that still need answers

- Who owns the Forms, workbook, Gmail sender, n8n credentials and server after student handover?
- Which six Form copies are authoritative and where does each submit responses?
- Which department decision resolves the D4 weighting and repeated supervisor responses?
- What is the approved treatment of whole-total rounding, missing submissions and retakes?
- Who can grant/respond/revoke access, and who closes Google Forms during stage freeze?
- Are individual summaries expected by email, archive, or both, and who authorizes recipients?
- Is any society connection actually required? The user's spoken department/society wording is unclear; no separate society system or API was identified.
- What are the retention period, backup destination, restore owner and university deployment hostname?

Continue independent code/document work without guessing these answers. No new Google token, institutional hostname or faculty decision has been invented.

## Acceptance evidence to retain

Record the environment, source revision, database/session, time in Asia/Karachi, expected result, actual result, evidence path, responsible reviewer and any approval reference. Never replace missing evidence with a green status label.

Required cases include: allowed evaluator, denied forwarded link, one correct stage submission, missing evaluation, duplicate/corrected supervisor input, exact criteria/D7 agreement, stale source read failure, concurrent approval/import, frozen-result correction, report hash/download, all seven template layouts and a real staging restore. Automated unit tests cover code paths; they do not replace these operational checks.

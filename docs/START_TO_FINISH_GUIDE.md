# OBE-TraceX From a Google Form to the Final Printed Record

This guide explains the working local pilot in simple English. It also identifies the connections that still need setup before real departmental use.

## 1 What you already have

You have six evaluation Google Forms, their response tabs in FYDP_Master_Database, calculations and averaged sheets, and seven n8n reporting workflows. These remain your existing system. This development did not rewrite, activate or delete those seven workflows or change your source workbook.

The new portal is a second application. It brings student identity, evaluation review, stage freezing, HOD approval and official group documents into one place. Its name is OBE-TraceX: Automated Outcome-Based Education Evaluation & Grading Portal.

Your laptop can run both applications:

| Application | Local address | Purpose |
|---|---|---|
| Existing n8n | http://localhost:5678 | Existing individual report automation |
| New portal | http://127.0.0.1:8000 | Coordinator/HOD management and official group documents |

Both must be running if you want both services available. Closing the portal does not delete n8n. Closing a CMD process stops the app running in that process, not the saved database.

## 2 Can the portal read the Excel/Google Sheet data?

**Yes.** The portal can read the six response tabs from an uploaded XLSX workbook. It can also read those same tabs directly from Google Sheets after a read-only server connection is configured.

It matches responses to an official student roster using seat number, and to an assigned evaluator using the evaluator email. It uses the approved rubric rules to calculate the marks. It does not blindly copy every displayed final total from D7, because D7's current D4 formula has a known weighting discrepancy.

There are three integration routes:

| Route | What you do | What is ready now |
|---|---|---|
| Excel upload | Download a workbook copy and upload it in Data connections | Implemented; no Google credential needed |
| Google Sheets read | Click Read Google Sheets after IT configures the connection | Adapter implemented; live credentials not configured |
| Signed n8n events | A separate tested sidecar sends normalized assessment events | Receiver/signing example implemented; live sidecar not configured |

The pilot does not continuously monitor your Google account by itself. Uploading a workbook is a snapshot. A Google read fetches the source at that time. Automatic scheduled reads remain a deployment/integration step. Your existing n8n automation remains independent.

## 3 Before a real evaluation session

The Coordinator creates an academic session, for example the official academic year/defense cycle. Enter the actual course code.

The Coordinator imports the official roster. Each student has an approved name, seat number, project ID/title, expected group size and attempt number. Form-entered name spelling does not replace this official name.

The Coordinator imports evaluator assignments. These say who may assess each student for each rubric. Optional opening/closing times describe the allowed evaluation window. The portal enforces its acceptance rules; it does not automatically close Google Forms themselves.

The HOD reviews the proposed academic policy. The current pilot uses the supplied criterion weights, equal weighting across assigned evaluators, full precision during calculations and two decimal places on display. Do not approve this for a real session until Miss confirms rounding and the units in the original template's criterion cells.

## 4 When an evaluator fills a Google Form

Consider student SE-24001 in project FYDP-01.

1. An assigned evaluator opens the appropriate actual Google Form, such as D1 proposal.
2. They enter the student identity and choose the rubric levels.
3. Google Forms saves a response in its linked response tab.
4. The existing workbook/n8n pipeline continues according to its saved configuration. Its existing release checkbox or trigger rules still apply; the portal does not press those checkboxes.
5. The Coordinator uploads the latest XLSX or performs a configured Google read. Alternatively, a future live sidecar sends a signed event.
6. The portal checks the seat's format and roster membership. `se-24001` is normalized to `SE-24001`. A different valid seat number still has to belong to the roster; a format rule alone cannot prevent every wrong student selection.
7. The portal checks that this evaluator is assigned to this student and this rubric. An editable evaluator name alone is insufficient.
8. A valid first response is accepted. Missing, malformed or unassigned data is rejected with an issue. A duplicate/shared evaluator identity needs review.
9. The dashboard can show the accepted result. It remains unapproved until the required review/freeze steps occur.

A name such as Ahmed, ahmed or a misspelled name in the form does not create a different student when the seat matches. The report uses the official roster identity and group information.

## 5 When several evaluators mark one student

D1, D3, D5 and D6 can have multiple assigned evaluators. Each contributes once through the assignment/revision record. The portal averages earned marks criterion by criterion.

For a criterion out of 3, one evaluator choosing 100% gives 3 marks and another choosing 50% gives 1.5. Their average is 2.25. Different stages use their own criterion maxima.

The portal waits for all assigned evaluations before allowing a group stage to freeze. A student with one missing evaluation does not silently receive zero.

Your older tests used one Google account to submit on behalf of several evaluator names. That is useful for calculation experiments, but production evaluator identity needs separate verified accounts or an approved mapping. The importer flags repeated evaluator email/seat combinations rather than giving that account extra influence.

## 6 What the Coordinator reviews and freezes

The Coordinator opens a project group from Overview. Each D1–D6 card shows the student result, evaluator count and anything blocking approval.

When the group is complete, the Coordinator enters a review reference and clicks Freeze for that stage. The portal stores an approved copy containing the group identity, official student names/seats, criterion marks, total, source revision references and approval history.

A source sheet edit after this point cannot silently replace that copy. If someone else changes the data while the review page is open, the portal rejects the stale approval and asks for a reload.

This pilot freezes a group stage at a time. A one-click whole-cohort moderation/freeze screen is not yet implemented. The precise moderation rules still need faculty confirmation.

## 7 What happens after an evaluator corrects a response

On the next import/read, the portal can detect changed data for an existing assigned evaluation. It holds the change instead of silently counting a second independent evaluator.

- Before freezing: the Coordinator can approve or reject the held correction with a reason.
- After freezing: the HOD first reopens the affected stage with a reason. The Coordinator then reviews the correction and freezes the replacement stage result.
- If a final result was already approved, reopening a stage supersedes that final approval. It must be approved again.

The earlier frozen result remains in history. The source Google Form edit link and its actual behavior still need inspection; a portal rule alone does not change Forms settings.

## 8 Final HOD approval

The Coordinator completes all six stage reviews. The HOD then reviews the group and approves its final result.

The pilot checks that all six stages are frozen, the roster agrees and no corrections remain unresolved. D7 adds D1–D6 to a maximum of 200. There is no hidden conversion to 100 marks.

The HOD's final approval creates a separate final snapshot. Official reports come from this snapshot and its linked approved stages, not from a sheet that may change later.

## 9 Official group QEC documents

Open QEC documents. Download the original template and a clearly labelled synthetic sample for comparison. Both roles can inspect them; only the HOD can record template verification.

The sample contains fake names and SAMPLE-ONLY as the project ID. It is for checking layout, not an academic record.

Once the final result and exact template version are approved, open the group and download D1–D7 as Word or PDF. The portal:

1. Opens the original corresponding Word template.
2. Fills the group ID/title, course/department fields and member rows.
3. Inserts the approved marks for the correct seats.
4. Retains the supplied table structure, QEC reference, signature areas and other original rubric pages.
5. Returns a Word file or renders a genuine PDF with LibreOffice.
6. Records the report version, template hash, file hash and exporting user.

Save the download to your computer and print it. PDF download does not require printing HTML manually. PDF rendering does require LibreOffice on the portal's machine.

The original templates contain four student rows. This pilot handles one to four members. A larger group requires an approved template/layout decision. Visual identity must be checked in Word and the actual NED server renderer, especially with long names/titles. It is not guaranteed simply because the template file is the original.

No signature is fabricated. Signature lines remain for the authorized signing process. Automatic Drive report archiving is not configured in this pilot.

## 10 Individual reports and QEC references

The existing seven n8n workflows continue producing their individual HTML reports. Their exported templates still contain QEC references. This build preserved them rather than editing tested originals.

The next n8n change should happen on inactive copies: remove QEC references from those individual summaries, keep identity/marks intact, and retest two students in one execution before replacing the live version. Official group QEC reports are the portal's separate path.

## 11 What stays in sync and what is protected

| Situation | Portal behavior |
|---|---|
| A new authorized response is read | Accept it if valid and within its acceptance rules |
| Same response is read again | No extra evaluator mark is added |
| A response changes | Hold it for correction review |
| A student name in the form changes | Keep the official roster name |
| A frozen stage's source changes | Keep the frozen snapshot and hold the change |
| HOD reopens a stage | Preserve history and supersede the current final approval |
| n8n is stopped | Existing form collection can continue, but that n8n process cannot send reports |
| Portal is stopped | Its database remains saved; no portal reads/exports run until it restarts |
| Only an XLSX was uploaded | Later source changes appear only after a new upload/read |

## 12 What remains before the department uses it

Bind the real Google connection, identify the six canonical forms among their copies, validate evaluator identity, confirm academic decisions, reconcile a full historical group including uneven D4 values, approve template samples, test PostgreSQL concurrency and backups, and complete faculty/IT acceptance.

The current version is a tested local pilot. A working localhost page is not proof that NED hosting, institutional account ownership, unattended synchronization or official document acceptance is complete.

The official group summary table is populated. Supplementary evaluator rubric pages are retained as blank masters; the portal does not fabricate completed evaluator forms or signatures.

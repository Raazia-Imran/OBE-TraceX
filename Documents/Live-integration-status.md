# Integration status · 25 November 2026

The last connected laptop run read the grading workbook through n8n and refreshed the live portal session. The seven grading workflows target this workbook. Report-archive branches were installed on all seven. The grading triggers and Gmail senders were inactive during validation.

| Check | Evidence |
|---|---|
| D1 live archive | One roster-matched workbook row produced a signed report. The portal stored the expected student's exact HTML bytes. Replaying it returned the existing document. |
| Isolated archive replay | D1, D3, D5, D6 and D7 passed the student, stage and byte checks in a temporary portal database. This exercised report rendering and archiving from existing rows. |
| D2 and D4 | Raw response tabs have trailing whitespace in the seat header. A normalization update and repeat run were launched. Retrieve the final result from the laptop or rerun the isolated validation before marking these stages complete. |
| Portal regression suite | 68 Django tests passed on the working laptop copy, including a test that rejects a mismatched Form response workbook before changing respondent permissions. |

## Department rollout

1. Obtain the Forms owner's authorization and the approved evaluator assignments by group and stage. Six stage links were configured, with zero verified allowlists and zero evaluator assignments at inspection.
2. Confirm each Form's respondent URL and linked workbook. Verify that an assigned account can submit and a forwarded link fails for an unassigned account.
3. Reconcile the live session's 15 import issues with the coordinator. Nine roster seats lacked a consolidated row, five workbook seats were outside the session roster, and one D4 supervisor detail was missing or repeated.
4. Submit a controlled evaluation through a designated test Form. Follow the response into its worksheet, calculated marks, dashboard and report. Verify delivery to the designated test recipient before turning on department email.
5. Verify the group exports, approval, freeze and correction flow against the department's reference marks. Record the run against the existing acceptance sheet.

The laptop contains working-copy integration changes. Verify the final replay and synchronize reviewed source changes before relying on a fresh clone to reproduce this installation. Keep live credentials, student rows and workflow exports containing personal data outside the public repository.

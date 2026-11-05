# Integration with existing n8n and Google Sheets

**Workflow correction:** Use [the current real-group integration guide](../docs/REAL_GROUP_END_TO_END.md). The primary importer now reads the existing D7 master totals and supporting criterion tabs; re-entering evaluator assignments or regrading raw submissions is not required for this route. Older raw-event/demo sections below describe the optional legacy path.

## Preserve the baseline

Keep n8n on port 5678 and the portal on port 8000 during development. Export and privately back up n8n workflows, persistent database and encryption key before a future migration. This repository stores hashes of the seven supplied exports, not their private credential/recipient bindings.

Do not import a new workflow into the existing production workflow ID, enable duplicate senders or change workbook formulas during initial portal setup. The portal has no Google Sheets write scope and no API for modifying n8n.

## Option A: read source responses without changing n8n

Start with a coordinator-uploaded XLSX or a manual Google Sheets read. Configure server-side Application Default Credentials (typically a university service account JSON mounted as a secret), share only the intended workbook with that identity as a viewer, and set:

```text
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/google-credentials.json
GOOGLE_WORKBOOK_ID=<verified-workbook-id>
```

The adapter requests only `spreadsheets.readonly` and reads bounded D1–D6 raw tabs, not formula-generated checkboxes. Google credentials belong to the department, not a graduating student. Store no credentials in Git. See `evaluations/google_sync.py` for exact range/schema mapping.

The pilot's Google reads are manual; schedule unattended reads only after the ownership, academic-session routing, monitoring and failure policy are agreed. A scheduled management command must run as an authorized service identity and record each import. Do not infer that manual Google setup enables continuous sync.

## Option B: a separate signed n8n sidecar

After testing Option A, build a separate inactive sidecar workflow against TEST response tabs. Normalize each received row to the following contract and POST its exact UTF-8 body to `/integrations/n8n/evaluation/` over HTTPS.

```json
{
  "event_id": "d4c5b76f-6072-4614-8462-3ff3b4bd5287",
  "issued_at": 1793872800,
  "evaluation": {
    "session": "Synthetic QA",
    "attempt": 1,
    "seat": "SE-99001",
    "stage": "D1",
    "evaluator": "reviewer@example.test",
    "source_id": "stable-google-form-response-id",
    "percentages": [100, 75, 50, 100],
    "comments": "Synthetic test only"
  }
}
```

Use the actual current Unix time and a new UUID event ID. The signed `source_id` must retain the same source response identity on a correction. Do not use a newly randomized source_id for every repeated read. Verify evaluator identity against registered assignments, not an editable display name. Existing tests with one shared sender email and multiple evaluator display names need explicit reconciliation.

Signature: lowercase hex HMAC-SHA256 of the **exact raw body**, using `N8N_WEBHOOK_SECRET`, placed in `X-OBE-Signature`. Both sides keep this secret outside the repository. Use `n8n/sign_event.js` as signing logic after canonical normalization. The HTTP Request node must send `json.rawBody` as its raw JSON body with the matching signature header; reserializing the object changes the signature.

Accepted status values: `accepted`, `unchanged`, `held`. Held changes do not replace approved scores. Events expire after five minutes; exact replay event IDs return unchanged. Signature failures return 401, malformed/unassigned/expired events return 400, and an unconfigured integration returns 503. Retry only with a controlled new timestamp/signature after reconciling a failure; never treat a 200 held status as final grade approval.

Production n8n policy may disallow environment-variable reads or Node's crypto module in Code nodes. Have IT approve a credential-based signing mechanism or a small internal sender service rather than relaxing the entire instance's sandbox. Do not change the tested seven workflows to make this example run.

## Existing individual reports

The seven supplied workflows create HTML attachments with QEC references. The portal now has the separate official-template path. Prepare copies to remove QEC identifiers from individual summaries, retain report identity, and retest. This work remains pending; the baseline itself was preserved.

## What synchronization does not do

The portal never writes an approved result over raw form responses. Approved snapshots do not update when source formulas or names change. Portal freezes do not themselves close Google Forms. Enforce actual form-session restrictions separately after verifying its edit/closing behavior. Downloaded reports are private responses; automatic Drive report archiving/link synchronization is not configured in this pilot.

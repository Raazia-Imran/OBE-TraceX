# Connected workspace
Source formulas remain owned by the Google workbook. The portal only reads calculated values and retains its own immutable snapshots/documents.

## Running locally
Start Portal.cmd and Start Expo Portal.cmd use the isolated Expo database when present. Original local.sqlite3 is retained.
Start Live Updates.cmd reads the live session and Coordinator username from private-data/live-session.cmd. Both launchers start this worker when configured.
The worker refreshes through the existing credential-preserving n8n reader, then waits 60 seconds. The UI checks for new data every 10 seconds. This is near-live polling, not an instant push guarantee.
A failed read keeps previously imported records and reports a connection error. Validation issues are displayed separately from connectivity.
Saved faculty-reference and rehearsal sessions are protected from the background worker.

## Report archive
Approved QEC exports and labelled previews are persisted as binary documents with SHA-256 digests. Downloads require an authorized Coordinator/HOD session and are served as attachments.
POST /integrations/n8n/report/ accepts an HMAC-SHA256 signed body in X-OBE-Signature, using private OBE_REPORT_WEBHOOK_SECRET (or N8N_WEBHOOK_SECRET fallback). Reports require session label, seat, attempt, D1-D7 stage, filename, extension, base64 content, event identity and a timestamp within five minutes.
integrations/n8n/archive_report.js is an additive branch contract to attach after the existing HTML node. Set the actual session and map seat/stage from the corresponding trigger. Send its signed rawBody with an HTTP Request node. Existing email/calculation nodes must remain unchanged.
The receiver passed an isolated n8n acceptance test using the existing D1 HTML template and a live source row. The archived HTML was verified byte-for-byte. No email was sent and no original grading workflow was changed. The branch still needs connection to each canonical live stage workflow after Form/source mapping is confirmed.

## Required external inputs
All six supplied editor/respondent pairs are saved privately in the local live session. D1 was title-checked; D2-D6 are mapped in the supplied order pending owner sign-in verification. Linked response-sheet destinations and owner-authorized Google permissions still need confirmation. Full historical replay is deferred until after the mid evaluation.
Google permissions need a private authorized-user token with Drive and Forms access. The evaluator page refuses public/domain/group responder access rather than presenting it as a verified allowlist.
No new Google authorization or official template approval has been fabricated.

## Historical comparison
/workbook/ shows actual imported stage/final values in the portal.
/comparison/ compares all six reported stage totals and the final mark against the saved faculty workbook. Missing rows and mismatches remain visible.
The current live snapshot differs from the historical reference and lacks historical students. Student identities and marks are retained only in the private database. This is not a passing historical replay.
The supplied three-group input must still be replayed through isolated copies of all six Forms/workflows to verify the final output exactly.

## Server handover
Use PostgreSQL and the existing production security configuration. Run migrations 0005 and 0006. Run one managed background worker per live source session (systemd/container scheduler), monitor its status, retain database/document backups and configure HTTPS, server secrets and Google OAuth for the university identity.
The current desktop configuration is a local evaluation environment, not a completed university-server deployment.

Coordinator-only Form editor buttons are available in Evaluator access and Integration hub. HOD users see respondent links and saved data without editor buttons. Form URLs and private configuration are not committed to the public repository.

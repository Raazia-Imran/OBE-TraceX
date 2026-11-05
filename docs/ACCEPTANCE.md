# Validation and acceptance

## Local automated coverage

Run `python manage.py test evaluations` from the repository. The suite verifies:

- Unequal D4 weights and the overall 200 maximum.
- Zero versus missing/invalid/non-finite values, seat normalization and decimal display.
- Authorized assignment matching, repeated delivery and changed-response review.
- Variable evaluator counts and equal-weight criterion averages.
- Missing evaluations, incorrect group membership and unapproved rules blocking freezing.
- Stale review versions, role separation, final prerequisites and unresolved corrections.
- Frozen snapshots surviving source changes and HOD reopening retaining history.
- Evaluation windows, signed event authentication/expiry/replay and disabled integrations.
- CSRF, restricted routes, logout method, password hashing, login throttling and TOTP replay protection.
- DOCX identity/marks association, original table geometry/sections, and official export prerequisites.
- Atomic roster rejection and source-import error handling.

A passing local test does not establish production PostgreSQL concurrency, network permissions, faculty approval or visual identity across Word versions.

## Template acceptance

Generate `python manage.py template_sample --output private-samples`. Samples are synthetic and clearly named SAMPLE_ONLY. Original template files remain unchanged. Check each D1–D7 file against its source for reference, logo/artwork, margins, orientation, table grid, signatures, department/course text and pagination. Test maximum-length real-world names and project titles separately. Original rubric pages remain present; the summary table is populated. No evaluator signature is fabricated.

The HOD template approval stores the source file hash and a verification reference. A changed template hash requires new verification. This gate records the HOD decision; it does not prove legal/QEC acceptance without faculty review.

## Live pilot acceptance

| Test | Pass requirement |
|---|---|
| Google form routing | Every actual form writes to the intended workbook and tab |
| Historical reconciliation | Every criterion/student/stage matches independently calculated approved results |
| Duplicate evaluator | Corrected response counts once; unauthorized duplicates are held |
| Concurrent freeze/import | Exactly one active stage snapshot; stale approval rejected in PostgreSQL |
| Changed frozen response | Approved snapshot unchanged; correction held |
| HOD reopening | Old snapshots retained, final approval invalidated, replacement reapproved |
| Official reports | All members, correct marks, QEC reference and approved source layout |
| Role access | Coordinator/HOD actions enforced server-side; anonymous access denied |
| MFA and recovery | Both owners enrolled, replay denied, documented recovery exercised |
| API failure | Google/n8n outage visible; no false success and no source mutations |
| Backup restore | Database, MFA key, templates and n8n credentials recover on isolated staging |
| Department handover | Named Coordinator, HOD and IT owners sign off on the tested deployment |

## Deliberate pilot limitations

No cohort-wide moderation button, multi-role evaluator dashboards, automatic Drive archiving, self-service roster restructuring, automatic scheduled synchronization or signed final PDFs are claimed. The portal currently imports a roster once per session, supports 1–4 members in the supplied templates, uses equal assigned-evaluator weighting and a faculty-approval gate for the proposed rounding policy. These boundaries must be accepted or extended before live operation.

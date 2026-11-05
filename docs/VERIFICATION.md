# Verification record

Local verification on 5 November 2026:

- 33 automated Django tests passed on the isolated SQLite test database.
- `manage.py check` and `makemigrations --check --dry-run` passed.
- `manage.py check --deploy` passed with generated in-memory production configuration. This is a configuration check, not a live server or penetration test.
- Original uploaded workflow/template hashes remained unchanged.
- Generated genuine PDF and Word samples for D1–D7, retaining the original group table grids, section structure, QEC references and artwork.
- Compared source and populated PDF page counts under the same local renderer after fixing an overflow in supplementary rubric identity lines. Source faculty and target Word/server rendering acceptance is still required.
- Visually reviewed synthetic dashboard, login and group approval screens in the browser. These were static renders of the actual Django templates; the authentication/mutation flows were exercised by automated tests rather than a live browser login.
- Code/guide publishing excludes private student workbooks, raw n8n workflow exports, credentials and local databases.

The populated group summary is the official report output. Supplementary evaluator rubric pages remain blank master forms; the portal does not invent evaluator signatures or fill a group ID into an individual identity line.

Not verified here: NED deployment, Docker execution, actual Google credential binding, unattended synchronization, actual form edit/closing settings, live n8n sidecar delivery, faculty policy/QEC acceptance and a production backup/restore drill. GitHub CI is supplied for SQLite/PostgreSQL; check its actual run results before release.

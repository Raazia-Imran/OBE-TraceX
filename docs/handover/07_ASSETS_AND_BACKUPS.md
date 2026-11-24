# OBE TraceX assets and recovery

## Collected media and earlier documents

[VERIFIED FROM CURRENT FILE] These existing assets were available and collected. Their presence is not an accuracy certification of claims inside a video/poster. Review outdated completion/approval wording before reuse.

| Asset | Role |
|---|---|
| OBE-TraceX-Promo-60s.mp4 | Existing portrait promotional video |
| OBE_TraceX_Narrated_Walkthrough.mp4 | Existing narrated demonstration |
| OBE-TraceX Poster in Navy and Cyan.png | Existing poster |
| OBE-TraceX From Evaluation to Evidence images | Two alternative existing poster images; filenames normalized where needed |
| OBE_TraceX_A4_Expo_Standee.pdf | Existing print/display standee |
| media-src/render_promo.py | Editable source for promotional film |
| media-src/make_wordmark.py | Wordmark generation source |
| evaluations/static/evaluations | Logo, NED emblem, share card, favicon and interface assets |

The earlier pitch, project progress, setup, testing-status and real-group testing PDFs were retained separately. An editable earlier progress DOCX was also available. Duplicate setup PDFs with identical content need only one reading copy; the asset inventory records provenance.

[UNRESOLVED] No OBE-TraceX slide deck was found in the targeted project folders or title search during this task. No new slide deck was invented as a replacement. If one exists elsewhere, add it to 05_Assets and update the manifest. Other projects' slides/posters are not OBE-TraceX assets.

## Private local backups

[VERIFIED FROM CURRENT FILE] The local private backup contains a consistent SQLite backup of the active real database and the older local private databases, the portal private configuration/scripts, the original n8n automation directory, and a fresh local n8n SQLite backup with its existing config. The config can contain the encryption key; keep it under the same access restrictions as the database.

The n8n documentation confirms that a database/workflow export alone is insufficient to recover encrypted credentials without the matching key/config. A backup existing on this laptop is not proof that recovery works, nor an independent off-device backup. Complete an isolated restore drill with the department IT owner.

The copied raw private exports can include recipient addresses and credential bindings. Do not publish them. The shareable ZIP excludes these files, all student databases/workbooks, passwords and runtime connection files. Public integration fragments and blank mapping sheets are included instead.

## Recovery sequence

1. Preserve the latest working installation and the backed-up bytes. Check file sizes/hashes from 08_Evidence before restoring.
2. Restore source at its recorded commit into a new isolated folder. Recreate the virtual environment from requirements; do not move a Windows venv to another computer.
3. Restore the intended portal database into a private TEST path and set OBE_DB_PATH explicitly. Verify table counts and stored-document hashes before allowing mutations.
4. Recover the department-owned secrets through the authorized owner. Keep the same n8n encryption key with its encrypted database/credentials. Do not print/decrypt credentials into chat.
5. Restore n8n in an isolated instance with workflows inactive and email destinations controlled. Check the target version and migration requirements first.
6. Confirm Google read access and six exact Form destinations. Reauthorize expired tokens through the owner rather than making Sheets public.
7. Run local code checks, a private read, one-group acceptance and document layout inspection. Record the recovered environment and remaining failures.
8. Promote only after academic and IT owners approve; preserve the pre-restore copy and document rollback.

A restored database contains protected records and account secrets. Do not overwrite the current real database merely to see whether a historical backup opens.

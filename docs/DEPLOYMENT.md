# NED deployment and operational handover

This is a staging runbook. No NED machine, domain or production credential has been configured by this development session. The supplied Docker configuration has not been executed in this workspace because Docker is unavailable.

## Confirm with IT first

Obtain the supported Linux/Windows environment, container policy, storage, PostgreSQL support, approved domain/TLS path, Google outbound connectivity, institutional identity policy, backup owner and recovery objectives. Confirm whether evaluation data may stay in Google Workspace. Campus hosting does not move Google Forms/Sheets data onto the campus server.

## Staging sequence

1. Clone the reviewed commit on an isolated IT host. Keep the existing n8n machine untouched.
2. Copy `.env.example` to `.env` and restrict its filesystem permissions. Set the actual hostname/CSRF origin, independent PostgreSQL password, Django secret and MFA encryption key. Generate Django/webhook secrets with `python -c "import secrets; print(secrets.token_urlsafe(64))"` and the MFA key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` in a private terminal. Never paste these outputs into chat or Git.
3. Run `docker compose build` then `docker compose up -d db`.
4. Run `docker compose run --rm web python manage.py migrate` and `docker compose run --rm web python manage.py collectstatic --noinput`.
5. Run `docker compose run --rm -it web python manage.py provision_account coordinator --role coordinator` and the equivalent HOD command. Each owner chooses a unique password privately.
6. Run `docker compose run --rm -it web python manage.py enroll_mfa <username>` with each owner in a private terminal. Scan/type the local authenticator secret and verify a code. Production blocks account sign-in without MFA enrollment. Keep the MFA key in the university secret manager with its backup.
7. Export static files to the host path: `docker compose cp web:/app/staticfiles/. /srv/obe-static/` after the web container exists. Alternatively, use an IT-approved shared volume/static-server configuration. The Nginx alias must match the chosen path; do not assume a Docker volume is automatically host-mounted there.
8. Install the adapted reverse-proxy config and valid TLS certificates, then `docker compose up -d web`. The app's port is bound to loopback, PostgreSQL has no published port. `TRUST_PROXY=1` is valid only behind this trusted proxy which replaces the forwarded protocol header.
9. Run `docker compose exec web python manage.py check --deploy`. Inspect all warnings. Run the test suite against a separate PostgreSQL test database with a role permitted to create test databases; do not run destructive tests against production.
10. Configure the read-only Google credential using a private read-only secret mount. Verify the six actual form destinations. If using n8n events, set the shared signing secret privately and exercise a separate TEST workflow first.
11. Complete faculty historical reconciliation, final report comparison and the acceptance checklist. Approve only the templates that match on the actual target renderer/fonts.
12. Perform a backup/restore drill on a separate host and obtain Coordinator/HOD/IT acceptance before the controlled pilot.

## Backup and restore

Back up PostgreSQL with `pg_dump` through an authorized IT process. Store encrypted backups off-host with retention agreed by the department. Back up deployment configuration, the Django secret, the **MFA encryption key**, original/approved template files and approval records together. The portal stores immutable mark snapshots and report hashes in the database; downloaded report files are not retained on server by this pilot.

For n8n, preserve its database and encryption key separately using the installed release's supported backup procedure. Workflow JSON alone cannot restore encrypted credentials. This repository does not migrate or overwrite n8n's existing database.

Restore into an isolated staging stack. Verify login/MFA, roster identity, stage and final snapshot hashes, template approval hashes and generated reports. Record restore duration and any missing data. Never point both a restored and original n8n sender at live recipients.

## Account recovery

Password recovery is through authorized IT, using `python manage.py changepassword <username>` on the server. There is no public reset form or emailed reset token in this pilot. Log the support ticket and verify the owner's identity first. Lost authenticator recovery requires an IT-controlled procedure with database access and a recorded audit event; this pilot deliberately does not expose a self-service MFA reset endpoint. Agree and test that procedure before launch.

## Monitoring and maintenance

Monitor service availability, database backups, disk use, Google credential failures, pending corrections, sync freshness and PDF rendering errors. Add the IT-approved alerting mechanism before unattended deployment. The read-only `/healthz/` endpoint reports app availability only; it does not prove Google/n8n connectivity or successful backups.

The current login throttle uses the direct peer address. Behind Nginx that may be the proxy address, so tune rate limiting at the trusted reverse proxy and keep the per-username application throttle. Do not trust arbitrary client-supplied forwarded-IP headers.

Pin reviewed dependency/container versions and update in staging. Docker image tags here are starting points, not immutable production digests; IT should pin reviewed image digests during deployment. Maintain confidentiality of n8n execution logs and portal backups.

## Rollback

Retain the previous application image and a compatible database backup before each release. Test migrations against staging and choose a documented rollback path. Stop portal ingestion before rollback to avoid losing new assessments. Never restore older results over newer approved marks without faculty authorization and reconciliation. Keep the tested original n8n workflows available as the reference throughout cutover.

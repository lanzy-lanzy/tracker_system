# PostgreSQL Admin Backup Design

## Goal

Add admin-dashboard backup and restore support for the Railway PostgreSQL database while preserving the existing SQLite workflow for local development.

## Architecture

Backup behavior lives in `admin_panel.backup_utils` so database-specific work is testable without rendering the dashboard. The admin view delegates create, upload, restore, list, and export actions to that module, then records user-facing messages and audit logs.

## Behavior

When the default database engine is PostgreSQL, the Backup page creates custom-format `.dump` backups using `pg_dump --format=custom --no-owner --no-acl`. The code parses `DATABASE_URL` into PostgreSQL client environment variables so the password is not passed as a process argument. Uploaded backups must be `.dump` files with safe filenames and must fit within the existing upload size limit. Restoring a backup first creates a pre-restore dump, then runs `pg_restore --clean --if-exists --no-owner --no-acl`.

When the default database engine is SQLite, the page keeps the existing `.sqlite3` file copy, upload, download, and restore behavior.

## Error Handling

The dashboard reports missing `DATABASE_URL`, unavailable `pg_dump` or `pg_restore`, unsafe filenames, oversized uploads, missing backup files, and failed subprocess commands as clear admin messages. The Railway Railpack image installs `postgresql-client` at runtime through `railpack.json`. Restore remains admin-only, POST-only, CSRF-protected through Django forms, and audited.

## Testing

Unit tests cover engine detection, allowed extensions, safe path validation, backup listing, PostgreSQL command construction, missing `DATABASE_URL`, and restore pre-backup behavior with subprocess calls mocked.

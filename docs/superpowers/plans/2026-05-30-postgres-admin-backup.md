# PostgreSQL Admin Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build PostgreSQL create, import, download, and restore backup support in the admin dashboard.

**Architecture:** Add a focused backup utility module for database detection, safe file handling, and native PostgreSQL dump/restore commands. Keep the existing admin routes and template, but make their labels and accepted file type dynamic based on the active database backend.

**Tech Stack:** Django 5.2, PostgreSQL via `DATABASE_URL`, `pg_dump`, `pg_restore`, Django `TestCase`/`SimpleTestCase`.

---

### Task 1: Backup Utilities

**Files:**
- Create: `admin_panel/backup_utils.py`
- Test: `admin_panel/tests.py`

- [ ] Add tests for database kind detection, extension selection, safe path validation, and PostgreSQL command calls with `subprocess.run` mocked.
- [ ] Run `python manage.py test admin_panel`.
- [ ] Implement `BackupError`, `database_kind`, `allowed_extension`, `safe_backup_path`, `list_backups`, `create_backup`, `save_uploaded_backup`, and `restore_backup`.
- [ ] Run `python manage.py test admin_panel`.

### Task 2: Dashboard Integration

**Files:**
- Modify: `admin_panel/views.py`
- Modify: `admin_panel/templates/admin_panel/backup.html`
- Create: `railpack.json`
- Test: `admin_panel/tests.py`

- [ ] Add view tests for PostgreSQL create/upload/restore message behavior with utility functions mocked.
- [ ] Run `python manage.py test admin_panel`.
- [ ] Replace SQLite-specific view code with calls to `backup_utils`.
- [ ] Make the template copy, upload accept attribute, and empty state reflect `.dump` for PostgreSQL and `.sqlite3` for SQLite.
- [ ] Add `railpack.json` so Railway installs `postgresql-client` in the runtime image.
- [ ] Run `python manage.py test admin_panel`.

### Task 3: Management Command

**Files:**
- Modify: `core/management/commands/backup_db.py`

- [ ] Update the command to call `admin_panel.backup_utils.create_backup`.
- [ ] Run `python manage.py test admin_panel core`.

### Task 4: Final Verification

**Files:**
- All touched files

- [ ] Run `python manage.py test`.
- [ ] Run `python manage.py check`.
- [ ] Review `git diff --check`.

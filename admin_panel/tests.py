import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from admin_panel import backup_utils


SQLITE_DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}

POSTGRES_DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "railway",
    }
}


class BackupUtilityTests(SimpleTestCase):
    def test_docker_deployment_installs_postgres_client_18_for_railway_postgres(self):
        project_root = Path(__file__).resolve().parent.parent
        dockerfile = (project_root / "Dockerfile").read_text()
        railway_config = (project_root / "railway.toml").read_text()

        self.assertIn('builder = "DOCKERFILE"', railway_config)
        self.assertIn("apt.postgresql.org/pub/repos/apt", dockerfile)
        self.assertIn("postgresql-client-18", dockerfile)

    @override_settings(DATABASES=SQLITE_DATABASES)
    def test_sqlite_uses_sqlite_extension(self):
        self.assertEqual(backup_utils.database_kind(), "sqlite")
        self.assertEqual(backup_utils.allowed_extension(), ".sqlite3")

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_postgres_uses_dump_extension(self):
        self.assertEqual(backup_utils.database_kind(), "postgresql")
        self.assertEqual(backup_utils.allowed_extension(), ".dump")

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_safe_backup_path_rejects_wrong_extension_and_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BASE_DIR=Path(tmp)):
                self.assertIsNone(backup_utils.safe_backup_path("tracker_backup.sqlite3"))
                self.assertIsNone(backup_utils.safe_backup_path("../tracker_backup.dump"))
                self.assertIsNotNone(backup_utils.safe_backup_path("tracker_backup.dump"))

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_create_postgres_backup_runs_pg_dump_without_exposing_database_url(self):
        database_url = "postgresql://user:secret@example.com:5432/railway?sslmode=require"
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BASE_DIR=Path(tmp)):
                with patch.dict(os.environ, {"DATABASE_URL": database_url}):
                    with patch("admin_panel.backup_utils.subprocess.run") as run:
                        backup = backup_utils.create_backup()

        self.assertEqual(backup.path.suffix, ".dump")
        command = run.call_args.args[0]
        env = run.call_args.kwargs["env"]
        self.assertEqual(command[0], "pg_dump")
        self.assertIn("--format=custom", command)
        self.assertIn("--file", command)
        self.assertNotIn(database_url, " ".join(str(part) for part in command))
        self.assertNotIn("secret", " ".join(str(part) for part in command))
        self.assertEqual(env["PGHOST"], "example.com")
        self.assertEqual(env["PGPORT"], "5432")
        self.assertEqual(env["PGDATABASE"], "railway")
        self.assertEqual(env["PGUSER"], "user")
        self.assertEqual(env["PGPASSWORD"], "secret")
        self.assertEqual(env["PGSSLMODE"], "require")

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_create_postgres_backup_requires_database_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BASE_DIR=Path(tmp)):
                with patch.dict(os.environ, {}, clear=True):
                    with self.assertRaisesRegex(backup_utils.BackupError, "DATABASE_URL"):
                        backup_utils.create_backup()

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_restore_postgres_backup_creates_pre_restore_dump_then_runs_pg_restore(self):
        database_url = "postgresql://user:secret@example.com:5432/railway?sslmode=require"
        with tempfile.TemporaryDirectory() as tmp:
            backup_dir = Path(tmp) / "backups"
            backup_dir.mkdir()
            restore_file = backup_dir / "tracker_backup_20260530_120000.dump"
            restore_file.write_bytes(b"dump")

            with override_settings(BASE_DIR=Path(tmp)):
                with patch.dict(os.environ, {"DATABASE_URL": database_url}):
                    with patch("admin_panel.backup_utils.subprocess.run") as run:
                        result = backup_utils.restore_backup(restore_file.name)

        self.assertTrue(result.pre_restore_backup.name.startswith("pre_restore_"))
        self.assertEqual(result.pre_restore_backup.suffix, ".dump")
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0][0], "pg_dump")
        restore_command = run.call_args_list[1].args[0]
        self.assertEqual(restore_command[0], "pg_restore")
        self.assertIn("--clean", restore_command)
        self.assertIn("--if-exists", restore_command)
        self.assertIn(str(restore_file), restore_command)

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_uploaded_postgres_backup_must_have_dump_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BASE_DIR=Path(tmp)):
                uploaded = SimpleUploadedFile("bad.sqlite3", b"backup")
                with self.assertRaisesRegex(backup_utils.BackupError, ".dump"):
                    backup_utils.save_uploaded_backup(uploaded)


class BackupViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("admin", password="password")
        self.user.profile.role = "admin"
        self.user.profile.save()
        self.client.force_login(self.user)

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_backup_page_uses_postgres_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(BASE_DIR=Path(tmp)):
                response = self.client.get(reverse("admin_backup"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["database_kind"], "postgresql")
        self.assertEqual(response.context["allowed_ext"], ".dump")
        self.assertContains(response, ".dump")
        self.assertContains(response, "PostgreSQL")

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_create_backup_action_delegates_to_backup_utils(self):
        backup = backup_utils.BackupFile(
            name="tracker_backup_20260530_120000.dump",
            path=Path("backups/tracker_backup_20260530_120000.dump"),
            size=10,
            modified=backup_utils.datetime.now(),
            size_display="10.0 B",
        )
        with patch("admin_panel.backup_utils.create_backup", return_value=backup) as create_backup:
            response = self.client.post(reverse("admin_backup"), {"action": "create"})

        self.assertRedirects(response, reverse("admin_backup"))
        create_backup.assert_called_once_with()

    @override_settings(DATABASES=POSTGRES_DATABASES)
    def test_restore_backup_action_delegates_to_backup_utils(self):
        result = backup_utils.RestoreResult(
            restored_backup=Path("backups/tracker_backup_20260530_120000.dump"),
            pre_restore_backup=Path("backups/pre_restore_20260530_120001.dump"),
        )
        with patch("admin_panel.backup_utils.restore_backup", return_value=result) as restore_backup:
            response = self.client.post(
                reverse("admin_backup"),
                {"action": "restore", "filename": "tracker_backup_20260530_120000.dump"},
            )

        self.assertRedirects(response, reverse("admin_backup"))
        restore_backup.assert_called_once_with("tracker_backup_20260530_120000.dump")

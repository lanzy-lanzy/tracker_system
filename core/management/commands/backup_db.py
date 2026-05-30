from django.core.management.base import BaseCommand

from admin_panel import backup_utils


class Command(BaseCommand):
    help = "Backup the configured database to the backups/ directory"

    def handle(self, *args, **options):
        try:
            backup = backup_utils.create_backup()
        except backup_utils.BackupError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Backup created: {backup.name} ({backup.size:,} bytes)"
            )
        )

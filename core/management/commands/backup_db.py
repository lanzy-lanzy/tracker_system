import os
import shutil
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backup the SQLite database to the backups/ directory"

    def handle(self, *args, **options):
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)

        db_path = settings.BASE_DIR / "db.sqlite3"
        if not db_path.exists():
            self.stderr.write(self.style.ERROR("No SQLite database found at db.sqlite3"))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tracker_backup_{timestamp}.sqlite3"
        backup_path = backup_dir / filename

        shutil.copy2(db_path, backup_path)

        size = backup_path.stat().st_size
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup created: {filename} ({size:,} bytes)"
            )
        )

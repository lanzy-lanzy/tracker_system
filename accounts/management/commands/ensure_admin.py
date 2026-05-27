from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Ensures an admin user exists (respects SEED_ADMIN_PASSWORD env var)"

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Admin user already exists, skipping.")
            return
        password = os.environ.get("SEED_ADMIN_PASSWORD")
        if not password:
            self.stdout.write("SEED_ADMIN_PASSWORD not set. Create a superuser manually at /admin/.")
            return
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=password,
        )
        self.stdout.write(self.style.SUCCESS("Created superuser 'admin'."))

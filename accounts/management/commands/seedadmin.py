import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the admin user from SEED_ADMIN_PASSWORD env var"

    def handle(self, *args, **options):
        password = os.environ.get("SEED_ADMIN_PASSWORD")
        if not password:
            self.stdout.write("SEED_ADMIN_PASSWORD not set, skipping admin seed")
            return
        if User.objects.filter(username="admin").exists():
            self.stdout.write("Admin user already exists, skipping")
            return
        user = User.objects.create_superuser("admin", "admin@example.com", password)
        Profile.objects.create(user=user, role="admin")
        self.stdout.write(f"Admin user created with password from SEED_ADMIN_PASSWORD")

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
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = user.email or "admin@example.com"
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(update_fields=["email", "is_staff", "is_superuser", "password"])
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = "admin"
        profile.save(update_fields=["role"])
        action = "created" if created else "updated"
        self.stdout.write(f"Admin user {action} with password from SEED_ADMIN_PASSWORD")

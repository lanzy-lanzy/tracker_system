from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .models import Profile


class SeedAdminCommandTests(TestCase):
    def test_seedadmin_creates_admin_profile_and_is_idempotent(self):
        with patch.dict("os.environ", {"SEED_ADMIN_PASSWORD": "temporary-password"}, clear=False):
            call_command("seedadmin")
            call_command("seedadmin")

        user = get_user_model().objects.get(username="admin")

        self.assertTrue(user.is_superuser)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.profile.role, "admin")

    def test_seedadmin_repairs_existing_admin_profile(self):
        user = get_user_model().objects.create_user(username="admin", password="old-password")

        with patch.dict("os.environ", {"SEED_ADMIN_PASSWORD": "new-temporary-password"}, clear=False):
            call_command("seedadmin")

        user.refresh_from_db()
        user.profile.refresh_from_db()

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("new-temporary-password"))
        self.assertEqual(user.profile.role, "admin")

# Create your tests here.

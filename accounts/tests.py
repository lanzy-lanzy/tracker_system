from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from drivers.models import Driver

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


class SeedSampleDataCommandTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.admin.profile.role = "admin"
        self.admin.profile.save(update_fields=["role"])

    def test_seed_sample_data_links_each_driver_to_driver_user(self):
        call_command("seed_sample_data")

        drivers = Driver.objects.select_related("user__profile")

        self.assertGreaterEqual(drivers.count(), 5)
        self.assertFalse(drivers.filter(user__isnull=True).exists())
        for driver in drivers:
            self.assertEqual(driver.user.profile.role, "driver")
            self.assertEqual(driver.user.driver_profile, driver)


class UserManagementDriverSyncTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="admin", password="password")
        self.admin.profile.role = "admin"
        self.admin.profile.save(update_fields=["role"])
        self.client.force_login(self.admin)

    def driver_payload(self, **overrides):
        payload = {
            "username": "driver1",
            "email": "driver@example.com",
            "password": "password123",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "role": "driver",
            "contact_number": "09171234567",
            "license_number": "LIC-001",
            "license_expiry": "2030-01-01",
            "address": "Depot Road",
            "employment_status": "active",
            "emergency_contact_name": "Maria Dela Cruz",
            "emergency_contact_number": "09181234567",
            "remarks": "Available for city routes",
        }
        payload.update(overrides)
        return payload

    def test_creating_driver_user_creates_linked_driver_profile(self):
        response = self.client.post("/accounts/users/create/", self.driver_payload())

        user = get_user_model().objects.get(username="driver1")

        self.assertRedirects(response, "/accounts/users/")
        self.assertEqual(user.profile.role, "driver")
        self.assertEqual(user.driver_profile.full_name, "Juan Dela Cruz")
        self.assertEqual(user.driver_profile.license_number, "LIC-001")

    def test_editing_driver_user_updates_linked_driver_profile(self):
        user = get_user_model().objects.create_user(
            username="driver2",
            first_name="Old",
            last_name="Name",
            password="password123",
        )
        user.profile.role = "driver"
        user.profile.save(update_fields=["role"])
        Driver.objects.create(
            user=user,
            full_name="Old Name",
            contact_number="09000000000",
            license_number="OLD-001",
            license_expiry="2030-01-01",
            employment_status="active",
        )

        response = self.client.post(
            f"/accounts/users/{user.pk}/edit/",
            self.driver_payload(
                username="driver2",
                first_name="New",
                last_name="Driver",
                contact_number="09991234567",
                license_number="NEW-002",
                license_expiry="2031-02-03",
            ),
        )

        user.driver_profile.refresh_from_db()

        self.assertRedirects(response, "/accounts/users/")
        self.assertEqual(user.driver_profile.full_name, "New Driver")
        self.assertEqual(user.driver_profile.contact_number, "09991234567")
        self.assertEqual(user.driver_profile.license_number, "NEW-002")


class ProfilePicturePersistenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="password")
        self.client.force_login(self.user)

    def test_modal_upload_saves_profile_picture_bytes_to_database(self):
        image = SimpleUploadedFile(
            "avatar.png",
            b"\x89PNG\r\n\x1a\nprofile-image-bytes",
            content_type="image/png",
        )

        response = self.client.post(
            reverse("profile_edit_modal"),
            {
                "first_name": "Profile",
                "last_name": "Owner",
                "email": "owner@example.com",
                "phone": "09171234567",
                "address": "Depot",
                "profile_picture": image,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(bytes(self.user.profile.profile_picture_data), b"\x89PNG\r\n\x1a\nprofile-image-bytes")
        self.assertEqual(self.user.profile.profile_picture_mime_type, "image/png")
        self.assertEqual(self.user.profile.profile_picture_filename, "avatar.png")
        self.assertEqual(self.user.profile.profile_picture.name, "")

    def test_profile_picture_view_streams_database_image(self):
        self.user.profile.profile_picture_data = b"database-image"
        self.user.profile.profile_picture_mime_type = "image/png"
        self.user.profile.profile_picture_filename = "avatar.png"
        self.user.profile.save()

        response = self.client.get(reverse("profile_picture", args=[self.user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response.content, b"database-image")

    def test_profile_page_uses_database_profile_picture_url(self):
        self.user.profile.profile_picture_data = b"database-image"
        self.user.profile.profile_picture_mime_type = "image/png"
        self.user.profile.profile_picture_filename = "avatar.png"
        self.user.profile.save()

        response = self.client.get(reverse("profile"))

        self.assertContains(response, reverse("profile_picture", args=[self.user.pk]))

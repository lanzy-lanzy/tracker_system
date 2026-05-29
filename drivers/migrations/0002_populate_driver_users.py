from django.db import migrations


def create_user_accounts_for_existing_drivers(apps, schema_editor):
    Driver = apps.get_model("drivers", "Driver")
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("accounts", "Profile")
    for driver in Driver.objects.filter(user__isnull=True):
        base = driver.full_name.lower().replace(" ", ".").replace("ñ", "n").replace("ü", "u")
        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        user = User.objects.create_user(
            username=username,
            password="changeme123",
            email=f"{username}@tracker.local",
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = "driver"
        profile.save()
        driver.user = user
        driver.save()


class Migration(migrations.Migration):

    dependencies = [
        ("drivers", "0001_initial"),
        ("accounts", "0002_alter_profile_profile_picture"),
    ]

    operations = [
        migrations.RunPython(
            create_user_accounts_for_existing_drivers,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

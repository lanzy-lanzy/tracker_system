import os
from django.apps import AppConfig
from django.contrib.auth import get_user_model

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        User = get_user_model()
        password = os.environ.get("SEED_ADMIN_PASSWORD")
        if password and not User.objects.filter(is_superuser=True).exists():
            try:
                User.objects.create_superuser(
                    username="admin",
                    email="admin@example.com",
                    password=password,
                )
            except Exception:
                pass

"""
WSGI config for tracker_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker_system.settings")

application = get_wsgi_application()

if os.environ.get("VERCEL") and not os.environ.get("WSGI_INIT_DONE"):
    os.environ["WSGI_INIT_DONE"] = "1"
    from django.core.management import call_command
    try:
        call_command("migrate", "--noinput")
        call_command("seedadmin")
    except Exception as e:
        print(f"WSGI startup: {e}", file=sys.stderr)

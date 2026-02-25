"""Set admin user password from ADMIN_PASSWORD env var on every startup.

Ensures the Django admin password always matches the Railway env var.
Safe to run multiple times — only updates if user exists.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set admin user password from ADMIN_PASSWORD environment variable"

    def handle(self, *args, **options):
        password = os.environ.get("ADMIN_PASSWORD", "")
        username = os.environ.get("ADMIN_USERNAME", "admin")

        if not password:
            self.stdout.write("ADMIN_PASSWORD not set — skipping admin password sync")
            return

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(f"Admin password updated for user '{username}'")
        except User.DoesNotExist:
            User.objects.create_superuser(
                username=username,
                email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
                password=password,
            )
            self.stdout.write(f"Superuser '{username}' created")

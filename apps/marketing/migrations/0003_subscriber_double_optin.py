"""
Migration: add double opt-in fields to Subscriber.

Two-step approach for confirmation_token (unique UUIDField):
  Step 1 — add as nullable, fill with uuid4 for existing rows
  Step 2 — set NOT NULL + UNIQUE
"""

import uuid

from django.db import migrations, models


def fill_confirmation_tokens(apps, schema_editor):
    Subscriber = apps.get_model("marketing", "Subscriber")
    for sub in Subscriber.objects.filter(confirmation_token__isnull=True):
        sub.confirmation_token = uuid.uuid4()
        sub.save(update_fields=["confirmation_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0002_language_field"),
    ]

    operations = [
        # is_confirmed — simple boolean, no uniqueness issue
        migrations.AddField(
            model_name="subscriber",
            name="is_confirmed",
            field=models.BooleanField(
                default=False,
                help_text="True after subscriber clicks confirmation link (double opt-in).",
            ),
        ),
        # confirmed_at — nullable datetime
        migrations.AddField(
            model_name="subscriber",
            name="confirmed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        # confirmation_token step 1: add nullable (no unique constraint yet)
        migrations.AddField(
            model_name="subscriber",
            name="confirmation_token",
            field=models.UUIDField(null=True, blank=True),
        ),
        # Fill existing rows with unique UUIDs
        migrations.RunPython(fill_confirmation_tokens, migrations.RunPython.noop),
        # confirmation_token step 2: set NOT NULL + UNIQUE
        migrations.AlterField(
            model_name="subscriber",
            name="confirmation_token",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

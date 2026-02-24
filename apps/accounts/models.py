from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for Smile Memory admin users."""

    phone = models.CharField(max_length=50, blank=True)
    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", "English"), ("th", "Thai")],
        default="th",
    )

    class Meta:
        db_table = "users"

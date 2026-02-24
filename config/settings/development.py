"""Development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# SQLite for local development (no Docker needed)
# Switch to PostgreSQL when Docker is available
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Console email backend (prints emails to terminal)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar (uncomment when installed)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]
